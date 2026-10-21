# Databricks notebook source
# MAGIC %md
# MAGIC # 06 · Deploy the dashboards, Genie Agents, Labs folder and daily data job
# MAGIC
# MAGIC Run as a facilitator after `01`–`03` and `05`, on serverless compute. No laptop or CLI is needed: the Databricks
# MAGIC SDK authenticates as you. It's safe to re-run; anything that already exists in the folder is updated in place.
# MAGIC
# MAGIC Everything runs on an existing SQL warehouse: the one you name, or the first pro or serverless warehouse you can use
# MAGIC (serverless and running ones first). Nothing here creates a warehouse or changes its permissions.
# MAGIC
# MAGIC | Creates or updates | `share_with` gets |
# MAGIC |---|---|
# MAGIC | Dashboard **Credit Committee: APAC exposure (reference)**, published | CAN VIEW |
# MAGIC | Dashboard **SMBC Workshop: progress board**, published | CAN VIEW |
# MAGIC | Genie Agent **Credit Risk (reference)**: the Lab 2 model answer | CAN RUN |
# MAGIC | Genie Agent **Credit Risk (secured demo)**: the governance demo from `05` | CAN RUN |
# MAGIC | Folder **Labs**: the attendee notebooks from `labs/`; attendees clone one to run it | CAN READ |
# MAGIC | Job **SMBC Workshop: daily data refresh**: regenerates the data and rebuilds the reference tables every day at 06:00 Singapore time | Nothing |
# MAGIC
# MAGIC `share_with` is `users` by default: the built-in group of everyone in this workspace, so no group has to be created.
# MAGIC The facilitators in `facilitator_emails` get CAN MANAGE. The default folder is in your home folder rather than
# MAGIC `Shared`, because every user can manage what's in `Shared`.

# COMMAND ----------

dbutils.widgets.text("folder", "", "Folder (blank: <your home folder>/SMBC Workshop)")
dbutils.widgets.text("warehouse", "", "SQL warehouse name or ID (blank: pick one you can use)")
dbutils.widgets.text("share_with", "users", "Share with (users: everyone in the workspace)")
dbutils.widgets.text("facilitator_emails", "", "Other facilitators' emails, comma-separated")

import base64
import importlib
import json
import os
import sys

from databricks.sdk import WorkspaceClient

sys.path.insert(0, os.path.abspath("tools"))
import workspace_api, dashboards, genie_agents, data_job

for module in (workspace_api, dashboards, genie_agents, data_job):  # pick up edits when re-run in the same session
    importlib.reload(module)
from workspace_api import api

w = WorkspaceClient()
workspace_api.use_client(w)
me = w.current_user.me().user_name
host = w.config.host.rstrip("/")
folder = dbutils.widgets.get("folder").strip().rstrip("/") or f"/Workspace/Users/{me}/SMBC Workshop"
share_with = dbutils.widgets.get("share_with").strip()
facilitators = [e.strip() for e in dbutils.widgets.get("facilitator_emails").split(",")
                if e.strip() and e.strip().lower() != me.lower()]
repo = os.path.dirname(os.getcwd())  # this notebook lives in <repo>/setup
api("post", "/api/2.0/workspace/mkdirs", {"path": folder})
print("Folder:", folder)

# COMMAND ----------

# MAGIC %md ## SQL warehouse

# COMMAND ----------

warehouse = workspace_api.pick_warehouse(dbutils.widgets.get("warehouse").strip())
warehouse_id, name = warehouse["id"], warehouse["name"]
print(f"Using warehouse {name} ({warehouse_id}), serverless={warehouse.get('enable_serverless_compute')}")

# COMMAND ----------

# MAGIC %md ## Dashboards
# MAGIC
# MAGIC Every dataset query runs first; nothing is deployed unless they all succeed.

# COMMAND ----------

dashboards.configure(warehouse_id, folder)
if dashboards.test():
    raise RuntimeError("A dashboard query failed (see above). Check that 02_build_bronze_silver_gold has run.")
dashboard_ids = dashboards.deploy_all()

# COMMAND ----------

# MAGIC %md ## Genie Agents

# COMMAND ----------

agents = {"Credit Risk (reference)": "reference", "Credit Risk (secured demo)": "secured"}
if not spark.catalog.tableExists("smbc_workshop.gold.facility_exposure_secured"):
    print("Skipping the secured demo agent: run 05_governance_demo first.")
    del agents["Credit Risk (secured demo)"]

agent_ids = {}
for title, variant in agents.items():
    agent_ids[title], created = genie_agents.create_or_update(title, variant, warehouse_id, folder)
    print(f"{title}: {agent_ids[title]} ({'created' if created else 'updated'})")

# COMMAND ----------

# MAGIC %md ## Labs folder
# MAGIC
# MAGIC Copies every notebook in this repo's `labs/` folder (built from the guide by `handouts/build_handouts.py`) into a
# MAGIC **Labs** folder, where attendees open them. An earlier setup's single **Lab workbook** notebook is removed.

# COMMAND ----------

labs_folder, labs_id, lab_names = f"{folder}/Labs", None, []
if workspace_api.get_status(f"{repo}/labs") is None:
    print(f"Skipping the Labs folder: {repo}/labs not found.")
