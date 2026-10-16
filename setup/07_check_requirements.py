# Databricks notebook source
# MAGIC %md
# MAGIC # 07 · Check the workshop requirements
# MAGIC
# MAGIC Run as a facilitator after `01`–`06`, on serverless compute. It automates the checks from section 3 of the guide
# MAGIC that don't need a person at an SMBC laptop, and prints one row per check, numbered as in the checklist (3.1).
# MAGIC Every row should say **PASS**. **WARN** needs a decision; **FAIL** needs a fix.
# MAGIC
# MAGIC The smoke tests in section 3.8 cover what this can't: sign-in and the venue network, Designer and its Genie Code
# MAGIC prompts, Excel drag-and-drop, Genie Code in notebooks, agent mode, Genie One and the Consumer-access user.

# COMMAND ----------

dbutils.widgets.text("folder", "", "Folder used by 06 (blank: <your home folder>/SMBC Workshop)")
dbutils.widgets.text("warehouse_name", "SMBC Workshop", "SQL warehouse name")
dbutils.widgets.text("attendee_group", "smbc_workshop_attendees", "Attendee group")
dbutils.widgets.text("facilitator_group", "smbc_workshop_facilitators", "Facilitator group")
dbutils.widgets.dropdown("ask_genie", "yes", ["yes", "no"], "Ask the reference Genie Agent a question (about 30 s)")
dbutils.widgets.dropdown("raise_on_failure", "yes", ["yes", "no"], "Fail the run if a check fails")

import importlib
import json
import os
import sys

from databricks.sdk import WorkspaceClient

sys.path.insert(0, os.path.abspath("tools"))
import workspace_api, dashboards, genie_agents

for module in (workspace_api, dashboards, genie_agents):
    importlib.reload(module)
from workspace_api import api

w = WorkspaceClient()
workspace_api.use_client(w)
me = w.current_user.me().user_name
folder = dbutils.widgets.get("folder").strip().rstrip("/") or f"/Workspace/Users/{me}/SMBC Workshop"
attendees = dbutils.widgets.get("attendee_group").strip()
facilitators = dbutils.widgets.get("facilitator_group").strip()
warehouse_name = dbutils.widgets.get("warehouse_name").strip()
CATALOG = "smbc_workshop"
results = []


def check(item, name, fix=""):
    """Run one check. The function returns (status, detail); an exception counts as FAIL."""
    def run(fn):
        try:
            status, detail = fn()
        except Exception as err:
            status, detail = "FAIL", str(err).splitlines()[0][:400]
        results.append((item, name, status, detail, "" if status == "PASS" else fix))
        print(f"{status:<5} {item:<3} {name}: {detail}")
    return run


def levels(object_type, object_id, principal):
    """Permission levels a principal holds on a workspace object, direct or inherited."""
    acl = api("get", f"/api/2.0/permissions/{object_type}/{object_id}").get("access_control_list", [])
    return {p["permission_level"] for e in acl if principal in (e.get("group_name"), e.get("user_name"), e.get("service_principal_name"))
            for p in e.get("all_permissions", [])}


def scim_group(name):
    found = api("get", "/api/2.0/preview/scim/v2/Groups",
                {"filter": f'displayName eq "{name}"', "attributes": "displayName,meta,entitlements"}).get("Resources", [])
    return found[0] if found else None

# COMMAND ----------

# MAGIC %md ## Platform, identity and Unity Catalog

# COMMAND ----------

@check("1", "Unity Catalog metastore", "Attach a Unity Catalog metastore to the workspace (account console).")
def _():
    return "PASS", f"metastore {spark.sql('SELECT current_metastore()').first()[0]}"


@check("7", "Groups are account-level", "Create the groups in the account console (or sync them from Entra ID) and "
       "assign them to this workspace; workspace-local groups can't receive Unity Catalog privileges (guide 3.5).")
def _():
    kinds = {}
    for g in (attendees, facilitators):
        group = scim_group(g)
        kinds[g] = "missing" if group is None else group.get("meta", {}).get("resourceType")
    bad = {g: k for g, k in kinds.items() if k != "Group"}
    return ("FAIL" if bad else "PASS"), ", ".join(f"{g}: {'account-level' if k == 'Group' else k}" for g, k in kinds.items())


