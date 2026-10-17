# Databricks notebook source
# MAGIC %md
# MAGIC # Lab workbook · SMBC Data & AI Workshop · Thursday 22 October 2026
# MAGIC
# MAGIC > **All workshop data is synthetic.** The labs use a made-up SMBC APAC corporate lending book: every borrower, group, limit and balance is fictional. No SMBC data, systems or customer information is used at any point.
# MAGIC
# MAGIC This is a read-only copy. To run the SQL cells, use **File → Clone** to copy it to your own folder, or paste the SQL into the SQL editor.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Before you start
# MAGIC
# MAGIC **1. Sign in.** Open `<workspace URL>` in Microsoft Edge or Google Chrome and sign in with your SMBC account.
# MAGIC
# MAGIC **2. Check in.** Open **SQL Editor**, choose the **SMBC Workshop** warehouse, paste this line and click **Run**. Change `DA` to `DE` if you're a data engineer.
# MAGIC
# MAGIC ```sql
# MAGIC INSERT INTO smbc_workshop.ops.checkin SELECT current_user(), 'DA', current_timestamp();
# MAGIC ```
# MAGIC
# MAGIC **3. Find your schema.** Your Lab 1 tables go in `smbc_workshop.<your schema>`: the part of your email address before the @, in lower case, with any other characters replaced by `_`. For example, `jane.tan@…` becomes `jane_tan`.
# MAGIC
# MAGIC **4. Getting help.** Turn your card to red, or raise a hand, and a helper will come to you.
# MAGIC
# MAGIC **5. Short on time?** The checkpoint tables in `smbc_workshop.checkpoint` hold the reference result, so you can carry on with Lab 2 and the Genie Code segment whatever happens in Lab 1.

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Check in. Change 'DA' to 'DE' if you're a data engineer.
# MAGIC INSERT INTO smbc_workshop.ops.checkin SELECT current_user(), 'DA', current_timestamp();

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. The scenario and the data
# MAGIC
# MAGIC The labs use a synthetic **SMBC APAC** corporate lending book with about USD 27bn of drawn exposure across 12 booking branches in Asia Pacific. Every borrower, group and figure is made up. Borrowers belong to counterparty groups, such as a conglomerate and its subsidiaries in several countries, and each group has an approved credit limit set by the risk team. As at SMBC, the fiscal year runs from April to March.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Source files (`/Volumes/smbc_workshop/raw/landing/`)
# MAGIC
# MAGIC | Folder | Format | Rows | What it is |
# MAGIC |---|---|---|---|
# MAGIC | `counterparties/` | CSV | 2,370 | Customer master: borrower, parent group, country, sector, internal rating. Names in English, plus local script where available (日本語, 中文, ไทย, 한국어, Tiếng Việt). |
# MAGIC | `facilities/` | JSON Lines | 6,047 | Credit facilities: product, currency, committed amount, start and maturity dates, booking branch, collateral. |
# MAGIC | `monthly_balances/` | CSV | 74,799 | Month-end drawn balance and days past due per facility, April 2025 to September 2026. |
# MAGIC | `fx_rates/` | CSV | 252 | Month-end FX rates to USD and JPY for 14 currencies. |
# MAGIC | `group_limits/` | Excel | 420 | The risk team's spreadsheet of approved limits per counterparty group. |
# MAGIC | `sector_emission_factors/` | CSV | 16 | Illustrative emission factors by sector, for an optional ESG stretch question. |

# COMMAND ----------

# MAGIC %md
# MAGIC ### Notes from the source-system owners
# MAGIC
# MAGIC These are the kind of handover notes a data team gets, and Lab 1 deals with each of them:
# MAGIC
# MAGIC - *"The customer master extract sometimes contains the same row twice."*
# MAGIC - *"Currency codes on facilities are typed by hand, so expect `usd`, `US$`, `S$` and `RMB`."*
# MAGIC - *"The trade-finance system writes dates as DD/MM/YYYY; the core loan system uses YYYY-MM-DD."*
# MAGIC - *"Bangkok re-sent its September trade-finance extract. Keep the latest copy of each row (see `extract_ts`)."*
# MAGIC - *"FX rates are captured on the last business day of each month, not always the calendar month end."*
# MAGIC - *"A few facilities were booked before the customer record was created in the master."*

