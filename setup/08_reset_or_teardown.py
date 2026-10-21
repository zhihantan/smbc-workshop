# Databricks notebook source
# MAGIC %md
# MAGIC # 08 · Reset between runs, or tear down after the workshop
# MAGIC
# MAGIC | Action | What it does | When |
# MAGIC |---|---|---|
# MAGIC | `reset_progress` | Empties `ops.checkin` and `ops.lab_answers`, so the progress board starts at zero | Before each run |
# MAGIC | `drop_attendee_schemas` | `reset_progress`, then drops every attendee schema **and everything people built in it** | After a dry run |
# MAGIC | `teardown` | Drops the whole `smbc_workshop` catalog, deletes the dashboards, Genie Agents and Labs folder in the 06 folder, and deletes the daily data job | When the workshop environment is no longer needed |
# MAGIC
# MAGIC **`dry_run` is on by default:** the notebook only lists what it would change. Set it to `no` to make the changes.
# MAGIC None of this touches the SQL warehouse, or the dashboards and Genie Agents that attendees saved in their own folders.

# COMMAND ----------

dbutils.widgets.dropdown("action", "reset_progress", ["reset_progress", "drop_attendee_schemas", "teardown"], "Action")
dbutils.widgets.dropdown("dry_run", "yes", ["yes", "no"], "Dry run: only list what would change")
dbutils.widgets.text("folder", "", "Folder used by 06 (blank: <your home folder>/SMBC Workshop)")

import importlib
import os
import sys

from databricks.sdk import WorkspaceClient

sys.path.insert(0, os.path.abspath("tools"))
import workspace_api, dashboards, genie_agents, data_job

for module in (workspace_api, dashboards, genie_agents, data_job):
    importlib.reload(module)
from workspace_api import api

w = WorkspaceClient()
workspace_api.use_client(w)
me = w.current_user.me().user_name
folder = dbutils.widgets.get("folder").strip().rstrip("/") or f"/Workspace/Users/{me}/SMBC Workshop"
action = dbutils.widgets.get("action")
dry_run = dbutils.widgets.get("dry_run") == "yes"
CATALOG = "smbc_workshop"
SYSTEM_SCHEMAS = {"information_schema", "default", "raw", "bronze", "silver", "gold", "ops", "checkpoint"}


def do(description, fn):
    print(("WOULD " if dry_run else "") + description)
    if not dry_run:
        fn()

# COMMAND ----------

if action in ("reset_progress", "drop_attendee_schemas"):
    for table in ("checkin", "lab_answers"):
        rows = spark.table(f"{CATALOG}.ops.{table}").count()
        do(f"delete {rows} row(s) from {CATALOG}.ops.{table}", lambda t=table: spark.sql(f"DELETE FROM {CATALOG}.ops.{t}"))

if action == "drop_attendee_schemas":
    for schema in sorted(r[0] for r in spark.sql(f"SHOW SCHEMAS IN {CATALOG}").collect()):
        if schema not in SYSTEM_SCHEMAS:
            tables = spark.sql(f"SHOW TABLES IN {CATALOG}.`{schema}`").count()
            do(f"drop schema {CATALOG}.{schema} ({tables} table(s))",
               lambda s=schema: spark.sql(f"DROP SCHEMA {CATALOG}.`{s}` CASCADE"))
    print("\nAttendees get their schema back, empty, when they run the check-in block again.")

if action == "teardown":
    for title in (dashboards.REFERENCE_NAME, dashboards.PROGRESS_NAME):
        status = workspace_api.get_status(f"{folder}/{title}.lvdash.json")
        if status:
            do(f"move dashboard '{title}' to the trash",
               lambda i=status["resource_id"]: api("delete", f"/api/2.0/lakeview/dashboards/{i}"))
    for title in ("Credit Risk (reference)", "Credit Risk (secured demo)", "Credit Risk (starter)"):
        space_id = genie_agents.find(title, folder)
        if space_id:
            do(f"delete Genie Agent '{title}' ({space_id})", lambda i=space_id: api("delete", f"/api/2.0/genie/spaces/{i}"))
    for path, what in ((f"{folder}/Labs", "folder"), (f"{folder}/Lab workbook", "notebook")):  # the workbook is from an earlier setup
        if workspace_api.get_status(path):
            do(f"delete {what} {path}",
               lambda p=path: api("post", "/api/2.0/workspace/delete", {"path": p, "recursive": True}))
    job_id = data_job.find()
    if job_id:
        do(f"delete job '{data_job.NAME}' ({job_id})", lambda: api("post", "/api/2.1/jobs/delete", {"job_id": job_id}))
    do(f"drop catalog {CATALOG} and everything in it", lambda: spark.sql(f"DROP CATALOG {CATALOG} CASCADE"))
    print("\nThe SQL warehouse is left as it is.")

print("\nDry run only: set dry_run to 'no' to make these changes." if dry_run else "\nDone.")
