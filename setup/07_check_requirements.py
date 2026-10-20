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
dbutils.widgets.text("warehouse", "", "SQL warehouse name or ID (blank: the one the dashboards use)")
dbutils.widgets.text("share_with", "users", "Who 06 shared with (users: everyone in the workspace)")
dbutils.widgets.text("facilitator_emails", "", "Other facilitators' emails, comma-separated")
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
share_with = dbutils.widgets.get("share_with").strip()
facilitators = {me.lower()} | {e.strip().lower() for e in dbutils.widgets.get("facilitator_emails").split(",") if e.strip()}
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

# COMMAND ----------

# MAGIC %md ## Platform, identity and Unity Catalog

# COMMAND ----------

@check("1", "Unity Catalog metastore", "Attach a Unity Catalog metastore to the workspace (account console).")
def _():
    return "PASS", f"metastore {spark.sql('SELECT current_metastore()').first()[0]}"


@check("7", "Workspace entitlements", "Give workspace users Workspace access and Databricks SQL access (guide 3.5).")
def _():
    needed = {"workspace-access", "databricks-sql-access"}
    found = api("get", "/api/2.0/preview/scim/v2/Groups",
                {"filter": 'displayName eq "users"', "attributes": "displayName,entitlements"}).get("Resources", [])
    have = {e["value"] for e in (found[0].get("entitlements", []) if found else [])}
    missing = needed - have
    if not missing:
        return "PASS", "everyone in the workspace has Workspace access and Databricks SQL access"
    return "WARN", f"not given to all workspace users: {', '.join(sorted(missing))} (check individual attendees)"


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


# What every attendee needs, as (securable, privilege). A privilege granted on a parent covers its children.
ATTENDEE_NEEDS = [
    (f"CATALOG {CATALOG}", "USE CATALOG"),
    (f"CATALOG {CATALOG}", "CREATE SCHEMA"),
    (f"SCHEMA {CATALOG}.raw", "USE SCHEMA"),
    (f"VOLUME {CATALOG}.raw.landing", "READ VOLUME"),
    (f"SCHEMA {CATALOG}.checkpoint", "USE SCHEMA"),
    (f"SCHEMA {CATALOG}.checkpoint", "SELECT"),
    (f"SCHEMA {CATALOG}.ops", "USE SCHEMA"),
    (f"TABLE {CATALOG}.ops.checkin", "MODIFY"),
    (f"TABLE {CATALOG}.ops.lab_answers", "MODIFY"),
]


def chain(securable):
    """The securable and its parents: TABLE c.s.t -> SCHEMA c.s -> CATALOG c."""
    parts = securable.split(" ", 1)[1].split(".")
    return [securable] + ([f"SCHEMA {'.'.join(parts[:2])}"] if len(parts) == 3 else []) + ([f"CATALOG {parts[0]}"] if len(parts) > 1 else [])


@check("9", "Attendee access", "An admin grants attendees access to smbc_workshop: the three GRANT statements in guide 3.6.")
def _():
    held = {}  # principal -> {(securable, privilege)}
    for securable in sorted({s for need, _ in ATTENDEE_NEEDS for s in chain(need)}):
        for row in spark.sql(f"SHOW GRANTS ON {securable}").collect():
            if row["Principal"].lower() not in facilitators:
                held.setdefault(row["Principal"], set()).add((securable, row["ActionType"]))
    gaps = {p: [f"{priv} on {need.split(' ', 1)[1]}" for need, priv in ATTENDEE_NEEDS
                if not any({(s, priv), (s, "ALL PRIVILEGES")} & grants for s in chain(need))] for p, grants in held.items()}
    ready = sorted(p for p, missing in gaps.items() if not missing)
    if ready:
        return "PASS", f"{', '.join(ready)} can do everything the labs need"
    if not gaps:
        return "WARN", "only the facilitators have access to smbc_workshop so far"
    closest = min(gaps, key=lambda p: len(gaps[p]))
    return "WARN", f"nobody else has everything yet; {closest} is missing {'; '.join(gaps[closest])}"

# COMMAND ----------

# MAGIC %md ## Compute, dashboards and Genie

# COMMAND ----------

reference_status = workspace_api.get_status(f"{folder}/{dashboards.REFERENCE_NAME}.lvdash.json")
wanted = dbutils.widgets.get("warehouse").strip()
if not wanted and reference_status:
    wanted = api("get", f"/api/2.0/lakeview/dashboards/{reference_status['resource_id']}").get("warehouse_id", "")


@check("3", "SQL warehouse", "Pick a pro or serverless warehouse that you and the attendees can use, and re-run 06 with it (guide 3.4).")
def _():
    warehouse = workspace_api.pick_warehouse(wanted)
    if not (warehouse.get("enable_serverless_compute") or warehouse.get("warehouse_type") == "PRO"):
        return "FAIL", f"{warehouse['name']} is a classic warehouse: Genie Agents need pro or serverless"
    detail = f"{warehouse['name']}: {'serverless' if warehouse.get('enable_serverless_compute') else 'pro'}, {warehouse['cluster_size']}"
    try:
        attendee_levels = levels("warehouses", warehouse["id"], share_with) if share_with else None
    except workspace_api.ApiError:
        return "PASS", f"{detail}; you can't see its permissions, so check that attendees have CAN USE"
    if attendee_levels is not None and not attendee_levels & {"CAN_USE", "CAN_MONITOR", "CAN_MANAGE"}:
        return "WARN", f"{detail}; {share_with} lacks CAN USE"
    return "PASS", f"{detail}; attendees can use it" if share_with else detail


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
        if share_with and not levels("dashboards", status["resource_id"], share_with) & {"CAN_READ", "CAN_RUN", "CAN_EDIT", "CAN_MANAGE"}:
            notes.append(f"{share_with} can't view '{title}'")
    return ("FAIL" if notes else "PASS"), "; ".join(notes) or "both published; attendees can view"


reference_agent = genie_agents.find("Credit Risk (reference)", folder)
secured_agent = genie_agents.find("Credit Risk (secured demo)", folder)


@check("4", "Genie Agents shared", "Run 06_deploy_dashboards_and_agents.")
def _():
    notes = []
    for title, space_id in (("Credit Risk (reference)", reference_agent), ("Credit Risk (secured demo)", secured_agent)):
        if space_id is None:
            notes.append(f"'{title}' not found in {folder}")
        elif share_with and not levels("genie", space_id, share_with) & {"CAN_READ", "CAN_RUN", "CAN_EDIT", "CAN_MANAGE"}:
            notes.append(f"{share_with} can't use '{title}'")
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


@check("—", "Governance demo (05)", "Run 05_governance_demo again: whoever runs it is always a facilitator.")
def _():
    branches = spark.sql(f"SELECT count(DISTINCT booking_branch) FROM {CATALOG}.checkpoint.gold_facility_exposure_secured").first()[0]
    if branches == 12:
        return "PASS", "as a facilitator you see all 12 branches; attendees see SIN only"
    return "WARN", f"you see {branches} branch(es): you're not on the facilitator list, so the demo would show the attendee view"

# COMMAND ----------

summary = spark.createDataFrame(results, "item string, check string, status string, detail string, fix string")
display(summary)
failed = [r for r in results if r[2] == "FAIL"]
if dbutils.widgets.get("raise_on_failure") == "yes":  # 00_master_setup sets "no" and reports failures itself
    assert not failed, f"{len(failed)} check(s) failed: " + "; ".join(r[1] for r in failed)
dbutils.notebook.exit(json.dumps({"results": results}))