# COMMAND ----------

# MAGIC %md
# MAGIC ### Save-point tables (`smbc_workshop.checkpoint`)
# MAGIC
# MAGIC The reference solution to Lab 1. Anyone can use these to carry on with Lab 2 and the Genie Code segment.
# MAGIC
# MAGIC | Table | Grain | Use |
# MAGIC |---|---|---|
# MAGIC | `gold_group_exposure` | Counterparty group × month | Exposure, limit and `utilisation_pct` per group |
# MAGIC | `gold_facility_exposure` | Facility × month | Exposure with borrower, country, sector, branch, product, currency and days past due |
# MAGIC | `silver_*`, `quarantine_facilities` | Cleaned inputs, and the rows held back with a reason | For comparing with your own Lab 1 output |

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Lab 1: Build the trusted exposure table
# MAGIC
# MAGIC **Goal:** turn the raw extracts into `gold_group_exposure`, a table the Credit Committee can trust, with bad rows quarantined, duplicates removed, and every step visible as code and as lineage.
# MAGIC **Time:** 40 minutes, made up of a 25-minute core path and 15 minutes of stretch exercises.
# MAGIC **Tools:** Lakeflow Designer, Genie Code, Lakeflow Jobs, Unity Catalog.
# MAGIC
# MAGIC > **Short on time?** Nothing in Lab 2 depends on finishing Lab 1: the checkpoint tables have the same result. Work in pairs, ideally one analyst and one engineer, with the engineer driving.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Core path
# MAGIC
# MAGIC **0. Find your schema (1 min).** In **Catalog Explorer**, open `smbc_workshop`. Your schema is named after your email address, for example `jane_tan`. If you don't have one, run `CREATE SCHEMA smbc_workshop.<your_name>;` in the SQL editor.
# MAGIC
# MAGIC **1. Start a visual data prep (1 min).** Click **+ New → Visual data prep**. Rename the tab to `Monday exposure report`. In the compute picker at the top right, choose **Serverless**.
# MAGIC
# MAGIC **2. Bring in the sources (4 min).** Add a **Source** operator → **Browse existing** → `smbc_workshop` → `raw` → `landing` → select the **`counterparties`** folder. Designer reads every file in a folder into one table. Do the same for `facilities`, `monthly_balances` and `fx_rates`. For the limits, drag `group_limits.xlsx` onto the canvas (download it from the landing volume first), or browse to the `group_limits` folder. Click each Source and look at the preview: can you see two date formats in `monthly_balances`?
# MAGIC
# MAGIC **3. De-duplicate the customer master (1 min).** After `counterparties`, add **Unique** with **Unique by: All columns**. Row count: 2,370 → 2,325.
# MAGIC
# MAGIC **4. Clean the facilities with Genie Code (4 min).** Select the `facilities` Source and type this into the Genie Code prompt on the canvas:
# MAGIC > *Add a Prepare step that trims and upper-cases `currency`, maps `US$` to `USD`, `S$` to `SGD` and `RMB` to `CNY`, and parses `start_date` and `maturity_date` whether they're written YYYY-MM-DD or DD/MM/YYYY.*
# MAGIC
# MAGIC Open the operator it adds and read its actions. Then open **Table of contents** in the left panel, select the operator, and expand **Generated code**. Every visual step is real code you can review and version.
# MAGIC
# MAGIC **5. Quarantine bad rows with Guardrails (4 min).** Add **Guardrails** after the Prepare step, with these checks:
# MAGIC - **Value range:** `committed_amount` greater than 0
# MAGIC - **Expression:** `maturity_date >= start_date`
# MAGIC - **Not null:** `start_date`, `maturity_date`
# MAGIC
# MAGIC Set **When a check fails** to **Warn and continue with passed rows**. Connect **Failed** to an **Output** that writes the table `quarantine_facilities` to your schema. You should see 21 failed rows. Each one has a reason, and that's your data-quality evidence.
# MAGIC
# MAGIC **6. Fix the balances and FX dates (3 min).**
# MAGIC - On `monthly_balances`, add a **Prepare** step with two **Formula** actions. Describe them in plain English: *"`as_of_date` as a date, whether written YYYY-MM-DD or DD/MM/YYYY"* and *"`month` = first day of the month of `as_of_date`"*.
# MAGIC - Then add **Unique** → **Selected columns** `facility_id`, `as_of_date` → **Order by** `extract_ts` descending. Rows: 74,799 → 74,757.
# MAGIC - On `fx_rates`, add a Formula: *"`rate_month` = first day of the month of `rate_date`"*.
# MAGIC
# MAGIC **7. Join and convert with Genie Code (4 min).** Prompt:
# MAGIC > *Join the de-duplicated balances to the facilities that passed Guardrails and to the de-duplicated counterparties. Then join fx_rates on currency = currency_code and month = rate_month, and add exposure_usd = drawn_amount × usd_rate and exposure_jpy = drawn_amount × jpy_rate.*
# MAGIC
# MAGIC Check the Join outputs:
# MAGIC - **Left unmatched** on the facilities-to-counterparties join shows the facilities whose customer isn't in the master yet (send them to a second quarantine Output if you like).
# MAGIC - **Left unmatched** on the FX join should be empty. If it shows `US$`, `S$` or `RMB`, step 4 missed a mapping.
# MAGIC
# MAGIC **8. Roll up to the group and compare with limits (3 min).**
# MAGIC - Add **Aggregate**: group by `as_of_date`, `parent_group_id`; **SUM** of `exposure_usd` and `exposure_jpy`.
# MAGIC - Add **Join** with the limits on `parent_group_id` = `group_id`.
# MAGIC - Add a **Prepare** Formula: *"`utilisation_pct` = 100 × exposure_usd ÷ group_limit_usd"*.
# MAGIC
# MAGIC **9. Write and schedule (2 min).** Add an **Output**: **Table** `gold_group_exposure` in your schema, **Write mode: Overwrite**, then **Run**. Click **Schedule** to run it daily at 07:00 Singapore time.
# MAGIC
# MAGIC ✅ **Checkpoint:** your row on the progress board turns green. To check your result against the reference, run both queries; the two totals should be identical:
# MAGIC
# MAGIC ```sql
# MAGIC SELECT round(sum(exposure_usd) / 1e6, 1) AS mine_usd_m
# MAGIC FROM smbc_workshop.<your_schema>.gold_group_exposure WHERE as_of_date = '2026-09-30';
# MAGIC
# MAGIC SELECT round(sum(exposure_usd) / 1e6, 1) AS reference_usd_m
# MAGIC FROM smbc_workshop.checkpoint.gold_group_exposure WHERE as_of_date = '2026-09-30';
# MAGIC ```

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Compare your Lab 1 result with the reference. Your schema is worked out from your login.
# MAGIC BEGIN
# MAGIC   DECLARE my_schema STRING DEFAULT regexp_replace(lower(split_part(current_user(), '@', 1)), '[^a-z0-9_]', '_');
# MAGIC   SELECT my_schema,
# MAGIC          (SELECT round(sum(exposure_usd) / 1e6, 1) FROM IDENTIFIER('smbc_workshop.' || my_schema || '.gold_group_exposure')
# MAGIC           WHERE as_of_date = '2026-09-30') AS mine_usd_m,
# MAGIC          (SELECT round(sum(exposure_usd) / 1e6, 1) FROM smbc_workshop.checkpoint.gold_group_exposure
# MAGIC           WHERE as_of_date = '2026-09-30') AS reference_usd_m;
# MAGIC END

