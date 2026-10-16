# Databricks notebook source
# MAGIC %md
# MAGIC # 06 · Deploy the dashboards, Genie Agents and lab workbook
# MAGIC
# MAGIC Run as a facilitator after `01`–`03` and `05`, on serverless compute. No laptop or CLI is needed: the Databricks
# MAGIC SDK authenticates as you. It's safe to re-run; anything that already exists in the folder is updated in place.
# MAGIC
# MAGIC | Creates or updates | Attendee access |
# MAGIC |---|---|
# MAGIC | SQL warehouse **SMBC Workshop** (only if it doesn't exist yet) | CAN USE |
# MAGIC | Dashboard **Credit Committee: APAC exposure (reference)**, published | CAN VIEW |
# MAGIC | Dashboard **SMBC Workshop: progress board**, published | CAN VIEW |
# MAGIC | Genie Agent **Credit Risk (reference)**: the Lab 2 model answer | CAN RUN |
# MAGIC | Genie Agent **Credit Risk (secured demo)**: the governance demo from `05` | CAN RUN |
# MAGIC | Notebook **Lab workbook**: a read-only copy of `handouts/Lab_Workbook_notebook` | CAN READ |
# MAGIC
# MAGIC The facilitator group gets CAN MANAGE on all of them. The default folder is in your home folder rather than
# MAGIC `Shared`, because every user can manage what's in `Shared`.

# COMMAND ----------

dbutils.widgets.text("folder", "", "Folder (blank: <your home folder>/SMBC Workshop)")
dbutils.widgets.text("warehouse_name", "SMBC Workshop", "SQL warehouse name")
dbutils.widgets.dropdown("create_warehouse", "yes", ["yes", "no"], "Create the warehouse if it doesn't exist")
dbutils.widgets.text("attendee_group", "smbc_workshop_attendees", "Attendee group")
dbutils.widgets.text("facilitator_group", "smbc_workshop_facilitators", "Facilitator group")

import base64
import importlib
import json
import os
import sys

from databricks.sdk import WorkspaceClient

sys.path.insert(0, os.path.abspath("tools"))
import workspace_api, dashboards, genie_agents

for module in (workspace_api, dashboards, genie_agents):  # pick up edits when re-run in the same session
    importlib.reload(module)
from workspace_api import api

w = WorkspaceClient()
workspace_api.use_client(w)
me = w.current_user.me().user_name
host = w.config.host.rstrip("/")
folder = dbutils.widgets.get("folder").strip().rstrip("/") or f"/Workspace/Users/{me}/SMBC Workshop"
attendees = dbutils.widgets.get("attendee_group").strip()
facilitators = dbutils.widgets.get("facilitator_group").strip()
repo = os.path.dirname(os.getcwd())  # this notebook lives in <repo>/setup
api("post", "/api/2.0/workspace/mkdirs", {"path": folder})
print("Folder:", folder)

# COMMAND ----------

# MAGIC %md ## SQL warehouse

# COMMAND ----------

name = dbutils.widgets.get("warehouse_name").strip()
found = [wh for wh in api("get", "/api/2.0/sql/warehouses").get("warehouses", []) if wh["name"] == name]
if found:
    warehouse_id = found[0]["id"]
    print(f"Using warehouse {name} ({warehouse_id}), serverless={found[0].get('enable_serverless_compute')}")
elif dbutils.widgets.get("create_warehouse") == "yes":
    # Section 3.4 of the guide: Small, 1-4 clusters, for about 40-60 people. Lengthen auto-stop on the day.
    warehouse_id = api("post", "/api/2.0/sql/warehouses", {
        "name": name, "cluster_size": "Small", "min_num_clusters": 1, "max_num_clusters": 4, "auto_stop_mins": 30,
        "enable_serverless_compute": True, "warehouse_type": "PRO"})["id"]
    print(f"Created serverless warehouse {name} ({warehouse_id})")
else:
    raise RuntimeError(f"No SQL warehouse called '{name}'. Create it (guide section 3.4) or set create_warehouse to yes.")

# COMMAND ----------

# MAGIC %md ## Dashboards
# MAGIC
# MAGIC Every dataset query runs first; nothing is deployed unless they all succeed.

# COMMAND ----------

dashboards.configure(warehouse_id, folder)
if dashboards.test():
    raise RuntimeError("A dashboard query failed (see above). Check that 02_build_checkpoints has run.")