@check("7", "Attendee entitlements", "Give the attendee group Workspace access and Databricks SQL access (guide 3.5).")
def _():
    needed = {"workspace-access", "databricks-sql-access"}
    group = scim_group(attendees) or {}
    everyone = scim_group("users") or {}
    have = {e["value"] for e in group.get("entitlements", []) + everyone.get("entitlements", [])}
    missing = needed - have
    if not missing:
        return "PASS", "Workspace access and Databricks SQL access"
    return "WARN", f"not granted to {attendees} or to all users: {', '.join(sorted(missing))} (check individual users)"


@check("9", "Catalog, schemas and volumes", "Run 01_setup_workspace.")
def _():
    schemas = {r[0] for r in spark.sql(f"SHOW SCHEMAS IN {CATALOG}").collect()}
    missing = {"raw", "checkpoint", "ops"} - schemas
    folders = sorted(os.listdir(f"/Volumes/{CATALOG}/raw/landing"))
    expected = ["counterparties", "facilities", "fx_rates", "group_limits", "monthly_balances", "sector_emission_factors"]
    if missing or folders != expected:
        return "FAIL", f"missing schemas {sorted(missing)}; landing folders {folders}"
    return "PASS", f"raw, checkpoint, ops; {len(folders)} landing folders"


@check("9", "Checkpoint tables", "Run 02_build_checkpoints, then 03_validate_checkpoints.")
def _():
    counts = {t: spark.table(f"{CATALOG}.checkpoint.{t}").count() for t in ("gold_group_exposure", "gold_facility_exposure")}
    expected = {"gold_group_exposure": 7174, "gold_facility_exposure": 74283}
    return ("PASS" if counts == expected else "FAIL"), ", ".join(f"{t} {n:,} rows" for t, n in counts.items())


@check("9", "Attendee grants", "Re-run 01_setup_workspace with the right attendee group.")
def _():
    expected = [
        ("CATALOG", CATALOG, "USE CATALOG"),
        ("SCHEMA", f"{CATALOG}.raw", "USE SCHEMA"),
        ("VOLUME", f"{CATALOG}.raw.landing", "READ VOLUME"),
        ("SCHEMA", f"{CATALOG}.checkpoint", "USE SCHEMA"),
        ("SCHEMA", f"{CATALOG}.checkpoint", "SELECT"),
        ("SCHEMA", f"{CATALOG}.ops", "USE SCHEMA"),
        ("TABLE", f"{CATALOG}.ops.checkin", "MODIFY"),
        ("TABLE", f"{CATALOG}.ops.lab_answers", "MODIFY"),
    ]
    missing = []
    for kind, obj, privilege in expected:
        rows = spark.sql(f"SHOW GRANTS `{attendees}` ON {kind} {obj}").collect()
        if not any(r["ActionType"] in (privilege, "ALL PRIVILEGES") for r in rows):
            missing.append(f"{privilege} on {obj}")
    return ("FAIL" if missing else "PASS"), ("missing " + "; ".join(missing)) if missing else f"{len(expected)} grants to {attendees}"


@check("9", "Attendee schemas", "Add attendee emails to 01_setup_workspace and re-run it, or leave CREATE SCHEMA to attendees.")
def _():
    system = {"information_schema", "default", "raw", "checkpoint", "ops"}
    personal = [r[0] for r in spark.sql(f"SHOW SCHEMAS IN {CATALOG}").collect() if r[0] not in system]
    if personal:
        return "PASS", f"{len(personal)} attendee schema(s), e.g. {personal[0]}"
    rows = spark.sql(f"SHOW GRANTS `{attendees}` ON CATALOG {CATALOG}").collect()
    if any(r["ActionType"] == "CREATE SCHEMA" for r in rows):
        return "WARN", "none yet; attendees can create their own (Lab 1, step 0)"
    return "FAIL", "no attendee schemas, and attendees can't create them"

# COMMAND ----------

# MAGIC %md ## Compute, dashboards and Genie

# COMMAND ----------

warehouse = next((wh for wh in api("get", "/api/2.0/sql/warehouses").get("warehouses", []) if wh["name"] == warehouse_name), None)