else:
    api("post", "/api/2.0/workspace/mkdirs", {"path": labs_folder})
    for entry in sorted(api("get", "/api/2.0/workspace/list", {"path": f"{repo}/labs"}).get("objects", []), key=lambda o: o["path"]):
        lab = os.path.splitext(entry["path"].rsplit("/", 1)[1])[0]
        if entry["object_type"] == "NOTEBOOK":
            content = api("get", "/api/2.0/workspace/export", {"path": entry["path"], "format": "SOURCE"})["content"]
        elif entry["object_type"] == "FILE" and entry["path"].endswith(".py"):  # a notebook stored as a plain file
            local = entry["path"] if entry["path"].startswith("/Workspace") else "/Workspace" + entry["path"]
            content = base64.b64encode(open(local, "rb").read()).decode()
        else:
            continue
        api("post", "/api/2.0/workspace/import", {"path": f"{labs_folder}/{lab}", "format": "SOURCE", "language": "PYTHON",
                                                  "content": content, "overwrite": True})
        lab_names.append(lab)
    labs_id = workspace_api.get_status(labs_folder)["object_id"]
    print(f"Copied {len(lab_names)} notebooks to {labs_folder}: {', '.join(lab_names)}")
if workspace_api.get_status(f"{folder}/Lab workbook"):
    api("post", "/api/2.0/workspace/delete", {"path": f"{folder}/Lab workbook"})
    print("Removed the old Lab workbook notebook")

# COMMAND ----------

# MAGIC %md ## Daily data job
# MAGIC
# MAGIC Creates or updates the job **SMBC Workshop: daily data refresh**. Every day at 06:00 Singapore time it regenerates
# MAGIC the synthetic data, then rebuilds and validates the reference tables, with the files in this Git folder
# MAGIC (`tools/data_job.py` has the details). The data is seeded, so every run writes the same files and tables. You get an
# MAGIC email if a run fails. The workshop doesn't depend on the job, so if it can't be created, the rest carries on and `07`
# MAGIC flags it.

# COMMAND ----------

try:
    job_id, created = data_job.create_or_update(repo, notify=[me])
    print(f"{data_job.NAME}: job {job_id} ({'created' if created else 'updated'}), runs {data_job.WHEN}")
except workspace_api.ApiError as err:
    job_id = None
    print(f"Couldn't create the daily data job: {str(err).splitlines()[0][:300]}")

# COMMAND ----------

# MAGIC %md ## Permissions

# COMMAND ----------

failed_shares = []


def share(object_type, object_id, principal, level, what):
    try:
        workspace_api.share(object_type, object_id, principal, level)
        print(f"OK   {what}: {principal} {level}")
    except workspace_api.ApiError as err:
        failed_shares.append((what, principal, str(err).splitlines()[0]))
        print(f"FAIL {what}: {principal} {level} -> {str(err).splitlines()[0][:300]}")


objects = [("dashboards", i, "CAN_READ", title) for title, i in dashboard_ids.items()]
objects += [("genie", i, "CAN_RUN", title) for title, i in agent_ids.items()]
if labs_id:
    objects.append(("directories", labs_id, "CAN_READ", "Labs folder"))
if job_id:
    objects.append(("jobs", job_id, None, data_job.NAME))  # facilitators only
for object_type, object_id, level, what in objects:
    if share_with and level:
        share(object_type, object_id, share_with, level, what)
    for facilitator in facilitators:
        share(object_type, object_id, facilitator, "CAN_MANAGE", what)

# COMMAND ----------

# MAGIC %md ## Links

# COMMAND ----------

links = [("Warehouse", name, f"{host}/sql/warehouses/{warehouse_id}")]
links += [("Dashboard", title, f"{host}/dashboardsv3/{i}/published") for title, i in dashboard_ids.items()]
links += [("Genie Agent", title, f"{host}/genie/rooms/{i}") for title, i in agent_ids.items()]
if labs_id:
    links.append(("Folder", "Labs (the attendee notebooks)", f"{host}/browse/folders/{labs_id}"))
if job_id:
    links.append(("Job", data_job.NAME, f"{host}/jobs/{job_id}"))
links.append(("Genie One", "What a business user sees", f"{host}/one"))
display(spark.createDataFrame(links, "type string, name string, link string"))

if failed_shares:
    raise RuntimeError(
        f"{len(failed_shares)} permission(s) failed, starting with {failed_shares[0][0]} for {failed_shares[0][1]}: "
        f"{failed_shares[0][2]}\nCheck the share_with and facilitator_emails settings, then re-run this notebook (it's "
        "safe to re-run).")
dbutils.notebook.exit(json.dumps({"links": links}))  # read by 00_master_setup

# COMMAND ----------

# MAGIC %md
# MAGIC ## Next steps
# MAGIC
# MAGIC 1. In **Genie One** (`/one`), as a workspace admin, pin the reference dashboard and the reference Genie Agent to
# MAGIC    the homepage, and add a welcome message (guide section 3.3).
# MAGIC 2. Run **`07_check_requirements`**: every row should say PASS.
# MAGIC 3. Work through the smoke tests in the guide (section 3.8) as a test attendee, on an SMBC laptop.