# COMMAND ----------

# MAGIC %md
# MAGIC ### Stretch (pick any)
# MAGIC
# MAGIC - **Version and diff:** open the version history (right pane) to see a visual diff of your changes. Then commit the visual data prep to a Git folder.
# MAGIC - **Engineer's path:** rebuild the facility cleaning in the **Lakeflow Pipelines Editor** with Genie Code in agent mode, using expectations (`CONSTRAINT valid_commitment EXPECT (committed_amount > 0) ON VIOLATION DROP ROW`). Compare the data-quality metrics with your Guardrails output.
# MAGIC - **Alerting:** add a task that checks *"any group above 90% utilisation?"* and sends a notification when it's true.
# MAGIC - **Document it:** in Catalog Explorer, accept or edit the AI-suggested description for `gold_group_exposure`. Better metadata means better Genie answers in Lab 2.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Lab 2: Credit Committee in 30 seconds
# MAGIC
# MAGIC **Goal:** give the Credit Committee a dashboard for the questions they always ask, and a Genie Agent for the ones they haven't asked yet. Teach the agent the bank's rules, and test that it's right.
# MAGIC **Time:** 40 minutes, made up of a 25-minute core path and 15 minutes of stretch exercises.
# MAGIC **Tools:** AI/BI dashboards, Genie Agents, Genie One, Unity Catalog.
# MAGIC
# MAGIC > Use the **checkpoint** tables (`smbc_workshop.checkpoint.gold_group_exposure` and `gold_facility_exposure`) so everyone's answers match. If you finished Lab 1, your own tables give the same numbers.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Core path
# MAGIC
# MAGIC **1. Build the dashboard (10 min).**
# MAGIC - Click **+ New → Dashboard**. On the **Data** tab, add both checkpoint gold tables.
# MAGIC - On the canvas, ask the AI assistant: *"Bar chart of the top 10 counterparty groups by exposure_usd at the latest as_of_date, coloured by utilisation_pct."*
# MAGIC - Add these widgets:
# MAGIC   - a **counter** for total exposure at the latest month end;
# MAGIC   - a **counter** for groups above 80% utilisation;
# MAGIC   - a **line chart** of total exposure by month;
# MAGIC   - a **bar chart** of exposure by country.
# MAGIC - Add filters for `as_of_date` and `booking_branch`, then **Publish**.
# MAGIC - Open `<workspace URL>/one`: this is Genie One, what a business user sees.
# MAGIC
# MAGIC **2. Create a Genie Agent (5 min).**
# MAGIC - Click **Genie Agents → New**, select the two checkpoint gold tables, and click **Create**.
# MAGIC - Genie Code reads the tables and suggests descriptions and example queries. Review them, and accept the ones that are right.
# MAGIC - In **Configure → Settings**, set the title to `Credit Risk – <your name>` and the default warehouse to **SMBC Workshop**.
# MAGIC - Add the starter instructions (A.3), the two example SQL queries (A.5) and the common questions (A.6).
# MAGIC
# MAGIC **3. Ask, and check the SQL (5 min).** Try *"Which counterparty groups are closest to their limits?"* and *"Show exposure in yen by booking branch at the latest month end."* Open the generated SQL for each answer. Trust, but verify.
# MAGIC
# MAGIC **4. The fiscal-year test (4 min).** Before adding the fiscal-year instruction, ask:
# MAGIC - *"What was Orchid Group's utilisation at the end of Q1 FY2026?"*
# MAGIC - *"Show Orchid Group's utilisation for each month of FY2025."*
# MAGIC
# MAGIC Open the SQL and check which dates Genie used. Then add the fiscal-year instruction (A.4) and ask both again.
# MAGIC
# MAGIC ✅ **Checkpoint:** ask *"Which groups were above 90% of their limit at the end of FY2026 H1?"*, then submit the name of the group:
# MAGIC
# MAGIC ```sql
# MAGIC INSERT INTO smbc_workshop.ops.lab_answers SELECT current_user(), 'lab2', '<group name>', current_timestamp();
# MAGIC ```

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Lab 2 checkpoint. Replace <group name> with the group you found, then run the cell.
# MAGIC INSERT INTO smbc_workshop.ops.lab_answers SELECT current_user(), 'lab2', '<group name>', current_timestamp();

