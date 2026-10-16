# Databricks notebook source
# MAGIC %md
# MAGIC # 01 · Set up the workshop workspace
# MAGIC
# MAGIC Run once as a workspace admin (or anyone who can create catalogs and grant privileges), on serverless
# MAGIC compute. It is safe to re-run, for example after adding late registrations to `attendee_emails`.
# MAGIC
# MAGIC It creates:
# MAGIC
# MAGIC | Object | Purpose | Attendee access |
# MAGIC |---|---|---|
# MAGIC | `smbc_workshop.raw.landing` (volume) | The raw extracts and the limits spreadsheet | Read |
# MAGIC | `smbc_workshop.raw.facilitator` (volume) | Answer key and a CSV copy of the limits | None |
# MAGIC | `smbc_workshop.checkpoint` (schema) | Save-point tables built by `02_build_checkpoints` | Read |
# MAGIC | `smbc_workshop.ops` (schema) | Check-in and lab-answer tables for the progress board | Read + write |
# MAGIC | `smbc_workshop.<name>` (one schema per attendee) | Where each person's Lab 1 output goes | Full |
# MAGIC
# MAGIC Before running: create the attendee and facilitator groups (account console or SCIM from Entra ID) and add
# MAGIC them to this workspace. Next steps are listed at the end of the notebook.

# COMMAND ----------

dbutils.widgets.text("catalog", "smbc_workshop", "Catalog")
dbutils.widgets.text("managed_location", "", "Managed location (only if CREATE CATALOG asks for one)")
dbutils.widgets.text("attendee_group", "smbc_workshop_attendees", "Attendee group")
dbutils.widgets.text("facilitator_group", "smbc_workshop_facilitators", "Facilitator group")
dbutils.widgets.text("attendee_emails", "", "Attendee emails, comma-separated (creates one schema each)")
dbutils.widgets.dropdown("generate_data", "yes", ["yes", "no"], "Generate data into the landing volume")
dbutils.widgets.text("remove_after", "", "RemoveAfter tag, YYYYMMDD (Databricks FE workspaces only)")

catalog = dbutils.widgets.get("catalog").strip()
remove_after = dbutils.widgets.get("remove_after").strip()
managed_location = dbutils.widgets.get("managed_location").strip()
attendees = dbutils.widgets.get("attendee_group").strip()
facilitators = dbutils.widgets.get("facilitator_group").strip()
emails = [e.strip() for e in dbutils.widgets.get("attendee_emails").split(",") if e.strip()]

if catalog != "smbc_workshop":
    print(f"Note: 02_build_checkpoints.sql and 04/05 use 'smbc_workshop'. Find-and-replace it with '{catalog}'.")

# COMMAND ----------

# MAGIC %md ## Catalog, schemas, volumes, ops tables

# COMMAND ----------

location = f" MANAGED LOCATION '{managed_location}'" if managed_location else ""
spark.sql(f"CREATE CATALOG IF NOT EXISTS `{catalog}`{location} "
          "COMMENT 'SMBC Data & AI Workshop, 22 Oct 2026. All data is synthetic.'")
tags = {"synthetic_data": "true", "workshop_date": "2026-10-22"}
if remove_after:
    tags["RemoveAfter"] = remove_after
for key, value in tags.items():
    try:
        spark.sql(f"ALTER CATALOG `{catalog}` SET TAGS ('{key}' = '{value}')")
    except Exception as err:  # a governed tag policy may restrict a key; tags are optional
        print(f"Skipped tag {key}:", str(err).splitlines()[0])

