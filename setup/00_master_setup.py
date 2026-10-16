# Databricks notebook source
# MAGIC %md
# MAGIC # 00 · Master setup: create everything the workshop needs
# MAGIC
# MAGIC Run this one notebook to build the whole workshop environment in this workspace. It checks the prerequisites,
# MAGIC then runs the other setup notebooks in order with the settings at the top, and stops at the first problem with a
# MAGIC message saying what to fix. It's safe to re-run: every step updates what already exists. It takes about 15 minutes.
# MAGIC
# MAGIC **Before you start** (section 3 of the workshop guide has the details):
# MAGIC 1. The SAG team has turned on **partner-powered AI features** and allowed **cross-Geo processing** for this workspace.
# MAGIC 2. The attendee and facilitator groups exist as **account-level** groups (created in the account console or synced
# MAGIC    from Entra ID) and are assigned to this workspace. Workspace-local groups don't work with Unity Catalog.
# MAGIC 3. You can create a catalog in the metastore, and you're a **workspace admin** (needed to create the SQL warehouse).
# MAGIC 4. This repository is imported as a **Git folder**, and you're running this notebook from its `setup` folder.
# MAGIC 5. The notebook is attached to **Serverless** compute.
# MAGIC
# MAGIC Fill in the settings at the top, then click **Run all**.
# MAGIC
# MAGIC | Step | Notebook | What it creates |
# MAGIC |---|---|---|
# MAGIC | 1 | `01_setup_workspace` | Catalog `smbc_workshop` with its schemas, volumes and ops tables; one schema per attendee; grants; the synthetic data |
# MAGIC | 2 | `02_build_checkpoints` | The save-point tables (the Lab 1 reference solution) |
# MAGIC | 3 | `03_validate_checkpoints` | Nothing: checks the save-point tables against the answer key |
# MAGIC | 4 | `05_governance_demo` | The row-filtered, column-masked copy of the facility table |
# MAGIC | 5 | `06_deploy_dashboards_and_agents` | The **SMBC Workshop** SQL warehouse, two dashboards, two Genie Agents and the lab workbook, shared with both groups |
# MAGIC | 6 | `07_check_requirements` | Nothing: automated checks of the requirements, including a live question to a Genie Agent |

# COMMAND ----------

dbutils.widgets.text("attendee_group", "smbc_workshop_attendees", "1. Attendee group (account-level)")
dbutils.widgets.text("facilitator_group", "smbc_workshop_facilitators", "2. Facilitator group (account-level)")
dbutils.widgets.text("attendee_emails", "", "3. Attendee emails, comma-separated (optional)")
dbutils.widgets.text("managed_location", "", "4. Managed location (only if CREATE CATALOG asks for one)")
dbutils.widgets.text("warehouse_name", "SMBC Workshop", "5. SQL warehouse name")
dbutils.widgets.text("folder", "", "6. Folder for dashboards and agents (blank: <your home folder>/SMBC Workshop)")
dbutils.widgets.dropdown("generate_data", "yes", ["yes", "no"], "7. Generate the synthetic data")

import json
import os
import sys
import time

from databricks.sdk import WorkspaceClient

sys.path.insert(0, os.path.abspath("tools"))
import workspace_api
from workspace_api import api

w = WorkspaceClient()
workspace_api.use_client(w)
settings = {name: dbutils.widgets.get(name).strip() for name in
            ("attendee_group", "facilitator_group", "attendee_emails", "managed_location", "warehouse_name", "folder",
             "generate_data")}
attendees, facilitators = settings["attendee_group"], settings["facilitator_group"]

# COMMAND ----------

# MAGIC %md ## Pre-flight checks
# MAGIC
# MAGIC These catch the problems that would otherwise fail halfway through.

# COMMAND ----------

problems = []
try:
    print("Unity Catalog metastore:", spark.sql("SELECT current_metastore()").first()[0])
except Exception:
    problems.append("No Unity Catalog metastore is attached to this workspace (guide 3.1, item 1).")

for group in (attendees, facilitators):
    found = api("get", "/api/2.0/preview/scim/v2/Groups",
                {"filter": f'displayName eq "{group}"', "attributes": "displayName,meta"}).get("Resources", [])
    if not found:
        problems.append(f"Group '{group}' isn't in this workspace. Create it at account level (or sync it from Entra ID) "
                        "and assign it to this workspace (guide 3.5).")
    elif found[0].get("meta", {}).get("resourceType") != "Group":
        problems.append(f"Group '{group}' is workspace-local, and Unity Catalog can only grant privileges to account-level "
                        "groups. Create it in the account console or sync it from Entra ID (guide 3.5).")