# COMMAND ----------

# MAGIC %md
# MAGIC ### Stretch (pick any)
# MAGIC
# MAGIC - **Stump the Genie:** find a question it gets wrong, fix it with an instruction or an example query, and ask again. Share your best stump-and-fix with a facilitator: there's a prize.
# MAGIC   - *Starter example (tested):* ask *"Which booking branch has the highest share of trade finance in arrears?"* and open the SQL. In one test run Genie counted facilities; in another it weighted by exposure and asked which one we meant. Add the instruction *"Shares of arrears are measured by exposure (exposure_usd), not by number of facilities"*, and the answer becomes consistent.
# MAGIC - **Benchmarks:** add the benchmark questions (A.7) with their expected SQL and run an evaluation. Benchmarks are how a team shows a Genie Agent is accurate before sharing it.
# MAGIC - **Agent mode:** ask *"Why has the most utilised group's limit usage risen since April 2026?"* and watch it plan, run several queries and write a report.
# MAGIC - **In Japanese:** 「2026年度上期末時点で、与信限度額の90%を超えている取引先グループはどこですか？」 Answers may sometimes come back in English.
# MAGIC - **Share it:** attach your Genie Agent to your dashboard, or schedule a Monday 08:00 PDF subscription of the dashboard.
# MAGIC - **Semantic layer:** use the agent's ⋮ menu → **Export to metric view** to turn the definitions you taught it into a governed metric view.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. AI-assisted development with Genie Code
# MAGIC
# MAGIC **15 minutes**, mostly a live demo; participants can follow along in a notebook. The prompts are in A.8.
# MAGIC
# MAGIC 1. **Explore:** profile `gold_group_exposure` and ask what is unusual about the latest month compared with April.
# MAGIC 2. **Generate:** split one group's exposure change since April into an **FX effect** and a **new-drawdowns effect**, by subsidiary, and chart it. This answers the "why" behind the Credit Committee's question.
# MAGIC 3. **Explain and convert:** paste a legacy Synapse T-SQL procedure (A.9). Genie Code explains what it does, points out logic risks, and rewrites it as Databricks SQL against the workshop tables.
# MAGIC 4. **Iterate safely:**
# MAGIC    - Show the action-approval setting: by default an AI classifier approves actions within your request and blocks actions beyond it, or you can approve each one yourself.
# MAGIC    - Ask for an explanation with *"don't run any code"*.
# MAGIC    - Show that Genie Code can only reach data your Unity Catalog permissions allow.
# MAGIC    - Roll back a change with revision history.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Resources
# MAGIC
# MAGIC | Resource | Link |
# MAGIC |---|---|
# MAGIC | Free self-paced training and learning paths for data analysts and data engineers | https://www.databricks.com/learn/training |
# MAGIC | Certifications (Data Analyst Associate, Data Engineer Associate) | https://www.databricks.com/learn/certification |
# MAGIC | Databricks Free Edition, for practice outside work | https://www.databricks.com/learn/free-edition |
# MAGIC | Free virtual workshops (4 Nov *Hands-on with Genie*, 12 Nov *AI-Powered Data Engineering with Lakeflow*, 18 Nov *Build, Orchestrate and Improve Agents*; Americas time slots, recordings available) | https://www.databricks.com/learn/training/workshop |
# MAGIC | Lakeflow Designer documentation | https://learn.microsoft.com/azure/databricks/designer/what-is-lakeflow-designer |
# MAGIC | Genie Agents documentation | https://learn.microsoft.com/azure/databricks/genie-agents/ |
# MAGIC | Genie One documentation | https://learn.microsoft.com/azure/databricks/genie-one/ |
# MAGIC | Genie Code documentation | https://learn.microsoft.com/azure/databricks/genie-code/ |

