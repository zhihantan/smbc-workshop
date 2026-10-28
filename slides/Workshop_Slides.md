---
# SMBC Data & AI Workshop: slides for the labs and hands-on segments.
# One slide per block between "---" lines. Speaker notes are in <!-- --> comments under each slide.
# The executive briefing uses Richard's and Peter's own slides, so it isn't here.
# Generate a deck with any Markdown-to-slides tool. With Marp, for example:
#   npx @marp-team/marp-cli slides/Workshop_Slides.md --pptx      (or --pdf, --html)
# Every fact and number comes from docs/SMBC_Workshop_Guide.md and facilitator/answer_key.md: keep them in step.
marp: true
theme: default
paginate: true
title: "SMBC Data & AI Workshop: labs and hands-on"
footer: "SMBC Data & AI Workshop · All data is synthetic"
---

<!-- _class: invert -->
<!-- _paginate: false -->

# From days to seconds, with guardrails

## SMBC Data & AI Workshop: labs and hands-on

Data analysts and data engineers

All workshop data is synthetic: the borrowers, groups and figures are made up.

<!--
[Before 0:00, on screen as people arrive]
- Doors open 30 minutes early, with a help desk for sign-in problems.
- The theme for the day: from days to seconds, with guardrails.
- Say it early and often: everything today uses a synthetic SMBC APAC lending book. The borrowers, groups and figures are made up, and no SMBC data, systems or customer information is used at any point.
-->

---

# Get set up

1. Open `<workspace URL>` in Microsoft Edge or Google Chrome, and sign in with your SMBC account.
2. Open **SQL Editor** and choose the **`<warehouse name>`** SQL warehouse.
3. Run the check-in block (workbook A.1). It checks you in and creates your Lab 1 schema. Change `DA` to `DE` if you're a data engineer.

```sql
BEGIN
  DECLARE my_schema STRING DEFAULT regexp_replace(lower(split_part(current_user(), '@', 1)), '[^a-z0-9_]', '_');
  INSERT INTO smbc_workshop.ops.checkin SELECT current_user(), 'DA', current_timestamp();
  CREATE SCHEMA IF NOT EXISTS IDENTIFIER('smbc_workshop.' || my_schema);
  SELECT 'smbc_workshop.' || my_schema AS your_schema;
END
```

**Need help?** Turn your card to red. **Poll on Slido:** what do you use most today?

<!--
[0:00 · 10 min]
- Most people should already be signed in from the pre-work email; this slot only confirms everyone is in.
- Fill in the warehouse name that 00_master_setup printed at the end.
- The check-in block writes one row to smbc_workshop.ops.checkin and creates the attendee's Lab 1 schema; the progress board shows both live. Put the board on the second screen.
- A permission error means the person doesn't have access to smbc_workshop yet (guide 3.6): a facilitator fixes it.
- Run the Slido poll while people sign in: Excel, SQL, Python, Power BI, ADF or Synapse, something else. It shows the room's mix of tools.
- Red card up: a helper comes over. Pair anyone who is still blocked with a neighbour so they don't miss Lab 1.
-->

---

# Today's agenda

| Time | Segment | Length |
|---|---|---|
| 0:00 | Welcome and environment check | 10 min |
| 0:10 | Executive briefing | 15 min |
| 0:25 | Data engineering: Lakeflow | 20 min |
| **0:45** | **Lab 1: Build the trusted exposure table** | **20 min** |
| 1:05 | Break | 15 min |
| 1:20 | Self-service analytics: AI/BI, Genie Agents, Genie One | 20 min |
| **1:40** | **Lab 2: Credit Committee in 30 seconds** | **40 min** |
| 2:20 | Break | 15 min |
| **2:35** | **AI-assisted development: Genie Code** (follow along) | **15 min** |
| 2:50 | Quiz | 15 min |
| 3:05 | Next steps and resources | 10 min |

<!--
[0:02 · 1 min]
- Two short intros, each followed by a hands-on lab (20 and 40 minutes), then a Genie Code segment you can follow along with, and a quiz on phones.
- Lab 1 starts from a staging table and takes 15 minutes. Lab 2 has a 25-minute core path and 15 minutes of stretch exercises, so nobody waits and nobody gets left behind.
- The reference tables in bronze, silver and gold mean nobody gets stuck: if Lab 1 runs long, Lab 2 still works.
- Times are relative to the start time.
-->

---

# The Monday exposure report

**8:00 on Monday at the APAC hub.** The Credit Committee wants the top counterparty-group exposures across all booking branches, in USD and JPY, by 10:00. Today that means four system extracts, a spreadsheet of limits, and days of reconciliation.

