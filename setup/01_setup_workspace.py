# Databricks notebook source
# MAGIC %md
# MAGIC # 01 · Set up the workshop workspace
# MAGIC
# MAGIC Run once on serverless compute, as someone who can create the `smbc_workshop` catalog (or who already has
# MAGIC `ALL PRIVILEGES` and `MANAGE` on it). It is safe to re-run.
# MAGIC
# MAGIC It creates:
# MAGIC
# MAGIC | Object | Purpose | What attendees need |
# MAGIC |---|---|---|
# MAGIC | `smbc_workshop.raw.landing` (volume) | The raw extracts and the limits spreadsheet | Read |
# MAGIC | `smbc_workshop.raw.facilitator` (volume) | Answer key and a CSV copy of the limits | Nothing |
# MAGIC | `smbc_workshop.checkpoint` (schema) | Save-point tables built by `02_build_checkpoints` | Read |
# MAGIC | `smbc_workshop.ops` (schema) | Check-in and lab-answer tables for the progress board | Read and write |
# MAGIC
# MAGIC No groups are needed, and this notebook grants attendees nothing: an admin gives them access to the catalog (the
# MAGIC statements are below, and in guide 3.6). Each attendee creates their own Lab 1 schema, named after their email
# MAGIC address, when they run the check-in block. The facilitators (you, plus anyone in `facilitator_emails`) get
# MAGIC `ALL PRIVILEGES` and `MANAGE` on the catalog, so the progress board can see every attendee's schema.

# COMMAND ----------

dbutils.widgets.text("catalog", "smbc_workshop", "Catalog")
dbutils.widgets.text("managed_location", "", "Managed location (only if CREATE CATALOG asks for one)")
dbutils.widgets.text("facilitator_emails", "", "Other facilitators' emails, comma-separated (you're included)")
dbutils.widgets.dropdown("generate_data", "yes", ["yes", "no"], "Generate data into the landing volume")
dbutils.widgets.text("remove_after", "", "RemoveAfter tag, YYYYMMDD (Databricks FE workspaces only)")

catalog = dbutils.widgets.get("catalog").strip()
remove_after = dbutils.widgets.get("remove_after").strip()
managed_location = dbutils.widgets.get("managed_location").strip()
me = spark.sql("SELECT current_user()").first()[0]
facilitators = []
for email in [me] + dbutils.widgets.get("facilitator_emails").split(","):
    if email.strip() and email.strip().lower() not in {f.lower() for f in facilitators}:
        facilitators.append(email.strip())

if catalog != "smbc_workshop":
    print(f"Note: 02_build_checkpoints.sql and 04/05 use 'smbc_workshop'. Find-and-replace it with '{catalog}'.")

# COMMAND ----------

# MAGIC %md ## Catalog, schemas, volumes, ops tables

# COMMAND ----------

# Only create the catalog if it's missing: on a metastore without root storage, even CREATE CATALOG IF NOT EXISTS
# fails without a managed location, although the catalog is already there.
if spark.sql(f"SHOW CATALOGS LIKE '{catalog}'").count():
    print(f"Catalog {catalog} already exists")
else:
    location = f" MANAGED LOCATION '{managed_location}'" if managed_location else ""
    spark.sql(f"CREATE CATALOG `{catalog}`{location} "
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

# MAGIC %md ## Facilitator access
# MAGIC
# MAGIC Privileges granted on the catalog apply to everything in it, including the schemas attendees create, so the
# MAGIC progress board (which runs as whoever deployed it) can see their tables, and `08_reset_or_teardown` can drop them.

# COMMAND ----------

failed_grants = []
for facilitator in facilitators:
    for privilege in ("ALL PRIVILEGES", "MANAGE"):
        statement = f"GRANT {privilege} ON CATALOG `{catalog}` TO `{facilitator}`"
        try:
            spark.sql(statement)
            print("OK  ", statement)
        except Exception as err:
            failed_grants.append(statement)
            print("FAIL", statement, "->", str(err).splitlines()[0])
if failed_grants:
    print(f"\n{len(failed_grants)} grant(s) failed. If the catalog belongs to someone else, ask its owner to run them: "
          "without them the progress board can't see attendees' schemas.")

# COMMAND ----------

# MAGIC %md ## Attendee access (for an admin)
# MAGIC
# MAGIC This notebook doesn't grant attendees anything. Whoever looks after the catalog gives them access, for example to
# MAGIC everyone in the account with `account users`, or to an existing group (guide 3.6):
# MAGIC
# MAGIC ```sql
# MAGIC GRANT USE CATALOG, USE SCHEMA, SELECT, CREATE SCHEMA ON CATALOG smbc_workshop TO `account users`;
# MAGIC GRANT READ VOLUME ON VOLUME smbc_workshop.raw.landing TO `account users`;
# MAGIC GRANT MODIFY ON SCHEMA smbc_workshop.ops TO `account users`;
# MAGIC ```
# MAGIC
# MAGIC The current grants on the catalog:

# COMMAND ----------

display(spark.sql(f"SHOW GRANTS ON CATALOG `{catalog}`"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Next steps
# MAGIC
# MAGIC `00_master_setup` runs all of these for you. To run the notebooks one at a time instead:
# MAGIC 1. Run **`02_build_checkpoints`** to build the save-point tables, then **`03_validate_checkpoints`**: every
# MAGIC    check should pass.
# MAGIC 2. Run **`05_governance_demo`**, then **`06_deploy_dashboards_and_agents`**. It creates the dashboards (including
# MAGIC    the progress board) and the Genie Agents on a SQL warehouse you can use, and shares them.
# MAGIC 3. Run **`07_check_requirements`**: every row should say PASS.
# MAGIC 4. Create one test user with **Consumer access** only, for the Genie One demo, and work through the smoke tests
# MAGIC    in the workshop guide (section 3.8) as a test attendee, on an SMBC laptop.