# COMMAND ----------

# MAGIC %md
# MAGIC ## Appendix A: Copy-paste kit

# COMMAND ----------

# MAGIC %md
# MAGIC ### A.1 Check-in and checkpoint queries
# MAGIC
# MAGIC ```sql
# MAGIC -- Check-in (change 'DA' to 'DE' if you're a data engineer)
# MAGIC INSERT INTO smbc_workshop.ops.checkin SELECT current_user(), 'DA', current_timestamp();
# MAGIC
# MAGIC -- Lab 2 checkpoint
# MAGIC INSERT INTO smbc_workshop.ops.lab_answers SELECT current_user(), 'lab2', '<group name>', current_timestamp();
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ### A.2 Genie Code prompts for Lab 1 (Designer)
# MAGIC
# MAGIC ```text
# MAGIC Add a Prepare step that trims and upper-cases currency, maps US$ to USD, S$ to SGD and RMB to CNY, and parses
# MAGIC start_date and maturity_date whether they're written YYYY-MM-DD or DD/MM/YYYY.
# MAGIC ```
# MAGIC
# MAGIC ```text
# MAGIC Join the de-duplicated balances to the facilities that passed Guardrails and to the de-duplicated counterparties.
# MAGIC Then join fx_rates on currency = currency_code and month = rate_month, and add exposure_usd = drawn_amount × usd_rate
# MAGIC and exposure_jpy = drawn_amount × jpy_rate.
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ### A.3 Genie Agent starter instructions
# MAGIC
# MAGIC ```text
# MAGIC This agent answers questions about SMBC APAC's corporate lending exposure. All data is synthetic.
# MAGIC
# MAGIC - Exposure means drawn balance. Use exposure_usd unless the user asks for yen; then use exposure_jpy.
# MAGIC - Utilisation means a counterparty group's exposure divided by its approved group limit (utilisation_pct in
# MAGIC   gold_group_exposure). Above 90% is "near its limit"; above 100% is "in breach".
# MAGIC - Balances are month-end snapshots. For "current" or "latest", use the most recent as_of_date. Never add balances
# MAGIC   across months; compare month ends instead.
# MAGIC - A counterparty group's exposure includes all of its subsidiaries in every country (parent_group_id).
# MAGIC - Booking branch codes: SIN Singapore, HKG Hong Kong, BKK Bangkok, SGN Ho Chi Minh City, JKT Jakarta, BOM Mumbai,
# MAGIC   SYD Sydney, SEL Seoul, SHA Shanghai, KUL Kuala Lumpur, MNL Manila, TPE Taipei.
# MAGIC - Arrears means days_past_due greater than 30.
# MAGIC - Show amounts in USD millions with one decimal place unless asked otherwise.
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ### A.4 The fiscal-year instruction (add in Lab 2, step 4)
# MAGIC
# MAGIC ```text
# MAGIC The fiscal year runs from 1 April to 31 March and is named after the calendar year it starts in:
# MAGIC FY2026 = 1 April 2026 to 31 March 2027. H1 = April to September; H2 = October to March.
# MAGIC Q1 = April–June, Q2 = July–September, Q3 = October–December, Q4 = January–March.
# MAGIC "End of FY2026 H1" means as_of_date = 2026-09-30. "FY2026 to date" means as_of_date from 2026-04-30 onwards.
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ### A.5 Example SQL queries
# MAGIC
# MAGIC **"Top 10 counterparty groups by exposure at the latest month end"**
# MAGIC ```sql
# MAGIC SELECT group_name, round(exposure_usd / 1e6, 1) AS exposure_usd_m, utilisation_pct
# MAGIC FROM smbc_workshop.checkpoint.gold_group_exposure
# MAGIC WHERE as_of_date = (SELECT max(as_of_date) FROM smbc_workshop.checkpoint.gold_group_exposure)
# MAGIC ORDER BY exposure_usd DESC
# MAGIC LIMIT 10;
# MAGIC ```
# MAGIC
# MAGIC **"Exposure by country and sector at a given month end"** (parameterised)
# MAGIC ```sql
# MAGIC SELECT country_code, sector, round(sum(exposure_usd) / 1e6, 1) AS exposure_usd_m
# MAGIC FROM smbc_workshop.checkpoint.gold_facility_exposure
# MAGIC WHERE as_of_date = :as_of_date
# MAGIC GROUP BY country_code, sector
# MAGIC ORDER BY exposure_usd_m DESC;
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ### A.6 Common questions
# MAGIC
# MAGIC ```text
# MAGIC Which counterparty groups are closest to their limits?
# MAGIC How has total exposure changed month by month since April 2025?
# MAGIC What is our exposure to Vietnam by sector at the latest month end?
# MAGIC Show exposure in yen by booking branch at the latest month end.
# MAGIC Which booking branch has the highest share of trade finance in arrears?
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ### A.7 Benchmark questions (stretch)
# MAGIC
# MAGIC | Question | Expected SQL |
# MAGIC |---|---|
# MAGIC | Total exposure in USD at 30 Sep 2026 | `SELECT sum(exposure_usd) FROM smbc_workshop.checkpoint.gold_facility_exposure WHERE as_of_date = '2026-09-30'` |
# MAGIC | Which groups were above 90% of their limit at the end of FY2026 H1? | `SELECT group_name, utilisation_pct FROM smbc_workshop.checkpoint.gold_group_exposure WHERE as_of_date = '2026-09-30' AND utilisation_pct > 90` |
# MAGIC | Top 5 groups by exposure at the end of June 2026 | `SELECT group_name, exposure_usd FROM smbc_workshop.checkpoint.gold_group_exposure WHERE as_of_date = '2026-06-30' ORDER BY exposure_usd DESC LIMIT 5` |
# MAGIC | Utilisation by month in FY2026 for the most utilised group | `SELECT as_of_date, utilisation_pct FROM smbc_workshop.checkpoint.gold_group_exposure WHERE parent_group_id = (SELECT parent_group_id FROM smbc_workshop.checkpoint.gold_group_exposure WHERE as_of_date = '2026-09-30' ORDER BY utilisation_pct DESC LIMIT 1) AND as_of_date >= '2026-04-30' ORDER BY as_of_date` |
# MAGIC | Share of SGN trade-finance exposure in arrears at 30 Sep 2026 | `SELECT 100 * sum(CASE WHEN days_past_due > 30 THEN exposure_usd ELSE 0 END) / sum(exposure_usd) FROM smbc_workshop.checkpoint.gold_facility_exposure WHERE as_of_date = '2026-09-30' AND booking_branch = 'SGN' AND source_system = 'TRADE_FIN'` |