me = api("get", "/api/2.0/preview/scim/v2/Me")
is_admin = any(g.get("display") == "admins" for g in me.get("groups", []))
warehouses = [wh["name"] for wh in api("get", "/api/2.0/sql/warehouses").get("warehouses", [])]
if settings["warehouse_name"] not in warehouses and not is_admin:
    problems.append(f"There's no SQL warehouse called '{settings['warehouse_name']}', and only a workspace admin can create "
                    "one. Run this notebook as a workspace admin, or ask one to create the warehouse first (guide 3.4).")

for path in ("../data/generate_data.py", "tools/dashboards.py", "tools/genie_agents.py"):
    if not os.path.exists(path):
        problems.append(f"Can't find {path}. Import the whole repository as a Git folder and run this notebook from its "
                        "setup folder.")

if problems:
    raise RuntimeError("Fix these first, then run this notebook again:\n- " + "\n- ".join(problems))
print(f"Pre-flight checks passed. Running as {me.get('userName')}{' (workspace admin)' if is_admin else ''}.")

# COMMAND ----------

# MAGIC %md ## Run the setup notebooks
# MAGIC
# MAGIC Each step prints a link to its own run. If a step fails, open that run for the full error.

# COMMAND ----------

groups = {"attendee_group": attendees, "facilitator_group": facilitators}
place = {"folder": settings["folder"], "warehouse_name": settings["warehouse_name"]}
steps = [
    ("01_setup_workspace", "Catalog, schemas, volumes and grants; the synthetic data",
     {"catalog": "smbc_workshop", "managed_location": settings["managed_location"], "attendee_emails": settings["attendee_emails"],
      "generate_data": settings["generate_data"], "remove_after": "", **groups}),
    ("02_build_checkpoints", "Save-point tables (the Lab 1 reference solution)", {}),
    ("03_validate_checkpoints", "Save-point tables checked against the answer key", {"catalog": "smbc_workshop"}),
    ("05_governance_demo", "Row filter and column mask for the governance demo", groups),
    ("06_deploy_dashboards_and_agents", "SQL warehouse, dashboards, Genie Agents and lab workbook",
     {**place, "create_warehouse": "yes", **groups}),
    ("07_check_requirements", "Requirement checks, including a live Genie Agent question",
     {**place, "ask_genie": "yes", "raise_on_failure": "no", **groups}),
]

outputs, done = {}, []
for notebook, purpose, args in steps:
    print(f"Running {notebook}: {purpose}")
    started = time.time()
    try:
        outputs[notebook] = dbutils.notebook.run(f"./{notebook}", 3600, args) or "{}"
    except Exception as err:
        first_line = (str(err).strip().splitlines() or [type(err).__name__])[0][:600]
        raise RuntimeError(f"{notebook} failed: {first_line}\nOpen its run (linked above) for the full error, fix the cause, "
                           "then run this notebook again: every step is safe to re-run.") from None
    done.append((notebook, purpose, f"{time.time() - started:.0f} s"))
    print(f"  done in {time.time() - started:.0f} s")

# COMMAND ----------

# MAGIC %md ## Results

# COMMAND ----------

display(spark.createDataFrame(done, "notebook string, result string, took string"))

links = json.loads(outputs["06_deploy_dashboards_and_agents"]).get("links", [])
display(spark.createDataFrame([tuple(link) for link in links], "type string, name string, link string"))

checks = json.loads(outputs["07_check_requirements"]).get("results", [])
display(spark.createDataFrame([tuple(c) for c in checks], "item string, check string, status string, detail string, fix string"))
failed = [c for c in checks if c[2] == "FAIL"]
if failed:
    raise RuntimeError(f"Setup finished, but {len(failed)} requirement check(s) failed: "
                       + "; ".join(f"{c[1]} ({c[4]})" for c in failed))
print(f"Setup complete: {len(checks)} requirement checks, none failed.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## What's left (by hand)
# MAGIC
# MAGIC 1. **Genie One homepage** (workspace admin): add the welcome message and pin the reference dashboard and the
# MAGIC    reference Genie Agent (guide 3.3). This is done in the UI.
# MAGIC 2. **Business-user demo account:** one user with **Consumer access** only (guide 3.5).
# MAGIC 3. **Smoke tests** (guide 3.8) as a test attendee, on an SMBC laptop, on the SMBC network. They cover what this
# MAGIC    notebook can't: sign-in and network, Lakeflow Designer and its Genie Code prompts, Excel drag-and-drop, Genie
# MAGIC    Code in notebooks, agent mode and Genie One.
# MAGIC 4. **Late registrations:** add their emails to setting 3 and run this notebook again, with setting 7 set to `no`.
# MAGIC 5. **Before the workshop starts:** run `08_reset_or_teardown` → `reset_progress` so the progress board starts at zero.