for schema, comment in [
    ("raw", "Raw extracts as delivered by the source systems"),
    ("checkpoint", "Save-point tables: the reference solution for Lab 1"),
    ("ops", "Workshop operations: check-in and lab answers"),
]:
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{catalog}`.`{schema}` COMMENT '{comment}'")

spark.sql(f"CREATE VOLUME IF NOT EXISTS `{catalog}`.raw.landing COMMENT 'Source extracts for Lab 1 (synthetic)'")
spark.sql(f"CREATE VOLUME IF NOT EXISTS `{catalog}`.raw.facilitator COMMENT 'Answer key. Facilitators only.'")

spark.sql(f"""CREATE TABLE IF NOT EXISTS `{catalog}`.ops.checkin (
    user_email STRING, role STRING, checked_in_at TIMESTAMP)
  COMMENT 'One row per person who ran the check-in query'""")
spark.sql(f"""CREATE TABLE IF NOT EXISTS `{catalog}`.ops.lab_answers (
    user_email STRING, lab STRING, answer STRING, submitted_at TIMESTAMP)
  COMMENT 'Answers submitted at lab checkpoints'""")
print("Catalog objects ready")

# COMMAND ----------

# MAGIC %md ## Generate the synthetic data into the landing volume
# MAGIC
# MAGIC Imports `data/generate_data.py` from this repo (clone it as a Git folder so the relative path works). If you
# MAGIC prefer, generate locally and upload instead:
# MAGIC `databricks fs cp -r data/output/landing dbfs:/Volumes/smbc_workshop/raw/landing` (same for `facilitator`).

# COMMAND ----------

import os
import sys

if dbutils.widgets.get("generate_data") == "yes":
    sys.path.insert(0, os.path.abspath("../data"))
    import generate_data

    generate_data.main(["--out", f"/Volumes/{catalog}/raw"])
    for folder in sorted(os.listdir(f"/Volumes/{catalog}/raw/landing")):
        print(folder, os.listdir(f"/Volumes/{catalog}/raw/landing/{folder}"))

# COMMAND ----------

# MAGIC %md ## Grants

# COMMAND ----------

failed_grants = []


def grant(statement):
    try:
        spark.sql(statement)
        print("OK  ", statement)
    except Exception as err:
        failed_grants.append((statement, str(err).splitlines()[0]))
        print("FAIL", statement, "->", str(err).splitlines()[0])


grant(f"GRANT ALL PRIVILEGES ON CATALOG `{catalog}` TO `{facilitators}`")
grant(f"GRANT MANAGE ON CATALOG `{catalog}` TO `{facilitators}`")

grant(f"GRANT USE CATALOG ON CATALOG `{catalog}` TO `{attendees}`")
grant(f"GRANT USE SCHEMA ON SCHEMA `{catalog}`.raw TO `{attendees}`")
grant(f"GRANT READ VOLUME ON VOLUME `{catalog}`.raw.landing TO `{attendees}`")
grant(f"GRANT USE SCHEMA, SELECT ON SCHEMA `{catalog}`.checkpoint TO `{attendees}`")
grant(f"GRANT USE SCHEMA ON SCHEMA `{catalog}`.ops TO `{attendees}`")
grant(f"GRANT SELECT, MODIFY ON TABLE `{catalog}`.ops.checkin TO `{attendees}`")
grant(f"GRANT SELECT, MODIFY ON TABLE `{catalog}`.ops.lab_answers TO `{attendees}`")
if not emails:
    # No attendee list yet: let people create their own schema in Lab 1, step 0.
    grant(f"GRANT CREATE SCHEMA ON CATALOG `{catalog}` TO `{attendees}`")

# COMMAND ----------

# MAGIC %md ## One schema per attendee

# COMMAND ----------

import re


def schema_for(email):
    return re.sub(r"[^a-z0-9_]", "_", email.split("@")[0].lower())


for email in emails:
    schema = schema_for(email)
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{catalog}`.`{schema}` COMMENT 'Lab workspace for {email}'")
    grant(f"GRANT ALL PRIVILEGES ON SCHEMA `{catalog}`.`{schema}` TO `{email}`")

display(spark.createDataFrame([(e, f"{catalog}.{schema_for(e)}") for e in emails] or [("(none)", "")],
                              "email string, schema string"))

if failed_grants:
    raise RuntimeError(
        f"{len(failed_grants)} grant(s) failed, starting with: {failed_grants[0][1]}\n"
        "Most often the group doesn't exist at account level. Unity Catalog can only grant to account-level groups "
        "(created in the account console or synced from Entra ID) that are assigned to this workspace; groups created "
        "inside the workspace are workspace-local and can't receive Unity Catalog privileges. Fix the groups, then re-run "
        "this notebook (it's safe to re-run).")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Next steps
# MAGIC
# MAGIC `00_master_setup` runs all of these for you. To run the notebooks one at a time instead:
# MAGIC 1. Run **`02_build_checkpoints`** to build the save-point tables, then **`03_validate_checkpoints`**: every
# MAGIC    check should pass.
# MAGIC 2. Run **`05_governance_demo`**, then **`06_deploy_dashboards_and_agents`**. It creates the **SMBC Workshop**
# MAGIC    warehouse, the dashboards (including the progress board) and the Genie Agents, and shares them.
# MAGIC 3. Run **`07_check_requirements`**: every row should say PASS.
# MAGIC 4. Create one test user with **Consumer access** only, for the Genie One demo, and work through the smoke tests
# MAGIC    in the workshop guide (section 3.8) as a test attendee, on an SMBC laptop.
