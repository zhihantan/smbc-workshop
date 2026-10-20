# Databricks notebook source
# MAGIC %md
# MAGIC # 05 · Governance demo: row filter and column mask (facilitator, 3 minutes in Lab 2)
# MAGIC
# MAGIC Shows that a Genie Agent inherits Unity Catalog security: two people ask the same question and get
# MAGIC different, correct answers. Works on a **copy** of the gold table so participants' own Genie Agents are
# MAGIC unaffected.
# MAGIC
# MAGIC 1. Run this notebook after `02_build_checkpoints`. The facilitators are you plus anyone in `facilitator_emails`;
# MAGIC    no groups are needed. Re-run it to change the list.
# MAGIC 2. `06_deploy_dashboards_and_agents` then creates the Genie Agent **Credit Risk (secured demo)** on this table and
# MAGIC    shares it with everyone in the workspace.
# MAGIC 3. On the day: ask *"What is our total exposure by booking branch at the latest month end?"* as a facilitator, then
# MAGIC    have a volunteer attendee ask the same question on the projector. They see Singapore only, with masked names.
# MAGIC
# MAGIC The filter and mask run with the function owner's rights, except `session_user()`, which is the person asking. So
# MAGIC attendees need no privilege on the functions, only `SELECT` on the table.

# COMMAND ----------

dbutils.widgets.text("facilitator_emails", "", "Other facilitators' emails, comma-separated (you're included)")
me = spark.sql("SELECT session_user()").first()[0]
facilitators = []
for email in [me] + dbutils.widgets.get("facilitator_emails").split(","):
    email = email.strip().lower().replace("'", "")  # goes inside a SQL string literal
    if email and email not in facilitators:
        facilitators.append(email)
is_facilitator = "lower(session_user()) IN (" + ", ".join(f"'{f}'" for f in facilitators) + ")"
table = "smbc_workshop.checkpoint.gold_facility_exposure_secured"

spark.sql(f"""CREATE OR REPLACE TABLE {table}
  COMMENT 'Copy of gold_facility_exposure with a row filter (Singapore branch only unless you are a facilitator) and a masked borrower name. SYNTHETIC DATA.'
  AS SELECT * FROM smbc_workshop.checkpoint.gold_facility_exposure""")

# Row filter: facilitators see everything; everyone else sees only facilities booked in Singapore.
spark.sql(f"""CREATE OR REPLACE FUNCTION smbc_workshop.ops.singapore_branch_only(booking_branch STRING)
  RETURNS BOOLEAN
  COMMENT 'Row filter for the governance demo'
  RETURN {is_facilitator} OR booking_branch = 'SIN'""")

# Column mask: facilitators see borrower names; everyone else sees the first word only.
spark.sql(f"""CREATE OR REPLACE FUNCTION smbc_workshop.ops.mask_borrower_name(name STRING)
  RETURNS STRING
  COMMENT 'Column mask for the governance demo'
  RETURN CASE WHEN {is_facilitator} THEN name
              ELSE concat(split(name, ' ')[0], ' ••••') END""")

spark.sql(f"ALTER TABLE {table} SET ROW FILTER smbc_workshop.ops.singapore_branch_only ON (booking_branch)")
for column in ("counterparty_name", "counterparty_name_local"):
    spark.sql(f"ALTER TABLE {table} ALTER COLUMN {column} SET MASK smbc_workshop.ops.mask_borrower_name")
print(f"{table} is ready: {', '.join(facilitators)} see every branch; everyone else sees SIN only, with names masked")

# COMMAND ----------

# MAGIC %md What you see as a facilitator (all branches). Run the same query as a test attendee to see Singapore only.

# COMMAND ----------

display(spark.sql(f"""
  SELECT booking_branch, round(sum(exposure_usd) / 1e6, 1) AS exposure_usd_m, count(DISTINCT counterparty_id) AS borrowers
  FROM {table}
  WHERE as_of_date = '2026-09-30'
  GROUP BY booking_branch
  ORDER BY exposure_usd_m DESC"""))

# COMMAND ----------

# MAGIC %md To undo after the session (`08_reset_or_teardown` → `teardown` also removes them):
# MAGIC ```sql
# MAGIC DROP TABLE smbc_workshop.checkpoint.gold_facility_exposure_secured;
# MAGIC DROP FUNCTION smbc_workshop.ops.singapore_branch_only;
# MAGIC DROP FUNCTION smbc_workshop.ops.mask_borrower_name;
# MAGIC ```