dashboard_ids = dashboards.deploy_all()

# COMMAND ----------

# MAGIC %md ## Genie Agents

# COMMAND ----------

agents = {"Credit Risk (reference)": "reference", "Credit Risk (secured demo)": "secured"}
if not spark.catalog.tableExists("smbc_workshop.checkpoint.gold_facility_exposure_secured"):
    print("Skipping the secured demo agent: run 05_governance_demo first.")
    del agents["Credit Risk (secured demo)"]

agent_ids = {}
for title, variant in agents.items():
    agent_ids[title], created = genie_agents.create_or_update(title, variant, warehouse_id, folder)
    print(f"{title}: {agent_ids[title]} ({'created' if created else 'updated'})")

# COMMAND ----------

# MAGIC %md ## Lab workbook
# MAGIC
# MAGIC Copies `handouts/Lab_Workbook_notebook` from this repo so attendees can read the lab steps inside the workspace.
# MAGIC Run `handouts/build_handouts.py` first if the repo doesn't have it.

# COMMAND ----------

workbook_id = None
source = f"{repo}/handouts/Lab_Workbook_notebook"
status = workspace_api.get_status(source) or workspace_api.get_status(source + ".py")
if status is None:
    print(f"Skipping the lab workbook: {source} not found.")
else:
    if status["object_type"] == "NOTEBOOK":
        content = api("get", "/api/2.0/workspace/export", {"path": status["path"], "format": "SOURCE"})["content"]
    else:  # a plain .py file
        content = base64.b64encode(open(status["path"], "rb").read()).decode()
    api("post", "/api/2.0/workspace/import", {"path": f"{folder}/Lab workbook", "format": "SOURCE", "language": "PYTHON",
                                              "content": content, "overwrite": True})
    workbook_id = workspace_api.get_status(f"{folder}/Lab workbook")["object_id"]
    print("Lab workbook copied to", f"{folder}/Lab workbook")

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


share("warehouses", warehouse_id, attendees, "CAN_USE", f"Warehouse {name}")
share("warehouses", warehouse_id, facilitators, "CAN_MANAGE", f"Warehouse {name}")
for title, dashboard_id in dashboard_ids.items():
    share("dashboards", dashboard_id, attendees, "CAN_READ", title)
    share("dashboards", dashboard_id, facilitators, "CAN_MANAGE", title)
for title, space_id in agent_ids.items():
    share("genie", space_id, attendees, "CAN_RUN", title)
    share("genie", space_id, facilitators, "CAN_MANAGE", title)
if workbook_id:
    share("notebooks", workbook_id, attendees, "CAN_READ", "Lab workbook")
    share("notebooks", workbook_id, facilitators, "CAN_MANAGE", "Lab workbook")

# COMMAND ----------

# MAGIC %md ## Links

# COMMAND ----------

links = [("Warehouse", name, f"{host}/sql/warehouses/{warehouse_id}")]
links += [("Dashboard", title, f"{host}/dashboardsv3/{i}/published") for title, i in dashboard_ids.items()]
links += [("Genie Agent", title, f"{host}/genie/rooms/{i}") for title, i in agent_ids.items()]
if workbook_id:
    links.append(("Notebook", "Lab workbook", f"{host}/#notebook/{workbook_id}"))
links.append(("Genie One", "What a business user sees", f"{host}/one"))
display(spark.createDataFrame(links, "type string, name string, link string"))

if failed_shares:
    raise RuntimeError(
        f"{len(failed_shares)} permission(s) failed, starting with {failed_shares[0][0]} for {failed_shares[0][1]}: "
        f"{failed_shares[0][2]}\nCheck that the groups exist and are assigned to this workspace, then re-run this "
        "notebook (it's safe to re-run).")
dbutils.notebook.exit(json.dumps({"links": links}))  # read by 00_master_setup

# COMMAND ----------

# MAGIC %md
# MAGIC ## Next steps
# MAGIC
# MAGIC 1. In **Genie One** (`/one`), as a workspace admin, pin the reference dashboard and the reference Genie Agent to
# MAGIC    the homepage, and add a welcome message (guide section 3.3).
# MAGIC 2. Run **`07_check_requirements`**: every row should say PASS.
# MAGIC 3. Work through the smoke tests in the guide (section 3.8) as a test attendee, on an SMBC laptop.
