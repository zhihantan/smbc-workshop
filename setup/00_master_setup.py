# Databricks notebook source
# MAGIC %md
# MAGIC # 00 · Master setup: create everything the workshop needs
# MAGIC
# MAGIC Run this one notebook to build the whole workshop environment in this workspace. It checks the prerequisites,
# MAGIC then runs the other setup notebooks in order with the settings at the top, and stops at the first problem with a
# MAGIC message saying what to fix. It's safe to re-run: every step updates what already exists. It takes 5–15 minutes.
# MAGIC
# MAGIC **Before you start** (section 3 of the workshop guide has the details):
# MAGIC 1. The SAG team has turned on **partner-powered AI features** and allowed **cross-Geo processing** for this workspace.
# MAGIC 2. You can create the `smbc_workshop` catalog, or it already exists and you have `ALL PRIVILEGES` and `MANAGE` on it.
# MAGIC 3. You can use a pro or serverless **SQL warehouse**: the setup uses the one you name below, or picks one for you.
# MAGIC 4. This repository is imported as a **Git folder**, and you're running this notebook from its `setup` folder.
# MAGIC 5. The notebook is attached to **Serverless** compute.
# MAGIC
# MAGIC No groups are needed. Attendees need access to the `smbc_workshop` catalog, which an admin grants (guide 3.6);
# MAGIC the requirement checks at the end show whether they have it.
# MAGIC
# MAGIC Every setting is optional. Fill in the ones you need, then click **Run all**.
# MAGIC
# MAGIC | Step | Notebook | What it creates |
# MAGIC |---|---|---|
# MAGIC | 1 | `01_setup_workspace` | Catalog `smbc_workshop` with its schemas (`raw`, `bronze`, `silver`, `gold`, `ops`), volumes and ops tables; the synthetic data; full access for the facilitators |
# MAGIC | 2 | `02_build_bronze_silver_gold` | The bronze, silver and gold reference tables (the Lab 1 reference solution) |
# MAGIC | 3 | `03_validate_bronze_silver_gold` | Nothing: checks those tables against the answer key |
# MAGIC | 4 | `05_governance_demo` | The row-filtered, column-masked copy of the facility table |
# MAGIC | 5 | `06_deploy_dashboards_and_agents` | Two dashboards, two Genie Agents and the attendees' Labs folder, on the chosen SQL warehouse, shared with everyone in the workspace |
# MAGIC | 6 | `07_check_requirements` | Nothing: automated checks of the requirements, including a live question to a Genie Agent |

# COMMAND ----------

dbutils.widgets.text("warehouse", "", "1. SQL warehouse name or ID (blank: pick one you can use)")
dbutils.widgets.text("facilitator_emails", "", "2. Other facilitators' emails, comma-separated (you're included)")
dbutils.widgets.text("managed_location", "", "3. Managed location (only if CREATE CATALOG asks for one)")
dbutils.widgets.text("share_with", "users", "4. Share dashboards, agents and Labs with (users: everyone)")
dbutils.widgets.text("folder", "", "5. Folder for dashboards and agents (blank: <your home folder>/SMBC Workshop)")
dbutils.widgets.dropdown("generate_data", "yes", ["yes", "no"], "6. Generate the synthetic data")

import json
import os
import sys
import time

from databricks.sdk import WorkspaceClient

sys.path.insert(0, os.path.abspath("tools"))
import workspace_api

w = WorkspaceClient()
workspace_api.use_client(w)
settings = {name: dbutils.widgets.get(name).strip() for name in
            ("warehouse", "facilitator_emails", "managed_location", "share_with", "folder", "generate_data")}

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

warehouse = None
try:
    warehouse = workspace_api.pick_warehouse(settings["warehouse"])
    print(f"SQL warehouse: {warehouse['name']} ({warehouse['id']})")
except workspace_api.ApiError as err:
    problems.append(str(err))

for path in ("../data/generate_data.py", "tools/dashboards.py", "tools/genie_agents.py"):
    if not os.path.exists(path):
        problems.append(f"Can't find {path}. Import the whole repository as a Git folder and run this notebook from its "
                        "setup folder.")

if problems:
    raise RuntimeError("Fix these first, then run this notebook again:\n- " + "\n- ".join(problems))
print(f"Pre-flight checks passed. Running as {w.current_user.me().user_name}.")

# COMMAND ----------

# MAGIC %md ## Run the setup notebooks
# MAGIC
# MAGIC Each step prints a link to its own run. If a step fails, open that run for the full error.

# COMMAND ----------

facilitators = {"facilitator_emails": settings["facilitator_emails"]}
place = {"folder": settings["folder"], "warehouse": warehouse["id"], "share_with": settings["share_with"]}
steps = [
    ("01_setup_workspace", "Catalog, schemas and volumes; the synthetic data; facilitator access",
     {"catalog": "smbc_workshop", "managed_location": settings["managed_location"], "generate_data": settings["generate_data"],
      "remove_after": "", **facilitators}),
    ("02_build_bronze_silver_gold", "Bronze, silver and gold reference tables (the Lab 1 reference solution)", {}),
    ("03_validate_bronze_silver_gold", "Reference tables checked against the answer key", {"catalog": "smbc_workshop"}),
    ("05_governance_demo", "Row filter and column mask for the governance demo", facilitators),
    ("06_deploy_dashboards_and_agents", "Dashboards, Genie Agents and the Labs folder", {**place, **facilitators}),
    ("07_check_requirements", "Requirement checks, including a live Genie Agent question",
     {**place, **facilitators, "ask_genie": "yes", "raise_on_failure": "no"}),
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
warned = [c[1] for c in checks if c[2] == "WARN"]
print(f"Setup complete: {len(checks)} requirement checks, none failed"
      + (f"; {len(warned)} warning(s) to review: {', '.join(warned)}." if warned else "."))
print(f"Tell attendees to use the SQL warehouse '{warehouse['name']}'.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## What's left (by hand)
# MAGIC
# MAGIC 1. **Attendee access:** if the *Attendee access* check warned, an admin grants attendees access to `smbc_workshop`
# MAGIC    with the statements in guide 3.6. Attendees also need CAN USE on the SQL warehouse named above.
# MAGIC 2. **Genie One homepage** (workspace admin): add the welcome message and pin the reference dashboard and the
# MAGIC    reference Genie Agent (guide 3.3). This is done in the UI.
# MAGIC 3. **Business-user demo account:** one user with **Consumer access** only (guide 3.5).
# MAGIC 4. **Smoke tests** (guide 3.8) as a test attendee, on an SMBC laptop, on the SMBC network. They cover what this
# MAGIC    notebook can't: sign-in and network, Lakeflow Designer and its Genie Code prompts, Excel drag-and-drop, Genie
# MAGIC    Code in notebooks, agent mode and Genie One.
# MAGIC 5. **Before the workshop starts:** run `08_reset_or_teardown` → `reset_progress` so the progress board starts at zero.
