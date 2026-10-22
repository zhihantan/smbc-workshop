# Databricks notebook source
# MAGIC %md
# MAGIC # Lab 2: Credit Committee in 30 seconds
# MAGIC
# MAGIC *SMBC Data & AI Workshop*
# MAGIC
# MAGIC > **All workshop data is synthetic.** The labs use a made-up SMBC APAC corporate lending book: every borrower, group, limit and balance is fictional. No SMBC data, systems or customer information is used at any point.
# MAGIC
# MAGIC This is a read-only copy. To run its cells, use **File → Clone** to copy it to your own folder, or paste the SQL into the SQL editor.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Lab 2: Credit Committee in 30 seconds
# MAGIC
# MAGIC **Goal:** give the Credit Committee a dashboard for the questions they always ask, and a Genie Agent for the ones they haven't asked yet. Teach the agent the bank's rules, and test that it's right.
# MAGIC **Time:** 40 minutes, made up of a 25-minute core path and 15 minutes of stretch exercises.
# MAGIC **Tools:** AI/BI dashboards, Genie Agents, Genie One, Unity Catalog.
# MAGIC
# MAGIC > Use the **gold** reference tables (`smbc_workshop.gold.group_exposure` and `smbc_workshop.gold.facility_exposure`) so everyone's answers match. If you finished Lab 1, your own tables give the same numbers.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Core path
# MAGIC
# MAGIC **1. Build the dashboard (10 min).**
# MAGIC - Click **+ New → Dashboard**. On the **Data** tab, add both gold tables.
# MAGIC - On the canvas, ask Genie Code: *"Bar chart of the top 10 counterparty groups by exposure_usd at the latest as_of_date, coloured by utilisation_pct."*
# MAGIC - Add these widgets:
# MAGIC   - a **counter** for total exposure at the latest month end;
# MAGIC   - a **counter** for groups above 80% utilisation;
# MAGIC   - a **line chart** of total exposure by month;
# MAGIC   - a **bar chart** of exposure by country.
# MAGIC - Add filters for `as_of_date` and `booking_branch`, then **Publish**.
# MAGIC - Open `<workspace URL>/one`: this is Genie One, what a business user sees.
# MAGIC
# MAGIC **2. Create a Genie Agent (5 min).**
# MAGIC - Click **Genie Agents → New**, select the two gold tables (`group_exposure` and `facility_exposure`), and click **Create**.
# MAGIC - Genie Code reads the tables and suggests descriptions and example queries. Review them, and accept the ones that are right.
# MAGIC - In **Configure → Settings**, set the title to `Credit Risk – <your name>` and the default warehouse to the SQL warehouse you checked in with.
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