@check("3", "SQL warehouse", f"Run 06_deploy_dashboards_and_agents, or create '{warehouse_name}' and give attendees CAN USE (guide 3.4).")
def _():
    if warehouse is None:
        return "FAIL", f"no warehouse called '{warehouse_name}'"
    problems = []
    if not warehouse.get("enable_serverless_compute"):
        problems.append("not serverless")
    if not levels("warehouses", warehouse["id"], attendees) & {"CAN_USE", "CAN_MONITOR", "CAN_MANAGE"}:
        problems.append(f"{attendees} lacks CAN USE")
    detail = f"{warehouse['cluster_size']}, {warehouse['min_num_clusters']}-{warehouse['max_num_clusters']} clusters, auto-stop {warehouse['auto_stop_mins']} min"
    return ("FAIL" if problems else "PASS"), "; ".join(problems) or detail


@check("6", "Excel reader (Designer drag-and-drop is smoke test 5)", "Check the workspace Previews page for Excel file support.")
def _():
    n = spark.sql(f"SELECT count(*) FROM read_files('/Volumes/{CATALOG}/raw/landing/group_limits/', format => 'excel', headerRows => 1)").first()[0]
    return ("PASS" if n == 420 else "WARN"), f"{n} rows read from group_limits.xlsx (expected 420)"


@check("3", "Dashboards published and shared", "Run 06_deploy_dashboards_and_agents.")
def _():
    notes = []
    for title in (dashboards.REFERENCE_NAME, dashboards.PROGRESS_NAME):
        status = workspace_api.get_status(f"{folder}/{title}.lvdash.json")
        if status is None:
            notes.append(f"'{title}' not found in {folder}")
            continue
        api("get", f"/api/2.0/lakeview/dashboards/{status['resource_id']}/published")  # fails if it was never published
        if not levels("dashboards", status["resource_id"], attendees) & {"CAN_READ", "CAN_RUN", "CAN_EDIT", "CAN_MANAGE"}:
            notes.append(f"{attendees} can't view '{title}'")
    return ("FAIL" if notes else "PASS"), "; ".join(notes) or "both published; attendees can view"


reference_agent = genie_agents.find("Credit Risk (reference)", folder)
secured_agent = genie_agents.find("Credit Risk (secured demo)", folder)


@check("4", "Genie Agents shared", "Run 06_deploy_dashboards_and_agents.")
def _():
    notes = []
    for title, space_id in (("Credit Risk (reference)", reference_agent), ("Credit Risk (secured demo)", secured_agent)):
        if space_id is None:
            notes.append(f"'{title}' not found in {folder}")
        elif not levels("genie", space_id, attendees) & {"CAN_READ", "CAN_RUN", "CAN_EDIT", "CAN_MANAGE"}:
            notes.append(f"{attendees} can't use '{title}'")
    return ("FAIL" if notes else "PASS"), "; ".join(notes) or "both agents; attendees can ask questions"


if dbutils.widgets.get("ask_genie") == "yes":
    @check("4, 5", "Genie Agent answers (partner-powered AI, cross-Geo processing)",
           "Turn on partner-powered AI features for the account and workspace, and make sure cross-Geo processing "
           "isn't enforced (guide 3.2, 3.3).")
    def _():
        if reference_agent is None:
            return "FAIL", "reference agent not found"
        answer = genie_agents.ask(reference_agent, "Which groups were above 90% of their limit at the end of FY2026 H1?", show=False)
        found = "orchid" in (answer["text"] + str(answer["rows"])).lower()
        if answer["status"] == "COMPLETED" and found:
            return "PASS", f"found Orchid Group in {answer['seconds']} s"
        return "FAIL", f"status {answer['status']}: {(answer['error'] or answer['text'] or 'no Orchid in the answer')!s:.300}"


@check("—", "Governance demo (05)", f"Run 05_governance_demo, and add yourself to {facilitators} (an account-level group).")
def _():
    branches = spark.sql(f"SELECT count(DISTINCT booking_branch) FROM {CATALOG}.checkpoint.gold_facility_exposure_secured").first()[0]
    if branches == 12:
        return "PASS", "as a facilitator you see all 12 branches; attendees see SIN only"
    return "WARN", f"you see {branches} branch(es): you're not in {facilitators}, so the demo would show the attendee view"

# COMMAND ----------

summary = spark.createDataFrame(results, "item string, check string, status string, detail string, fix string")
display(summary)
failed = [r for r in results if r[2] == "FAIL"]
if dbutils.widgets.get("raise_on_failure") == "yes":  # 00_master_setup sets "no" and reports failures itself
    assert not failed, f"{len(failed)} check(s) failed: " + "; ".join(r[1] for r in failed)
dbutils.notebook.exit(json.dumps({"results": results}))