| Lab 1 | Lab 2 | Genie Code |
|---|---|---|
| **Automate it.** Lakeflow turns the raw extracts into a table the Credit Committee can trust | **Make it self-service.** An AI/BI dashboard and a Genie Agent for the Credit Committee | **Find out why.** Investigate what you found, and stay in control |

<!--
[0:04 · 2 min]
- One storyline runs through the day: the Monday exposure report.
- Lab 1 automates it with Lakeflow, Lab 2 makes it self-service with an AI/BI dashboard and a Genie Agent, and the Genie Code segment investigates what you found.
- By the end, everyone has built a pipeline, a dashboard and a Genie Agent themselves.
-->

---

# The data: a synthetic SMBC APAC lending book

- **12** booking branches · **420** counterparty groups · **2,325** borrowers · **6,047** credit facilities
- About **USD 27bn** of drawn exposure, at **18** month ends from April 2025 to September 2026
- Fiscal year: **April to March**. FY2026 = April 2026 to March 2027.

| Source folder in `smbc_workshop.raw.landing` | Format | Rows |
|---|---|---|
| `counterparties` (customer master) | CSV | 2,370 |
| `facilities` | JSON Lines | 6,047 |
| `monthly_balances` | CSV | 74,799 |
| `fx_rates` | CSV | 252 |
| `group_limits` (the risk team's spreadsheet) | Excel | 420 |

<!--
[0:06 · 2 min]
- Every borrower, group and figure is made up: this isn't SMBC's real book.
- Borrowers belong to counterparty groups, such as a conglomerate with subsidiaries in several countries. Each group has an approved credit limit, set by the risk team and kept in a spreadsheet.
- The files sit in a Unity Catalog volume, smbc_workshop.raw.landing, as the source systems delivered them. There's also a small sector_emission_factors file for an optional ESG question.
- The fiscal year runs April to March. Remember that for Lab 2.
-->

---

# Your inbox this morning

Handover notes from the source-system owners:

- *"The customer master extract sometimes contains the same row twice."*
- *"Currency codes on facilities are typed by hand, so expect `usd`, `US$`, `S$` and `RMB`."*
- *"The trade-finance system writes dates as DD/MM/YYYY; the core loan system uses YYYY-MM-DD."*
- *"Bangkok re-sent its September trade-finance extract. Keep the latest copy of each row (see `extract_ts`)."*
- *"FX rates are captured on the last business day of each month, not always the calendar month end."*
- *"A few facilities were booked before the customer record was created in the master."*

<!--
[0:08 · 2 min]
- These are the kind of handover notes a data team really gets, and Lab 1 deals with each of them.
- Ask the room: which one would hurt the Credit Committee most? Don't answer yet; we reveal it after Lab 1.
-->

---

<!-- _class: invert -->

# Data engineering with Lakeflow

0:25 · 20 minutes · Low-code ETL with Lakeflow Designer and Lakeflow Jobs, and AI-assisted pipeline creation

<!--
[0:25 · 20 min]
- At most 8 minutes of slides; spend the rest live in the workspace.
- Slides: the date hook, Lakeflow at a glance, and the trust message. Then the live demo, which is the first few steps of Lab 1.
-->

---

# Quick question

## 03/04/2026

### 3 April or 4 March?

<!--
[0:26 · 1 min]
- Show of hands: who reads this as 3 April? Who reads 4 March?
- Both are in today's data: the trade-finance system writes DD/MM/YYYY, the core loan system writes YYYY-MM-DD.
- In this data, parsing only the ISO format silently drops USD 4,789.2m of exposure at 30 September 2026. Lab 1 handles both formats.
-->

---

# Lakeflow at a glance

| | What it does | In today's lab |
|---|---|---|
| **Lakeflow Connect** | Ingests data from source systems | Not in the lab: the landing volume stands in for it |
| **Lakeflow Designer** | Visual, AI-assisted data prep | Lab 1 core path |
| **Lakeflow Pipelines** | Spark Declarative Pipelines in SQL or Python, for engineers | Lab 1 stretch |
| **Lakeflow Jobs** | Orchestration: schedules and notifications | Lab 1 core path and stretch |

**Unity Catalog** sits under all four: the same permissions and lineage, whichever tool built the table. It fits alongside existing Azure Data Factory and Synapse estates; adopt one piece at a time.

<!--
[0:28 · 2 min]
- Lab 1 uses Designer and Jobs in the core path, and Pipelines in the engineer's stretch exercise.
- Position it next to what people run today. Nobody has to replace everything at once.
-->

---

# No-code without shadow IT

1. **Generated code:** every Designer operator is backed by code you can view.
2. **Versioned:** version history shows a visual diff; commit it to a Git folder.
3. **Scheduled:** run it as a Lakeflow Job, on a schedule or when a file arrives.
4. **Governed:** Unity Catalog permissions and lineage on everything it reads and writes.

<!--
[0:30 · 2 min]
- The trust message: no-code without shadow IT.
- In Designer, open Table of contents, select an operator and expand Generated code: every visual step is real code you can review and version.
- Version history (right pane) shows a visual diff of changes, and the visual data prep can be committed to a Git folder.
- The Schedule button turns it into a Lakeflow Job, and Unity Catalog governs every table it reads and writes.
-->

---

# Live demo: what you'll see

1. Drag `group_limits.xlsx` onto the canvas: it becomes a Source.
2. One Genie Code prompt adds a Prepare step.
3. Preview the step.
4. Open the generated code.

```text
Add a Prepare step that trims and upper-cases currency, maps US$ to USD, S$ to SGD and RMB to CNY, and parses
start_date and maturity_date whether they're written YYYY-MM-DD or DD/MM/YYYY.
```

<!--
[0:32 · about 12 min live]
Click path:
1. + New → Visual data prep. Rename it "Monday exposure report" and pick Serverless in the compute picker.
2. Drag group_limits.xlsx (downloaded from the landing volume beforehand) onto the canvas: Designer turns it into a Source operator. Show the preview.
3. Add Source → Browse existing → smbc_workshop → raw → landing → facilities.
4. Select it and type the prompt on the slide. Open the Prepare operator it adds and read its actions aloud.
5. Table of contents → select the operator → expand Generated code.
Fallbacks:
- Excel drag fails: Source → Browse existing → the group_limits folder.
- The prompt fails, or Genie Code prompts are unavailable (partner-powered AI features or cross-Geo processing are off, guide Appendix B). In the 27 Oct test, this prompt failed. Add a Prepare operator by hand with the formulas in workbook A.2, and show the dry-run screenshots.
- The AI output differs from the rehearsal: use it. That's why a person reviews every step.
-->

---

<!-- _class: invert -->

# Lab 1: Build the trusted exposure table

0:45 · 20 minutes: a 15-minute core path, then the close

Work in pairs, ideally an analyst and an engineer: **the engineer drives.**

<!--
[0:45 · 1 min]
- Goal: turn the raw extracts into gold_group_exposure, a table the Credit Committee can trust. Attendees remove the duplicates, quarantine the bad rows, roll up to each counterparty group, and publish the result as a daily job.
- They start from bronze.exposure_staging. The workshop's daily job has already joined the extracts and converted them to USD and JPY, but nobody has checked the result.
- Nothing in Lab 2 depends on finishing Lab 1: the gold reference tables have the same result.
- The full steps are in the lab workbook PDF and in notebook 01 in the Labs folder.
- Helpers: watch for red cards, and for anyone without a Source on the canvas after three minutes.
-->

---

# Lab 1 at a glance

| Step | You do | Check |
|---|---|---|
| **1. Bring in the data** (3 min) | **+ New → Visual data prep**; **Serverless**; **Preview → All rows**; **Source** `bronze.exposure_staging` | 76,166 rows |
| **2. Fix the data quality** (7 min) | **Unique** by `facility_id`, `as_of_date`, latest `extract_ts` → **Guardrails**, **Failed** → a quarantine Output | 74,757 rows · 474 failed rows |
| **3. Roll up and publish** (5 min) | **Aggregate** by group and month → **Output** `gold_group_exposure` → **Run all** → **Schedule** at 07:00 | 7,174 rows; the checkpoint totals match |

<!--
[Leave on screen during the lab]
Core path, 15 minutes: 1 bring in the data (3 min) · 2 fix the data quality (7) · 3 roll up and publish (5).
Total exposure at 30 Sep 2026, in USD m: 28,287.1 in the staging table → 27,459.0 after Unique → 27,239.8 after Guardrails, which is the checkpoint figure.
Helpers, watch for:
- Counts don't match the workbook: Preview isn't set to All rows.
- Unique leaves 74,799 rows: it's set to All columns. The re-sent rows differ in extract_ts, so it needs facility_id and as_of_date.
- Total too high: the Aggregate isn't reading Guardrails' Passed output.
- Total far too low: the Aggregate is reading the Failed output.
- Output fails with a permission error: writing outside their own schema. Set the output location to smbc_workshop.<your_schema>.
- Can't see the bronze schema: a missing grant. Tell a facilitator.
-->

---

# Lab 1 · Step 1: bring in the data

- **+ New → Visual data prep**. Rename it `Monday exposure report`; compute: **Serverless**.
- Canvas toolbar: **Preview → All rows**.
- **Source → Browse existing →** `smbc_workshop` → `bronze` → **`exposure_staging`**: **76,166 rows**.

This table has the extracts joined and converted to USD and JPY. Nobody has checked it yet.

<!--
[0:46 · 3 min]
- The workshop's daily job builds exposure_staging every morning: balances joined to their facilities, customers and FX rates, with the currency codes and both date formats cleaned.
- Previews process the first 1,000 rows by default. All rows makes the counts match the workbook.
- The problems in the source-system owners' notes are still in it. Ask the room which ones they expect to find.
-->

---

# Lab 1 · Step 2: fix the data quality

| Add | Settings | Check |
|---|---|---|
| **Unique** | **Selected columns** `facility_id`, `as_of_date`; order by `extract_ts` descending | **76,166 → 74,757** |
| **Guardrails** | Expressions `committed_amount > 0` and `maturity_date >= start_date`; `parent_group_id` not null. **Failed** → Output `quarantine_facilities` | **474 failed rows**, from 36 facilities |

<!--
[0:49 · 7 min]
- Unique removes 1,409 rows: the 42 rows of Bangkok's re-sent trade-finance extract for 30 September 2026, and 1,367 copies created by 45 duplicate customer records. What's left is one row per facility and month end.
- Guardrails: 12 facilities have a commitment of zero or less, 9 mature before they start, and 15 have no customer record. Use Expression checks, because a Value range check includes 0.
- The Errors output lists the checks that failed. That's the evidence an auditor asks for.
-->

---

# Lab 1 · Step 3: roll up and publish

- After Guardrails' **Passed** output: **Aggregate**, grouped by `as_of_date`, `parent_group_id` and `group_name`, with the **SUM** of `exposure_usd` and of `exposure_jpy`, keeping those names. **7,174 rows.**
- **Output:** table `gold_group_exposure` in your schema, **Write mode: Overwrite**.
- **Run all**, then **Schedule** it: every day at **07:00**, Singapore time, on Serverless.
- **Table of contents →** any operator **→ Generated code**.

<!--
[0:56 · 5 min]
- A counterparty group's exposure includes all of its subsidiaries in every country. That's why we aggregate by parent_group_id.
- Run all runs every operator on all rows and writes both Outputs.
- Schedule turns the visual data prep into a Lakeflow Job. 07:00 is an hour after the workshop's daily data refresh.
- When the Output exists, the participant's row turns green on the progress board.
-->

---

# Lab 1 checkpoint

Your row on the progress board turns green. The two totals should be **identical**:

```sql
SELECT round(sum(exposure_usd) / 1e6, 1) AS mine_usd_m
FROM smbc_workshop.<your_schema>.gold_group_exposure WHERE as_of_date = '2026-09-30';

SELECT round(sum(exposure_usd) / 1e6, 1) AS reference_usd_m
FROM smbc_workshop.gold.group_exposure WHERE as_of_date = '2026-09-30';
```

- **Higher?** The Aggregate isn't reading Guardrails' **Passed** output, or the Unique isn't set up as in step 2.
- **Much lower?** The Aggregate is reading the **Failed** output.
- **Short on time?** Use `smbc_workshop.gold`: the same result, ready for Lab 2.

<!--
[From about 1:01]
- Run both queries in the SQL editor. Notebook 01 in the Labs folder has a version that works out your schema from your login.
- 1:01: anyone who hasn't finished moves on. Lab 2 uses the gold reference tables.
-->

---

# Lab 1 stretch: pick any

| | |
|---|---|
| **Compare with limits** | Join `silver.group_limits` and add `utilisation_pct`: workbook A.2 |
| **Start from the raw files** | Build the staging step yourself from the extracts: workbook A.2 |
| **Version and diff** | See a visual diff of your changes, then commit to a Git folder |
| **Engineer's path** | Rebuild the facility cleaning in the Lakeflow Pipelines Editor, with expectations |
| **Alerting** | Notify someone when any group is above 90% utilisation |
| **Document it** | Accept or edit the AI-suggested description for `gold_group_exposure` |

<!--
[For anyone who finishes the core path early]
- Engineer's path: Genie Code in the Lakeflow Pipelines Editor, with expectations, for example CONSTRAINT valid_commitment EXPECT (committed_amount > 0) ON VIOLATION DROP ROW. Compare the data-quality metrics with the Guardrails output.
- Document it: better metadata means better Genie answers in Lab 2.
-->

---

# Lab 1 debrief

## USD 366.9m

What Bangkok's re-sent trade-finance extract would have added to the Credit Committee pack. One Unique step, keeping the latest `extract_ts`, prevented it.

- **1,409** duplicate rows removed: 42 from the re-sent extract, and 1,367 from 45 duplicate customer records
- **36** facilities held back: 12 with a negative commitment, 9 that mature before they start, 15 with no customer record

**Lineage:** Catalog Explorer → `gold_group_exposure` → **Lineage** traces every step back to the raw files.

<!--
[1:02 · 3 min]
- Open Catalog Explorer → gold_group_exposure → Lineage, and trace it back through exposure_staging to the raw files. That's lineage evidence nobody had to draw by hand.
- Then the reveal: Bangkok's re-sent extract for 30 September 2026 duplicated 42 balance rows. Without the Unique step, the Credit Committee pack would have overstated exposure by USD 366.9m.
- Every held-back row is in the quarantine table, and the Errors output records which checks failed. That's your data-quality evidence.
-->

---

<!-- _class: invert -->

# 15-minute break

Back at __:__

Lab 1 not finished? The gold reference tables have the same result.

<!--
[1:05 · 15 min]
- Fill in the clock time before the day: back at 1:20, relative to the start.
- Put the progress board on screen during the break.
-->

---

<!-- _class: invert -->

# Self-service analytics

1:20 · 20 minutes · AI/BI dashboards, Genie Agents and Genie One

<!--
[1:20 · 20 min]
- At most 8 minutes of slides, the rest live.
-->

---

# Three tools, one message

**Dashboards** for the questions you know.

**Genie Agents** for the ones you don't know yet.

**Genie One** is where business users find both.

<!--
[1:41 · 2 min]
- Dashboards answer the questions the Credit Committee always asks. A Genie Agent answers the follow-ups nobody built a chart for. Genie One is the simple front door for business users.
-->

---

# Curation is the job

1. **Governed definitions:** metric views, so exposure and utilisation mean one thing
2. **Instructions:** business rules, such as the April-to-March fiscal year
3. **Example SQL:** how your team answers common questions
4. **Benchmarks:** test questions with expected SQL, to measure accuracy before you share

<!--
[1:43 · 2 min]
- A Genie Agent is only as good as what it has been taught. Curation is the job, not an afterthought.
- Lab 2 shows what happens without a fiscal-year instruction.
-->

---

# Trust, but verify

- Every answer shows its SQL. **Open it.**
- Genie queries data **as the person asking**: Unity Catalog permissions, row filters and column masks apply.
- Generated queries are **read-only**.
- **Benchmarks** measure accuracy before you share an agent.
- The same governed data serves AI/BI dashboards, Genie Agents, and BI tools such as Power BI.

<!--
[1:45 · 2 min]
- A question about data you can't access returns an empty response.
- We show the permissions live in the governance moment at the end of Lab 2.
- Keep the BI point general: coexistence, not replacement.
-->

---

# Live demo: what you'll see

1. The Credit Committee dashboard
2. Genie One, as a business user sees it
3. A question in English, then in Japanese
4. The SQL behind the answer

「2026年度第2四半期末時点の、計上店別の円建てエクスポージャーを教えてください。」

<!--
[1:47 · about 12 min live]
Click path:
1. Open the published reference dashboard, "Credit Committee: APAC exposure (reference)". Walk through the counters, the top-10 chart and the trend.
2. Open <workspace URL>/one, signed in as the Consumer-access demo user: Genie One shows dashboards and Genie Agents, with no notebooks or compute.
3. Open the "Credit Risk (reference)" agent and ask "Show exposure in yen by booking branch at the latest month end", then the Japanese question on the slide: exposure in yen by booking branch (計上店) at the end of FY2026 Q2.
4. Open the SQL behind the answer.
Notes:
- These questions don't give away the Lab 2 answer. The dashboard's top-10 chart does show it, so don't dwell on the top bar.
- Tested on 15 October: Genie read the end of FY2026 Q2 as 30 September 2026, used exposure_jpy by booking branch, and answered in Japanese in about 20 seconds. Answers can sometimes come back in English.
- Talk through the dashboard while Genie works.
Fallback: if the Consumer-access user or Genie One chat fails, use the agent from Genie Agents in your own session.
-->

---

<!-- _class: invert -->

# Lab 2: Credit Committee in 30 seconds

1:40 · 40 minutes: a 25-minute core path and 15 minutes of stretch

Swap drivers: **the analyst drives.** Use the gold reference tables, so everyone's answers match.

<!--
[1:40 · 40 min]
- Goal: a dashboard for the questions the Credit Committee always asks, and a Genie Agent for the ones they haven't asked yet. Teach the agent the bank's rules, and test that it's right.
- The tables: smbc_workshop.gold.group_exposure and smbc_workshop.gold.facility_exposure.
-->

---

# Lab 2 at a glance

| Time | Step |
|---|---|
| 10 min | **1. Build the dashboard:** counters, charts, filters; publish |
| 5 min | **2. Create a Genie Agent:** instructions, example SQL, questions |
| 5 min | **3. Ask, and open the SQL** behind each answer |
| 4 min | **4. The fiscal-year test:** before and after the instruction |
| | ✅ **Checkpoint:** submit the group you found |

<!--
[Leave on screen during the lab]
Timings: 1:50 dashboards published; 1:55 agents created; 2:04 fiscal-year test done; 2:05 answers submitted.
Helpers, watch for:
- Genie Agents won't open: partner-powered AI features are off. Tell a facilitator.
- Genie picks the wrong dates for "Q1 FY2026", "FY2025" or "FY2026 H1": expected until the fiscal-year instruction (A.4) is added.
- A dashboard subscription email doesn't arrive: mail filtering. Use a PDF download instead.
- The load on Genie is staggered naturally: everyone starts with the dashboard.
-->

---

# Lab 2 · Step 1: build the dashboard

- **+ New → Dashboard.** On the **Data** tab, add both gold tables.
- Ask Genie Code on the canvas:

```text
Bar chart of the top 10 counterparty groups by exposure_usd at the latest as_of_date, coloured by utilisation_pct.
```

- Add a **counter** for total exposure at the latest month end, a **counter** for groups above 80% utilisation, a **line chart** of total exposure by month, and a **bar chart** of exposure by country.
- Add filters for `as_of_date` and `booking_branch`, then **Publish**.
- Open `<workspace URL>/one`: Genie One, what a business user sees.

<!--
[1:40 · 10 min]
- Genie Code drafts the chart; people adjust it. That's the pattern for the whole lab.
- Shortlist 2–3 good dashboards for the Best dashboard vote during the second break.
-->

---

# Lab 2 · Step 2: create a Genie Agent

- **Genie Agents → New**, select the two gold tables, click **Create**.
- Genie Code suggests descriptions and example queries. Review them, and accept the ones that are right.
- **Configure → Settings:** title `Credit Risk – <your name>`, default warehouse: the one you checked in with.
- Add from the workbook: the starter instructions (**A.3**), the two example SQL queries (**A.5**) and the common questions (**A.6**).

**Don't add the fiscal-year instruction (A.4) yet.**

<!--
[1:50 · 5 min]
- The starter instructions define exposure, utilisation, month-end balances, groups, branch codes and arrears.
- Holding back A.4 is deliberate: step 4 shows what happens without it.
-->

---

# Lab 2 · Step 3: ask, and check the SQL

> *"Which counterparty groups are closest to their limits?"*

> *"Show exposure in yen by booking branch at the latest month end."*

Open the generated SQL for each answer. **Trust, but verify.**

<!--
[1:55 · 5 min]
- Check which table it used, which as_of_date it filtered on, and whether yen came from exposure_jpy.
- In testing, the first question put the most utilised group at the top, at 94%.
-->

---

# Lab 2 · Step 4: the fiscal-year test

Before adding the fiscal-year instruction, ask:

> *"What was Orchid Group's utilisation at the end of Q1 FY2026?"*

> *"Show Orchid Group's utilisation for each month of FY2025."*

Open the SQL: **which dates did Genie use?** Then add the fiscal-year instruction (**A.4**) and ask both again.

<!--
[2:20 · 4 min]
- Don't give the answer away here; we compare results in the debrief.
- The instruction (A.4): the fiscal year runs from 1 April to 31 March and is named after the calendar year it starts in. FY2026 = 1 April 2026 to 31 March 2027.
-->

---

# Lab 2 checkpoint

1. Ask your Genie Agent:

> *"Which groups were above 90% of their limit at the end of FY2026 H1?"*

2. Submit the name of the group:

```sql
INSERT INTO smbc_workshop.ops.lab_answers SELECT current_user(), 'lab2', '<group name>', current_timestamp();
```

Correct answers appear on the progress board.

<!--
[From about 2:05]
- Replace <group name> with the group the agent found, then run the line in the SQL editor.
- If an answer looks wrong, check the as_of_date in the SQL: FY2026 H1 ends on 30 September 2026.
-->

---

# Lab 2 stretch: pick any

| | |
|---|---|
| **Stump the Genie** | Find a question it gets wrong, fix it with an instruction or example query, ask again. Best stump-and-fix wins a prize |
| **Benchmarks** | Add the benchmark questions (A.7) with their expected SQL and run an evaluation |
| **Agent mode** | *"Why has the most utilised group's limit usage risen since April 2026?"* |
| **In Japanese** | 「2026年度上期末時点で、与信限度額の90%を超えている取引先グループはどこですか？」 |
| **Share it** | Attach the agent to your dashboard, or schedule a Monday 08:00 PDF subscription |
| **Semantic layer** | The agent's ⋮ menu → **Export to metric view** |

<!--
[For anyone who finishes the core path early]
- Stump the Genie, a tested starter: "Which booking branch has the highest share of trade finance in arrears?" In one test run Genie counted facilities; in another it weighted by exposure and asked which one we meant. The instruction "Shares of arrears are measured by exposure (exposure_usd), not by number of facilities" makes the answer consistent. Facilitators pick the best stump-and-fix.
- Agent mode: watch it plan, run several queries and write a report.
- In Japanese: answers may sometimes come back in English.
-->

---

# Lab 2 debrief: what we saw in testing

| Without the fiscal-year instruction | With it |
|---|---|
| "Q1 FY2026" read as January–March 2026: *"70.0%, not near its limit"* | Q1 FY2026 ends on 30 June 2026: 79.0% |
| "FY2025" read as calendar 2025 | FY2025 = April 2025 to March 2026 |

**Without explicit rules the AI guesses, and it doesn't guess the same way every time.**

## 94%

Orchid Group at 30 Sep 2026: the only group above 90% of its limit. Its largest subsidiary ranks only **#24** among borrowers.

<!--
[2:18 · 2 min]
- From testing on 15 October. Yet Genie guessed "end of FY2026 H1" correctly as 30 September, which is why the checkpoint question worked even before the instruction.
- That's why curation and benchmarks matter before anyone shares an agent with a credit committee.
- The finding: at the end of calendar H1 (30 June) no group was above 90%; at the end of FY2026 H1, Orchid Group was at 94%. It's invisible one subsidiary at a time.
-->

---

# Governance moment: same question, two answers

> *"What is our total exposure by booking branch at the latest month end?"*

| Facilitator | Attendee |
|---|---|
| All 12 booking branches | Singapore branch only (row filter) |
| Borrower names in full | Borrower names masked (column mask) |

**Genie gets no superpowers: it inherits Unity Catalog permissions.**

<!--
[2:15 · 3 min]
- The demo agent "Credit Risk (secured demo)" sits on a copy of the facility table with a row filter (Singapore branch only, unless you're on the facilitator list) and a mask on borrower names.
- A facilitator and a volunteer ask the same question on screen.
- In testing, the facilitator saw all 12 branches; the attendee saw SIN only, with names masked.
-->

---

<!-- _class: invert -->

# 15-minute break

Back at __:__

Next: Genie Code. Ask why, safely.

<!--
[2:20 · 15 min]
- Fill in the clock time before the day: back at 2:35, relative to the start.
- Progress board on screen: read out how many people found the group.
-->

---

<!-- _class: invert -->

# AI-assisted development with Genie Code

2:35 · 15 minutes · Ask why, safely

Follow along: open a notebook on **Serverless** and paste the prompts from the workbook (**A.8**).

<!--
[2:35 · 15 min]
- Mostly a live demo; participants can follow along in their own notebook.
- Many people already use Genie Code, so skip the autocomplete basics: lead with what it does as an agent, the legacy-SQL conversion and the approval settings.
-->

---

# Genie Code · 1. Explore

```text
Profile smbc_workshop.gold.group_exposure and tell me what is unusual about the latest month
compared with April 2026.
```

Watch it plan, run code and summarise what it found.

<!--
[2:56 · 3 min]
- Genie Code works as an agent: it plans, writes and runs code, fixes its own errors and summarises.
- Fallback: rehearse these exact prompts in the dry run and keep screenshots. If the output varies on the day, say so: that's why the human stays in the loop.
-->

---

# Genie Code · 2. Generate

```text
For the group with the highest utilisation at 30 Sep 2026, split the change in USD exposure between 30 Apr 2026
and 30 Sep 2026 into an FX effect and a new-drawdowns (volume) effect, by subsidiary, using
smbc_workshop.gold.facility_exposure. Use: volume = (Sep balance − Apr balance) × Apr rate;
FX = Sep balance × (Sep rate − Apr rate). Chart it.
```

This answers the **"why"** behind the Credit Committee's question.

<!--
[2:59 · 4 min]
- The formulas are in the prompt so the answer is reproducible.
- Let it run; talk through the plan it shows while it works.
-->

---

# Genie Code · 3. Explain and convert

```text
Explain what this procedure does and point out any risks in its logic. Then rewrite it as Databricks SQL against
the smbc_workshop.gold tables. Just explain first, don't run any code.
```

Then paste the legacy Synapse T-SQL procedure from the workbook (**A.9**).

<!--
[3:03 · 3 min]
- The procedure uses a temp table, ISNULL and CROSS APPLY, typical of what teams migrate from Synapse.
- "Don't run any code" gets an explanation only: a safety control people can use any time.
- For hundreds of stored procedures, Lakebridge (Databricks' migration toolkit) is the at-scale route.
-->

---

# You stay in control

1. **Approvals:** by default an AI classifier approves actions within your request and blocks actions beyond it; or approve every action yourself.
2. **"Don't run any code"** gets you an explanation only.
3. **Permissions:** Genie Code can only reach data your Unity Catalog permissions allow.
4. **Revision history** rolls back a change.

<!--
[3:06 · 3 min]
- Show the action-approval setting.
- Try a table you don't have access to: Genie Code can't reach it.
- Roll back a change with the notebook's revision history.
-->

---

# Why did Orchid's utilisation rise?

## 71% → 94%

Orchid Group's limit utilisation, 30 April → 30 September 2026. Of the **USD 345.0m** rise:

| FX | New drawdowns |
|---|---|
| **25%** · USD 86.2m | **75%** · USD 258.8m |

Four subsidiaries account for **94%** of the new drawdowns. That's a credit conversation, not just a currency one.

<!--
[3:09 · 1 min]
- The "why" half of the CDAO's question.
- Measured on April balances instead, FX is 19%, so say which method you used.
-->

---

# Quiz: join on your phone

**Slido:** event code `#____` (or scan the QR code)

12 questions, about 20 seconds each

**Prizes:** quiz top three · Best Stump the Genie · First to finish Lab 1 · Best dashboard (peer vote)

<!--
[2:50 · 15 min]
- The questions and answers are in facilitator/quiz.md. After each question, say its one-line teaching point: that's what people remember.
- First to finish Lab 1 comes from the progress board's "First to finish" table.
- If Slido is blocked on the SMBC network: phones on mobile data, or read the questions out and take answers by show of hands.
-->

---

# What you found today

| | |
|---|---|
| **94%** | Orchid Group's limit utilisation at 30 Sep 2026: the only group above 90% |
| **#24** | Where its largest subsidiary ranks among borrowers: invisible one entity at a time |
| **25% FX** | Of Orchid's rise since April; the rest is new drawdowns, mostly by four subsidiaries |
| **USD 366.9m** | The overstatement from Bangkok's re-sent extract, caught by one Unique step |
| **1.1% → 9.6%** | Ho Chi Minh City trade-finance arrears, March to September 2026 |

<!--
[3:05 · 2 min]
- Back to the CDAO's question. Which group? Orchid Group, visible only once its subsidiaries are rolled up to the group. Why? Three-quarters new drawdowns, mostly by four subsidiaries, and a quarter FX.
- A second signal to follow up: trade-finance arrears in Ho Chi Minh City crept from 1.1% to 9.6% of exposure, against 0.4% across the whole book.
-->

---

# Keep learning

- **Free self-paced training and learning paths:** databricks.com/learn/training
- **Certifications** (Data Analyst Associate, Data Engineer Associate): databricks.com/learn/certification
- **Databricks Free Edition,** for practice outside work: databricks.com/learn/free-edition
- **Free virtual workshops:** 4 Nov *Hands-on with Genie* · 12 Nov *AI-Powered Data Engineering with Lakeflow* · 18 Nov *Build, Orchestrate and Improve Agents* (Americas time slots; recordings available): databricks.com/learn/training/workshop
- **Documentation:** Lakeflow Designer, Genie Agents, Genie One and Genie Code at learn.microsoft.com/azure/databricks

<!--
[3:27 · 3 min]
- The free virtual workshops run in Americas time slots, so point people to the recordings.
- Add a QR code to databricks.com/learn/training when you generate the deck.
-->

---

# Proposed next step: a 30-day Genie Agent challenge

1. **Nominate:** each team nominates one real business question set.
2. **Office hours:** the Databricks team holds weekly 30-minute office hours.
3. **Pilot:** leading into a pilot in SMBC's own workspace.

<!--
[3:30 · 2 min]
- A proposal: agree the wording with SMBC before the day.
-->

---

<!-- _class: invert -->
<!-- _paginate: false -->

# Thank you

The feedback survey is your raffle ticket.

All workshop data is synthetic: the borrowers, groups and figures are made up.

<!--
[3:33]
- Add the survey QR code when you generate the deck.
- Prize-giving: quiz top three, Best Stump the Genie, First to finish Lab 1, Best dashboard.
- Thank the SMBC organisers and the helpers.
-->
