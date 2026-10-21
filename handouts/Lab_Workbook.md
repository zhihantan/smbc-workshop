# Lab workbook · SMBC Data & AI Workshop

> **All workshop data is synthetic.** The labs use a made-up SMBC APAC corporate lending book: every borrower, group, limit and balance is fictional. No SMBC data, systems or customer information is used at any point.

## Contents

- [Before you start](#before-you-start)
- [1. The scenario and the data](#1-the-scenario-and-the-data)
- [2. Lab 1: Build the trusted exposure table](#2-lab-1-build-the-trusted-exposure-table)
- [3. Lab 2: Credit Committee in 30 seconds](#3-lab-2-credit-committee-in-30-seconds)
- [4. AI-assisted development with Genie Code](#4-ai-assisted-development-with-genie-code)
- [5. Resources](#5-resources)
- [Appendix A: Copy-paste kit](#appendix-a-copy-paste-kit)
- [Appendix B: Troubleshooting](#appendix-b-troubleshooting)

## Before you start

**1. Sign in.** Open `<workspace URL>` in Microsoft Edge or Google Chrome and sign in with your SMBC account. The workshop's **Labs** folder has one notebook per session, from *00 Start here* to *04 Kit and help*; clone one (**File → Clone**) to run its cells.

**2. Check in.** Open **SQL Editor**, choose the workshop's SQL warehouse (your facilitator will name it), paste this block and click **Run**. It checks you in and creates your schema for Lab 1. Change `DA` to `DE` if you're a data engineer.

```sql
-- Check in and create your Lab 1 schema. Change 'DA' to 'DE' if you're a data engineer.
BEGIN
  DECLARE my_schema STRING DEFAULT regexp_replace(lower(split_part(current_user(), '@', 1)), '[^a-z0-9_]', '_');
  INSERT INTO smbc_workshop.ops.checkin SELECT current_user(), 'DA', current_timestamp();
  CREATE SCHEMA IF NOT EXISTS IDENTIFIER('smbc_workshop.' || my_schema);
  SELECT 'smbc_workshop.' || my_schema AS your_schema;
END
```

**3. Your schema.** The check-in shows its name. Your Lab 1 tables go in `smbc_workshop.<your schema>`: the part of your email address before the @, in lower case, with any other characters replaced by `_`. For example, `jane.tan@…` becomes `jane_tan`.

**4. Getting help.** Turn your card to red, or raise a hand, and a helper will come to you.

**5. Short on time?** The reference tables in `smbc_workshop.gold` hold the Lab 1 result, so you can carry on with Lab 2 and the Genie Code segment whatever happens in Lab 1.

---

## 1. The scenario and the data

The labs use a synthetic **SMBC APAC** corporate lending book with about USD 27bn of drawn exposure across 12 booking branches in Asia Pacific. Every borrower, group and figure is made up. Borrowers belong to counterparty groups, such as a conglomerate and its subsidiaries in several countries, and each group has an approved credit limit set by the risk team. As at SMBC, the fiscal year runs from April to March.

### Source files (`/Volumes/smbc_workshop/raw/landing/`)

| Folder | Format | Rows | What it is |
|---|---|---|---|
| `counterparties/` | CSV | 2,370 | Customer master: borrower, parent group, country, sector, internal rating. Names in English, plus local script where available (日本語, 中文, ไทย, 한국어, Tiếng Việt). |
| `facilities/` | JSON Lines | 6,047 | Credit facilities: product, currency, committed amount, start and maturity dates, booking branch, collateral. |
| `monthly_balances/` | CSV | 74,799 | Month-end drawn balance and days past due per facility, April 2025 to September 2026. |
| `fx_rates/` | CSV | 252 | Month-end FX rates to USD and JPY for 14 currencies. |
| `group_limits/` | Excel | 420 | The risk team's spreadsheet of approved limits per counterparty group. |
| `sector_emission_factors/` | CSV | 16 | Illustrative emission factors by sector, for an optional ESG stretch question. |

### Notes from the source-system owners

These are the kind of handover notes a data team gets, and Lab 1 deals with each of them:

- *"The customer master extract sometimes contains the same row twice."*
- *"Currency codes on facilities are typed by hand, so expect `usd`, `US$`, `S$` and `RMB`."*
- *"The trade-finance system writes dates as DD/MM/YYYY; the core loan system uses YYYY-MM-DD."*
- *"Bangkok re-sent its September trade-finance extract. Keep the latest copy of each row (see `extract_ts`)."*
- *"FX rates are captured on the last business day of each month, not always the calendar month end."*
- *"A few facilities were booked before the customer record was created in the master."*

### Reference tables (`bronze`, `silver` and `gold`)

The reference solution to Lab 1, in the medallion layout. Anyone can use the gold tables to carry on with Lab 2 and the Genie Code segment.

| Table | Grain | Use |
|---|---|---|
| `gold.group_exposure` | Counterparty group × month | Exposure, limit and `utilisation_pct` per group |
| `gold.facility_exposure` | Facility × month | Exposure with borrower, country, sector, branch, product, currency and days past due |
| `silver.*`, including `silver.quarantine_facilities` | Cleaned inputs, and the rows held back with a reason | For comparing with your own Lab 1 output |
| `bronze.*` | The extracts as delivered, as tables | Where the cleaning starts |

---

## 2. Lab 1: Build the trusted exposure table

**Goal:** turn the raw extracts into `gold_group_exposure`, a table the Credit Committee can trust, with bad rows quarantined, duplicates removed, and every step visible as code and as lineage.
**Time:** 40 minutes, made up of a 25-minute core path and 15 minutes of stretch exercises.
**Tools:** Lakeflow Designer, Genie Code, Lakeflow Jobs, Unity Catalog.

> **Short on time?** Nothing in Lab 2 depends on finishing Lab 1: the gold reference tables have the same result. Work in pairs, ideally one analyst and one engineer, with the engineer driving.

### Core path

**0. Find your schema (1 min).** Your check-in created it and showed its name: the part of your email address before the @, for example `jane_tan`. Find it in **Catalog Explorer** → `smbc_workshop`. Not there? Run the check-in block (A.1) again.

**1. Start a visual data prep (1 min).** Click **+ New → Visual data prep**. Rename the tab to `Monday exposure report`. In the compute picker at the top right, choose **Serverless**.

**2. Bring in the sources (4 min).** Add a **Source** operator → **Browse existing** → `smbc_workshop` → `raw` → `landing` → select the **`counterparties`** folder. Designer reads every file in a folder into one table. Do the same for `facilities`, `monthly_balances` and `fx_rates`. For the limits, drag `group_limits.xlsx` onto the canvas (download it from the landing volume first), or browse to the `group_limits` folder. Click each Source and look at the preview: can you see two date formats in `monthly_balances`?

**3. De-duplicate the customer master (1 min).** After `counterparties`, add **Unique** with **Unique by: All columns**. Row count: 2,370 → 2,325.

**4. Clean the facilities with Genie Code (4 min).** Select the `facilities` Source and type this into the Genie Code prompt on the canvas:
> *Add a Prepare step that trims and upper-cases `currency`, maps `US$` to `USD`, `S$` to `SGD` and `RMB` to `CNY`, and parses `start_date` and `maturity_date` whether they're written YYYY-MM-DD or DD/MM/YYYY.*

Open the operator it adds and read its actions. Then open **Table of contents** in the left panel, select the operator, and expand **Generated code**. Every visual step is real code you can review and version.

**5. Quarantine bad rows with Guardrails (4 min).** Add **Guardrails** after the Prepare step, with these checks:
- **Value range:** `committed_amount` greater than 0
- **Expression:** `maturity_date >= start_date`
- **Not null:** `start_date`, `maturity_date`

Set **When a check fails** to **Warn and continue with passed rows**. Connect **Failed** to an **Output** that writes the table `quarantine_facilities` to your schema. You should see 21 failed rows. Each one has a reason, and that's your data-quality evidence.

**6. Fix the balances and FX dates (3 min).**
- On `monthly_balances`, add a **Prepare** step with two **Formula** actions. Describe them in plain English: *"`as_of_date` as a date, whether written YYYY-MM-DD or DD/MM/YYYY"* and *"`month` = first day of the month of `as_of_date`"*.
- Then add **Unique** → **Selected columns** `facility_id`, `as_of_date` → **Order by** `extract_ts` descending. Rows: 74,799 → 74,757.
- On `fx_rates`, add a Formula: *"`rate_month` = first day of the month of `rate_date`"*.

**7. Join and convert with Genie Code (4 min).** Prompt:
> *Join the de-duplicated balances to the facilities that passed Guardrails and to the de-duplicated counterparties. Then join fx_rates on currency = currency_code and month = rate_month, and add exposure_usd = drawn_amount × usd_rate and exposure_jpy = drawn_amount × jpy_rate.*

Check the Join outputs:
- **Left unmatched** on the facilities-to-counterparties join shows the facilities whose customer isn't in the master yet (send them to a second quarantine Output if you like).
- **Left unmatched** on the FX join should be empty. If it shows `US$`, `S$` or `RMB`, step 4 missed a mapping.

**8. Roll up to the group and compare with limits (3 min).**
- Add **Aggregate**: group by `as_of_date`, `parent_group_id`; **SUM** of `exposure_usd` and `exposure_jpy`.
- Add **Join** with the limits on `parent_group_id` = `group_id`.
- Add a **Prepare** Formula: *"`utilisation_pct` = 100 × exposure_usd ÷ group_limit_usd"*.

**9. Write and schedule (2 min).** Add an **Output**: **Table** `gold_group_exposure` in your schema, **Write mode: Overwrite**, then **Run**. Click **Schedule** to run it daily at 07:00 Singapore time.

✅ **Checkpoint:** your row on the progress board turns green. To check your result against the reference, run both queries (notebook *01* in the Labs folder works out your schema for you); the two totals should be identical:

```sql
SELECT round(sum(exposure_usd) / 1e6, 1) AS mine_usd_m
FROM smbc_workshop.<your_schema>.gold_group_exposure WHERE as_of_date = '2026-09-30';

SELECT round(sum(exposure_usd) / 1e6, 1) AS reference_usd_m
FROM smbc_workshop.gold.group_exposure WHERE as_of_date = '2026-09-30';
```

### Stretch (pick any)

- **Version and diff:** open the version history (right pane) to see a visual diff of your changes. Then commit the visual data prep to a Git folder.
- **Engineer's path:** rebuild the facility cleaning in the **Lakeflow Pipelines Editor** with Genie Code in agent mode, using expectations (`CONSTRAINT valid_commitment EXPECT (committed_amount > 0) ON VIOLATION DROP ROW`). Compare the data-quality metrics with your Guardrails output.
- **Alerting:** add a task that checks *"any group above 90% utilisation?"* and sends a notification when it's true.
- **Document it:** in Catalog Explorer, accept or edit the AI-suggested description for `gold_group_exposure`. Better metadata means better Genie answers in Lab 2.

---

## 3. Lab 2: Credit Committee in 30 seconds

**Goal:** give the Credit Committee a dashboard for the questions they always ask, and a Genie Agent for the ones they haven't asked yet. Teach the agent the bank's rules, and test that it's right.
**Time:** 40 minutes, made up of a 25-minute core path and 15 minutes of stretch exercises.
**Tools:** AI/BI dashboards, Genie Agents, Genie One, Unity Catalog.

> Use the **gold** reference tables (`smbc_workshop.gold.group_exposure` and `smbc_workshop.gold.facility_exposure`) so everyone's answers match. If you finished Lab 1, your own tables give the same numbers.

### Core path

**1. Build the dashboard (10 min).**
- Click **+ New → Dashboard**. On the **Data** tab, add both gold tables.
- On the canvas, ask the AI assistant: *"Bar chart of the top 10 counterparty groups by exposure_usd at the latest as_of_date, coloured by utilisation_pct."*
- Add these widgets:
  - a **counter** for total exposure at the latest month end;
  - a **counter** for groups above 80% utilisation;
  - a **line chart** of total exposure by month;
  - a **bar chart** of exposure by country.
- Add filters for `as_of_date` and `booking_branch`, then **Publish**.
- Open `<workspace URL>/one`: this is Genie One, what a business user sees.

**2. Create a Genie Agent (5 min).**
- Click **Genie Agents → New**, select the two gold tables (`group_exposure` and `facility_exposure`), and click **Create**.
- Genie Code reads the tables and suggests descriptions and example queries. Review them, and accept the ones that are right.
- In **Configure → Settings**, set the title to `Credit Risk – <your name>` and the default warehouse to the SQL warehouse you checked in with.
- Add the starter instructions (A.3), the two example SQL queries (A.5) and the common questions (A.6).

**3. Ask, and check the SQL (5 min).** Try *"Which counterparty groups are closest to their limits?"* and *"Show exposure in yen by booking branch at the latest month end."* Open the generated SQL for each answer. Trust, but verify.

**4. The fiscal-year test (4 min).** Before adding the fiscal-year instruction, ask:
- *"What was Orchid Group's utilisation at the end of Q1 FY2026?"*
- *"Show Orchid Group's utilisation for each month of FY2025."*

Open the SQL and check which dates Genie used. Then add the fiscal-year instruction (A.4) and ask both again.

✅ **Checkpoint:** ask *"Which groups were above 90% of their limit at the end of FY2026 H1?"*, then submit the name of the group:

```sql
INSERT INTO smbc_workshop.ops.lab_answers SELECT current_user(), 'lab2', '<group name>', current_timestamp();
```

### Stretch (pick any)

- **Stump the Genie:** find a question it gets wrong, fix it with an instruction or an example query, and ask again. Share your best stump-and-fix with a facilitator: there's a prize.
  - *Starter example (tested):* ask *"Which booking branch has the highest share of trade finance in arrears?"* and open the SQL. In one test run Genie counted facilities; in another it weighted by exposure and asked which one we meant. Add the instruction *"Shares of arrears are measured by exposure (exposure_usd), not by number of facilities"*, and the answer becomes consistent.
- **Benchmarks:** add the benchmark questions (A.7) with their expected SQL and run an evaluation. Benchmarks are how a team shows a Genie Agent is accurate before sharing it.
- **Agent mode:** ask *"Why has the most utilised group's limit usage risen since April 2026?"* and watch it plan, run several queries and write a report.
- **In Japanese:** 「2026年度上期末時点で、与信限度額の90%を超えている取引先グループはどこですか？」 Answers may sometimes come back in English.
- **Share it:** attach your Genie Agent to your dashboard, or schedule a Monday 08:00 PDF subscription of the dashboard.
- **Semantic layer:** use the agent's ⋮ menu → **Export to metric view** to turn the definitions you taught it into a governed metric view.

---

## 4. AI-assisted development with Genie Code

**15 minutes**, mostly a live demo; participants can follow along in notebook *03* in the Labs folder, which has the prompts (A.8) and the legacy procedure (A.9).

1. **Explore:** profile `gold.group_exposure` and ask what is unusual about the latest month compared with April.
2. **Generate:** split one group's exposure change since April into an **FX effect** and a **new-drawdowns effect**, by subsidiary, and chart it. This answers the "why" behind the Credit Committee's question.
3. **Explain and convert:** paste a legacy Synapse T-SQL procedure (A.9). Genie Code explains what it does, points out logic risks, and rewrites it as Databricks SQL against the workshop tables.
4. **Iterate safely:**
   - Show the action-approval setting: by default an AI classifier approves actions within your request and blocks actions beyond it, or you can approve each one yourself.
   - Ask for an explanation with *"don't run any code"*.
   - Show that Genie Code can only reach data your Unity Catalog permissions allow.
   - Roll back a change with revision history.

---

## 5. Resources

| Resource | Link |
|---|---|
| Free self-paced training and learning paths for data analysts and data engineers | https://www.databricks.com/learn/training |
| Certifications (Data Analyst Associate, Data Engineer Associate) | https://www.databricks.com/learn/certification |
| Databricks Free Edition, for practice outside work | https://www.databricks.com/learn/free-edition |
| Free virtual workshops (4 Nov *Hands-on with Genie*, 12 Nov *AI-Powered Data Engineering with Lakeflow*, 18 Nov *Build, Orchestrate and Improve Agents*; Americas time slots, recordings available) | https://www.databricks.com/learn/training/workshop |
| Lakeflow Designer documentation | https://learn.microsoft.com/azure/databricks/designer/what-is-lakeflow-designer |
| Genie Agents documentation | https://learn.microsoft.com/azure/databricks/genie-agents/ |
| Genie One documentation | https://learn.microsoft.com/azure/databricks/genie-one/ |
| Genie Code documentation | https://learn.microsoft.com/azure/databricks/genie-code/ |

---

## Appendix A: Copy-paste kit

### A.1 Check-in and checkpoint queries

```sql
-- Check in and create your Lab 1 schema. Change 'DA' to 'DE' if you're a data engineer.
BEGIN
  DECLARE my_schema STRING DEFAULT regexp_replace(lower(split_part(current_user(), '@', 1)), '[^a-z0-9_]', '_');
  INSERT INTO smbc_workshop.ops.checkin SELECT current_user(), 'DA', current_timestamp();
  CREATE SCHEMA IF NOT EXISTS IDENTIFIER('smbc_workshop.' || my_schema);
  SELECT 'smbc_workshop.' || my_schema AS your_schema;
END

-- Lab 2 checkpoint
INSERT INTO smbc_workshop.ops.lab_answers SELECT current_user(), 'lab2', '<group name>', current_timestamp();
```

### A.2 Genie Code prompts for Lab 1 (Designer)

```text
Add a Prepare step that trims and upper-cases currency, maps US$ to USD, S$ to SGD and RMB to CNY, and parses
start_date and maturity_date whether they're written YYYY-MM-DD or DD/MM/YYYY.
```

```text
Join the de-duplicated balances to the facilities that passed Guardrails and to the de-duplicated counterparties.
Then join fx_rates on currency = currency_code and month = rate_month, and add exposure_usd = drawn_amount × usd_rate
and exposure_jpy = drawn_amount × jpy_rate.
```

### A.3 Genie Agent starter instructions

```text
This agent answers questions about SMBC APAC's corporate lending exposure. All data is synthetic.

- Exposure means drawn balance. Use exposure_usd unless the user asks for yen; then use exposure_jpy.
- Utilisation means a counterparty group's exposure divided by its approved group limit (utilisation_pct in
  group_exposure). Above 90% is "near its limit"; above 100% is "in breach".
- Balances are month-end snapshots. For "current" or "latest", use the most recent as_of_date. Never add balances
  across months; compare month ends instead.
- A counterparty group's exposure includes all of its subsidiaries in every country (parent_group_id).
- Booking branch codes: SIN Singapore, HKG Hong Kong, BKK Bangkok, SGN Ho Chi Minh City, JKT Jakarta, BOM Mumbai,
  SYD Sydney, SEL Seoul, SHA Shanghai, KUL Kuala Lumpur, MNL Manila, TPE Taipei.
- Arrears means days_past_due greater than 30.
- Show amounts in USD millions with one decimal place unless asked otherwise.
```

### A.4 The fiscal-year instruction (add in Lab 2, step 4)

```text
The fiscal year runs from 1 April to 31 March and is named after the calendar year it starts in:
FY2026 = 1 April 2026 to 31 March 2027. H1 = April to September; H2 = October to March.
Q1 = April–June, Q2 = July–September, Q3 = October–December, Q4 = January–March.
"End of FY2026 H1" means as_of_date = 2026-09-30. "FY2026 to date" means as_of_date from 2026-04-30 onwards.
```

### A.5 Example SQL queries

**"Top 10 counterparty groups by exposure at the latest month end"**
```sql
SELECT group_name, round(exposure_usd / 1e6, 1) AS exposure_usd_m, utilisation_pct
FROM smbc_workshop.gold.group_exposure
WHERE as_of_date = (SELECT max(as_of_date) FROM smbc_workshop.gold.group_exposure)
ORDER BY exposure_usd DESC
LIMIT 10;
```

**"Exposure by country and sector at a given month end"** (parameterised)
```sql
SELECT country_code, sector, round(sum(exposure_usd) / 1e6, 1) AS exposure_usd_m
FROM smbc_workshop.gold.facility_exposure
WHERE as_of_date = :as_of_date
GROUP BY country_code, sector
ORDER BY exposure_usd_m DESC;
```

### A.6 Common questions

```text
Which counterparty groups are closest to their limits?
How has total exposure changed month by month since April 2025?
What is our exposure to Vietnam by sector at the latest month end?
Show exposure in yen by booking branch at the latest month end.
Which booking branch has the highest share of trade finance in arrears?
```

### A.7 Benchmark questions (stretch)

| Question | Expected SQL |
|---|---|
| Total exposure in USD at 30 Sep 2026 | `SELECT sum(exposure_usd) FROM smbc_workshop.gold.facility_exposure WHERE as_of_date = '2026-09-30'` |
| Which groups were above 90% of their limit at the end of FY2026 H1? | `SELECT group_name, utilisation_pct FROM smbc_workshop.gold.group_exposure WHERE as_of_date = '2026-09-30' AND utilisation_pct > 90` |
| Top 5 groups by exposure at the end of June 2026 | `SELECT group_name, exposure_usd FROM smbc_workshop.gold.group_exposure WHERE as_of_date = '2026-06-30' ORDER BY exposure_usd DESC LIMIT 5` |
| Utilisation by month in FY2026 for the most utilised group | `SELECT as_of_date, utilisation_pct FROM smbc_workshop.gold.group_exposure WHERE parent_group_id = (SELECT parent_group_id FROM smbc_workshop.gold.group_exposure WHERE as_of_date = '2026-09-30' ORDER BY utilisation_pct DESC LIMIT 1) AND as_of_date >= '2026-04-30' ORDER BY as_of_date` |
| Share of SGN trade-finance exposure in arrears at 30 Sep 2026 | `SELECT 100 * sum(CASE WHEN days_past_due > 30 THEN exposure_usd ELSE 0 END) / sum(exposure_usd) FROM smbc_workshop.gold.facility_exposure WHERE as_of_date = '2026-09-30' AND booking_branch = 'SGN' AND source_system = 'TRADE_FIN'` |

### A.8 Genie Code prompts (AI-assisted development segment)

```text
Profile smbc_workshop.gold.group_exposure and tell me what is unusual about the latest month
compared with April 2026.
```

```text
For the group with the highest utilisation at 30 Sep 2026, split the change in USD exposure between 30 Apr 2026
and 30 Sep 2026 into an FX effect and a new-drawdowns (volume) effect, by subsidiary, using
smbc_workshop.gold.facility_exposure. Use: volume = (Sep balance − Apr balance) × Apr rate;
FX = Sep balance × (Sep rate − Apr rate). Chart it.
```

```text
Explain what this procedure does and point out any risks in its logic. Then rewrite it as Databricks SQL against
the smbc_workshop.gold tables. Just explain first, don't run any code.
<paste A.9>
```

### A.9 Legacy Synapse procedure (synthetic example)

```sql
-- Legacy month-end group exposure report (synthetic example for the workshop)
CREATE PROCEDURE rpt.usp_GroupExposure_Monthly @AsOfDate DATE
AS
BEGIN
    SET NOCOUNT ON;

    IF OBJECT_ID('tempdb..#bal') IS NOT NULL DROP TABLE #bal;

    SELECT b.facility_id,
           b.drawn_amount,
           ISNULL(f.currency, 'USD') AS ccy,
           cp.parent_group_id
    INTO #bal
    FROM stg.monthly_balances b
    INNER JOIN stg.facilities f ON f.facility_id = b.facility_id
    INNER JOIN stg.counterparties cp ON cp.counterparty_id = f.counterparty_id
    WHERE b.as_of_date = @AsOfDate
      AND f.committed_amount > 0;

    SELECT TOP 20
           g.group_name,
           SUM(b.drawn_amount * fx.usd_rate) AS exposure_usd,
           CAST(100.0 * SUM(b.drawn_amount * fx.usd_rate) / NULLIF(g.group_limit_usd, 0) AS DECIMAL(9, 2))
               AS utilisation_pct,
           CASE WHEN SUM(b.drawn_amount * fx.usd_rate) > 0.90 * g.group_limit_usd THEN 'RED'
                WHEN SUM(b.drawn_amount * fx.usd_rate) > 0.75 * g.group_limit_usd THEN 'AMBER'
                ELSE 'GREEN' END AS rag_status
    FROM #bal b
    CROSS APPLY (SELECT TOP 1 r.usd_rate
                 FROM ref.fx_rates r
                 WHERE r.currency_code = b.ccy AND r.rate_date <= @AsOfDate
                 ORDER BY r.rate_date DESC) fx
    INNER JOIN ref.group_limits g ON g.group_id = b.parent_group_id
    GROUP BY g.group_name, g.group_limit_usd
    ORDER BY exposure_usd DESC;
END
```

---

## Appendix B: Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| **Genie Agents** is in the sidebar but agents won't open | Partner-powered AI features are off | Ask a facilitator |
| Genie Code prompts in Designer or agent mode are unavailable | Partner-powered AI features off, or cross-Geo processing enforced | Ask a facilitator |
| The check-in fails with a permission error, or you can't see the `landing` volume | No access to `smbc_workshop` yet | Ask a facilitator |
| Output fails with a permission error | Writing outside your own schema | Set **Output location** to `smbc_workshop.<your_schema>` |
| Some months disappear after the FX join | Joining on the exact date: FX is dated on the last business day | Join on currency and month (Lab 1, step 6) |
| Your total is higher than the checkpoint | Duplicates not removed (customer master or the re-sent Bangkok extract) | Lab 1, steps 3 and 6 |
| Your total is much lower than the checkpoint | Only one date format parsed, or currency codes not mapped | Lab 1, steps 4 and 6; check the join's **Left unmatched** output |
| Dragging the `.xlsx` onto the canvas fails | Excel file support not enabled, or downloads blocked | Use **Source → Browse existing →** `group_limits` folder instead |
| Genie picks the wrong dates for "Q1 FY2026", "FY2025" or "FY2026 H1" | It assumed a calendar year (it does this inconsistently) | Add the fiscal-year instruction (A.4) |
| Genie's arrears "share" is much higher than the dashboard's | It counted facilities instead of weighting by exposure | Add an instruction that shares are by exposure (see Stump the Genie) |
| A question in Japanese gets an English answer | Possible: the agent framework wraps prompts in English. In testing, the Japanese question in Lab 2 was answered correctly, in Japanese. | Add Japanese metadata or instructions if needed |
| A dashboard subscription email doesn't arrive | Mail gateway filtering | Ask a facilitator |
