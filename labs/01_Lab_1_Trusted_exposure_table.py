# Databricks notebook source
# MAGIC %md
# MAGIC # Lab 1: Build the trusted exposure table
# MAGIC
# MAGIC *SMBC Data & AI Workshop*
# MAGIC
# MAGIC > **All workshop data is synthetic.** The labs use a made-up SMBC APAC corporate lending book: every borrower, group, limit and balance is fictional. No SMBC data, systems or customer information is used at any point.
# MAGIC
# MAGIC This is a read-only copy. To run its cells, use **File → Clone** to copy it to your own folder, or paste the SQL into the SQL editor.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Lab 1: Build the trusted exposure table
# MAGIC
# MAGIC **Goal:** turn the raw extracts into `gold_group_exposure`, a table the Credit Committee can trust, with bad rows quarantined, duplicates removed, and every step visible as code and as lineage.
# MAGIC **Time:** 40 minutes, made up of a 25-minute core path and 15 minutes of stretch exercises.
# MAGIC **Tools:** Lakeflow Designer, Genie Code, Lakeflow Jobs, Unity Catalog.
# MAGIC
# MAGIC > **Short on time?** Nothing in Lab 2 depends on finishing Lab 1: the gold reference tables have the same result. Work in pairs, ideally one analyst and one engineer, with the engineer driving.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Core path
# MAGIC
# MAGIC **0. Find your schema (1 min).** Your check-in created it and showed its name: the part of your email address before the @, for example `jane_tan`. Find it in **Catalog Explorer** → `smbc_workshop`. Not there? Run the check-in block (A.1) again.
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
# MAGIC ✅ **Checkpoint:** your row on the progress board turns green. To check your result against the reference, run both queries (notebook *01* in the Labs folder works out your schema for you); the two totals should be identical:
# MAGIC
# MAGIC ```sql
# MAGIC SELECT round(sum(exposure_usd) / 1e6, 1) AS mine_usd_m
# MAGIC FROM smbc_workshop.<your_schema>.gold_group_exposure WHERE as_of_date = '2026-09-30';
# MAGIC
# MAGIC SELECT round(sum(exposure_usd) / 1e6, 1) AS reference_usd_m
# MAGIC FROM smbc_workshop.gold.group_exposure WHERE as_of_date = '2026-09-30';
# MAGIC ```

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Compare your Lab 1 result with the reference. Your schema is worked out from your login.
# MAGIC BEGIN
# MAGIC   DECLARE my_schema STRING DEFAULT regexp_replace(lower(split_part(current_user(), '@', 1)), '[^a-z0-9_]', '_');
# MAGIC   SELECT my_schema,
# MAGIC          (SELECT round(sum(exposure_usd) / 1e6, 1) FROM IDENTIFIER('smbc_workshop.' || my_schema || '.gold_group_exposure')
# MAGIC           WHERE as_of_date = '2026-09-30') AS mine_usd_m,
# MAGIC          (SELECT round(sum(exposure_usd) / 1e6, 1) FROM smbc_workshop.gold.group_exposure
# MAGIC           WHERE as_of_date = '2026-09-30') AS reference_usd_m;
# MAGIC END

# COMMAND ----------

# MAGIC %md
# MAGIC ### Stretch (pick any)
# MAGIC
# MAGIC - **Version and diff:** open the version history (right pane) to see a visual diff of your changes. Then commit the visual data prep to a Git folder.
# MAGIC - **Engineer's path:** rebuild the facility cleaning in the **Lakeflow Pipelines Editor** with Genie Code, using expectations (`CONSTRAINT valid_commitment EXPECT (committed_amount > 0) ON VIOLATION DROP ROW`). Compare the data-quality metrics with your Guardrails output.
# MAGIC - **Alerting:** add a task that checks *"any group above 90% utilisation?"* and sends a notification when it's true.
# MAGIC - **Document it:** in Catalog Explorer, accept or edit the AI-suggested description for `gold_group_exposure`. Better metadata means better Genie answers in Lab 2.