# COMMAND ----------

# MAGIC %md
# MAGIC ### A.8 Genie Code prompts (AI-assisted development segment)
# MAGIC
# MAGIC ```text
# MAGIC Profile smbc_workshop.checkpoint.gold_group_exposure and tell me what is unusual about the latest month
# MAGIC compared with April 2026.
# MAGIC ```
# MAGIC
# MAGIC ```text
# MAGIC For the group with the highest utilisation at 30 Sep 2026, split the change in USD exposure between 30 Apr 2026
# MAGIC and 30 Sep 2026 into an FX effect and a new-drawdowns (volume) effect, by subsidiary, using
# MAGIC smbc_workshop.checkpoint.gold_facility_exposure. Use: volume = (Sep balance − Apr balance) × Apr rate;
# MAGIC FX = Sep balance × (Sep rate − Apr rate). Chart it.
# MAGIC ```
# MAGIC
# MAGIC ```text
# MAGIC Explain what this procedure does and point out any risks in its logic. Then rewrite it as Databricks SQL against
# MAGIC the smbc_workshop.checkpoint tables. Just explain first, don't run any code.
# MAGIC <paste A.9>
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ### A.9 Legacy Synapse procedure (synthetic example)
# MAGIC
# MAGIC ```sql
# MAGIC -- Legacy month-end group exposure report (synthetic example for the workshop)
# MAGIC CREATE PROCEDURE rpt.usp_GroupExposure_Monthly @AsOfDate DATE
# MAGIC AS
# MAGIC BEGIN
# MAGIC     SET NOCOUNT ON;
# MAGIC
# MAGIC     IF OBJECT_ID('tempdb..#bal') IS NOT NULL DROP TABLE #bal;
# MAGIC
# MAGIC     SELECT b.facility_id,
# MAGIC            b.drawn_amount,
# MAGIC            ISNULL(f.currency, 'USD') AS ccy,
# MAGIC            cp.parent_group_id
# MAGIC     INTO #bal
# MAGIC     FROM stg.monthly_balances b
# MAGIC     INNER JOIN stg.facilities f ON f.facility_id = b.facility_id
# MAGIC     INNER JOIN stg.counterparties cp ON cp.counterparty_id = f.counterparty_id
# MAGIC     WHERE b.as_of_date = @AsOfDate
# MAGIC       AND f.committed_amount > 0;
# MAGIC
# MAGIC     SELECT TOP 20
# MAGIC            g.group_name,
# MAGIC            SUM(b.drawn_amount * fx.usd_rate) AS exposure_usd,
# MAGIC            CAST(100.0 * SUM(b.drawn_amount * fx.usd_rate) / NULLIF(g.group_limit_usd, 0) AS DECIMAL(9, 2))
# MAGIC                AS utilisation_pct,
# MAGIC            CASE WHEN SUM(b.drawn_amount * fx.usd_rate) > 0.90 * g.group_limit_usd THEN 'RED'
# MAGIC                 WHEN SUM(b.drawn_amount * fx.usd_rate) > 0.75 * g.group_limit_usd THEN 'AMBER'
# MAGIC                 ELSE 'GREEN' END AS rag_status
# MAGIC     FROM #bal b
# MAGIC     CROSS APPLY (SELECT TOP 1 r.usd_rate
# MAGIC                  FROM ref.fx_rates r
# MAGIC                  WHERE r.currency_code = b.ccy AND r.rate_date <= @AsOfDate
# MAGIC                  ORDER BY r.rate_date DESC) fx
# MAGIC     INNER JOIN ref.group_limits g ON g.group_id = b.parent_group_id
# MAGIC     GROUP BY g.group_name, g.group_limit_usd
# MAGIC     ORDER BY exposure_usd DESC;
# MAGIC END
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## Appendix B: Troubleshooting
# MAGIC
# MAGIC | Symptom | Likely cause | Fix |
# MAGIC |---|---|---|
# MAGIC | **Genie Agents** is in the sidebar but agents won't open | Partner-powered AI features are off | Ask a facilitator |
# MAGIC | Genie Code prompts in Designer or agent mode are unavailable | Partner-powered AI features off, or cross-Geo processing enforced | Ask a facilitator |
# MAGIC | Can't see the `landing` volume | Missing `READ VOLUME` grant | Ask a facilitator |
# MAGIC | Output fails with a permission error | Writing outside your own schema | Set **Output location** to `smbc_workshop.<your_schema>` |
# MAGIC | Some months disappear after the FX join | Joining on the exact date: FX is dated on the last business day | Join on currency and month (Lab 1, step 6) |
# MAGIC | Your total is higher than the checkpoint | Duplicates not removed (customer master or the re-sent Bangkok extract) | Lab 1, steps 3 and 6 |
# MAGIC | Your total is much lower than the checkpoint | Only one date format parsed, or currency codes not mapped | Lab 1, steps 4 and 6; check the join's **Left unmatched** output |
# MAGIC | Dragging the `.xlsx` onto the canvas fails | Excel file support not enabled, or downloads blocked | Use **Source → Browse existing →** `group_limits` folder instead |
# MAGIC | Genie picks the wrong dates for "Q1 FY2026", "FY2025" or "FY2026 H1" | It assumed a calendar year (it does this inconsistently) | Add the fiscal-year instruction (A.4) |
# MAGIC | Genie's arrears "share" is much higher than the dashboard's | It counted facilities instead of weighting by exposure | Add an instruction that shares are by exposure (see Stump the Genie) |
# MAGIC | A question in Japanese gets an English answer | Possible: the agent framework wraps prompts in English. In testing, the Japanese question in Lab 2 was answered correctly, in Japanese. | Add Japanese metadata or instructions if needed |
# MAGIC | A dashboard subscription email doesn't arrive | Mail gateway filtering | Ask a facilitator |
