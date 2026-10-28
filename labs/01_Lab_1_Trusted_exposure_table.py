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
# MAGIC **Goal:** turn the raw extracts into `gold_group_exposure`, a table the Credit Committee can trust. You remove the duplicates, quarantine the bad rows, roll up to each counterparty group, and publish the result as a daily job, with every step visible as code and as lineage.
# MAGIC **Time:** 20 minutes: a 15-minute core path, then a 3-minute facilitator close.
# MAGIC **Tools:** Lakeflow Designer, Lakeflow Jobs, Unity Catalog.
# MAGIC
# MAGIC > **Short on time?** Nothing in Lab 2 depends on finishing Lab 1: the gold reference tables have the same result. Work in pairs, ideally one analyst and one engineer, with the engineer driving.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Core path
# MAGIC
# MAGIC You start from `smbc_workshop.bronze.exposure_staging`, which the workshop's daily job builds from the extracts every morning. It joins the balances to their facilities, customers and FX rates. It cleans the currency codes and both date formats, and converts to USD and JPY. Nobody has checked it, though. The problems in the source-system owners' notes are still in it, so its total is too high. Making it trustworthy is your job.
# MAGIC
# MAGIC **1. Start and bring in the data (3 min).**
# MAGIC - Click **+ New → Visual data prep**. Rename the tab to `Monday exposure report`. In the compute picker at the top right, choose **Serverless**.
# MAGIC - In the canvas toolbar, open **Preview** and select **All rows**. By default, previews process only the first 1,000 rows, and the row counts in this lab are for all rows.
# MAGIC - Add a **Source** operator → **Browse existing** → `smbc_workshop` → `bronze` → **`exposure_staging`**. The preview shows 76,166 rows: one for each balance, with its facility, customer, group, and exposure in USD and JPY.
# MAGIC
# MAGIC **2. Fix the data quality (7 min).** Add these two operators, the first after the Source and the second after the first:
# MAGIC
# MAGIC | Add | Settings | Check |
# MAGIC |---|---|---|
# MAGIC | **Unique** | **Unique by: Selected columns** `facility_id` and `as_of_date`, and **Order by** `extract_ts` descending, so that the latest copy of each row is kept | 76,166 → 74,757 rows: one for each facility and month end. This removes Bangkok's re-sent extract and the extra rows from duplicate customer records |
# MAGIC | **Guardrails** | **Expression** checks `committed_amount > 0` and `maturity_date >= start_date` (not **Value range**, which includes 0), and a **Not null** check on `parent_group_id`. **When a check fails:** **Warn and continue with passed rows**. Connect **Failed** to an **Output** that writes the table `quarantine_facilities` to your schema | 474 failed rows, from 36 facilities: 12 with a negative commitment, 9 that mature before they start, and 15 whose customer isn't in the master yet. The **Errors** output lists the checks that failed. That's your data-quality evidence |
# MAGIC
# MAGIC **3. Roll up and publish (5 min).**
# MAGIC - After Guardrails' **Passed** output, add **Aggregate**. **Group by** `as_of_date`, `parent_group_id` and `group_name`. Under **Aggregate by**, add the **SUM** of `exposure_usd`, named `exposure_usd`, and the **SUM** of `exposure_jpy`, named `exposure_jpy`. That gives 7,174 rows, one per group and month.
# MAGIC - After the Aggregate, add an **Output**: **Table** `gold_group_exposure` in your schema (the one your check-in created), **Write mode: Overwrite**.
# MAGIC - Click **Run all** in the canvas toolbar. It runs every operator on all rows and writes both of your Outputs.
# MAGIC - Click **Schedule** in the header and set the visual data prep to run every day at 07:00, Singapore time, on Serverless compute.
# MAGIC - Open **Table of contents** in the left panel, select an operator, and expand **Generated code**. Every visual step is real code you can review and version.
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
# MAGIC - **Compare with limits:** add a **Join** with `smbc_workshop.silver.group_limits` on `parent_group_id` = `group_id`. Then add a **Prepare** step with a **Formula** action that creates `utilisation_pct`: `ROUND(100 * exposure_usd / group_limit_usd, 2)`.
# MAGIC - **Start from the raw files:** build the staging step yourself, from the extracts in `smbc_workshop.raw.landing`. A.2 has the formulas and join conditions.
# MAGIC - **Version and diff:** open the version history (right pane) to see a visual diff of your changes. Then commit the visual data prep to a Git folder.
# MAGIC - **Engineer's path:** rebuild the facility cleaning in the **Lakeflow Pipelines Editor** with Genie Code, using expectations (`CONSTRAINT valid_commitment EXPECT (committed_amount > 0) ON VIOLATION DROP ROW`). Compare the data-quality metrics with your Guardrails output.
# MAGIC - **Alerting:** add a task that checks *"any group above 90% utilisation?"* and sends a notification when it's true.
# MAGIC - **Document it:** in Catalog Explorer, accept or edit the AI-suggested description for `gold_group_exposure`. Better metadata means better Genie answers in Lab 2.
