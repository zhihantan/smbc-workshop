#!/usr/bin/env python3
"""Create, test and share the SMBC workshop Genie Agents (Genie REST API).

Variants: `reference` (Lab 2 model answer: starter + fiscal-year instructions, example SQL, benchmarks),
`starter` (the same without the fiscal-year instruction, to rehearse the Lab 2 fiscal-year test) and `secured`
(the governance demo on gold_facility_exposure_secured).

From a laptop, through the Databricks CLI:

  genie_agents.py --profile P --parent "/Workspace/Users/<you>/SMBC Workshop" create --variant reference --title "Credit Risk (reference)"
  genie_agents.py --profile P --parent ... create --variant secured --title "Credit Risk (secured demo)"
  genie_agents.py --profile P ask SPACE_ID "Which groups were above 90% of their limit at the end of FY2026 H1?"
  genie_agents.py --profile P share SPACE_ID users CAN_RUN                       # group, user email or service principal ID
  genie_agents.py --profile P --warehouse W patch SPACE_ID --variant reference --title "Credit Risk (reference)"
  genie_agents.py build --variant reference                                      # print serialized_space only

`create` and `patch` use the SQL warehouse in `--warehouse` (a name or ID), or the first pro or serverless warehouse you
can use. `create` updates the agent instead if one with the same title already exists in the folder. Inside the workspace,
`setup/06_deploy_dashboards_and_agents` creates and shares both agents without a laptop.
"""
import argparse, json, sys, time, uuid

import workspace_api
from workspace_api import api

CAT = "smbc_workshop.checkpoint"

STARTER = """This agent answers questions about SMBC APAC's corporate lending exposure. All data is synthetic.

- Exposure means drawn balance. Use exposure_usd unless the user asks for yen; then use exposure_jpy.
- Utilisation means a counterparty group's exposure divided by its approved group limit (utilisation_pct in gold_group_exposure). Above 90% is "near its limit"; above 100% is "in breach".
- Balances are month-end snapshots. For "current" or "latest", use the most recent as_of_date. Never add balances across months; compare month ends instead.
- A counterparty group's exposure includes all of its subsidiaries in every country (parent_group_id).
- Booking branch codes: SIN Singapore, HKG Hong Kong, BKK Bangkok, SGN Ho Chi Minh City, JKT Jakarta, BOM Mumbai, SYD Sydney, SEL Seoul, SHA Shanghai, KUL Kuala Lumpur, MNL Manila, TPE Taipei.
- Arrears means days_past_due greater than 30.
- Show amounts in USD millions with one decimal place unless asked otherwise."""

FISCAL_YEAR = """The fiscal year runs from 1 April to 31 March and is named after the calendar year it starts in: FY2026 = 1 April 2026 to 31 March 2027. H1 = April to September; H2 = October to March. Q1 = April-June, Q2 = July-September, Q3 = October-December, Q4 = January-March. "End of FY2026 H1" means as_of_date = 2026-09-30. "FY2026 to date" means as_of_date from 2026-04-30 onwards."""

DESCRIPTIONS = {
    "reference": "SMBC APAC corporate lending exposure. Synthetic data for the SMBC Data & AI Workshop.",
    "starter": "Lab 2 starting point: no fiscal-year instruction yet. Synthetic data for the SMBC Data & AI Workshop.",
    "secured": "Governance demo: a row filter (Singapore branch only unless you're a facilitator) and a masked borrower name. Synthetic data.",
}

SECURED_NOTE = """This demo agent uses a copy of the facility table protected by a Unity Catalog row filter and column mask. All data is synthetic. Exposure means drawn balance in USD (exposure_usd). Balances are month-end snapshots; for "latest", use the most recent as_of_date. Show amounts in USD millions with one decimal place."""

EXAMPLES = [
    ("Top 10 counterparty groups by exposure at the latest month end",
     f"SELECT group_name, round(exposure_usd / 1e6, 1) AS exposure_usd_m, utilisation_pct\nFROM {CAT}.gold_group_exposure\n"
     f"WHERE as_of_date = (SELECT max(as_of_date) FROM {CAT}.gold_group_exposure)\nORDER BY exposure_usd DESC\nLIMIT 10", None),
    ("Exposure by country and sector at a given month end",
     f"SELECT country_code, sector, round(sum(exposure_usd) / 1e6, 1) AS exposure_usd_m\nFROM {CAT}.gold_facility_exposure\n"
     "WHERE as_of_date = :as_of_date\nGROUP BY country_code, sector\nORDER BY exposure_usd_m DESC",
     [{"name": "as_of_date", "type_hint": "DATE", "default_value": {"values": ["2026-09-30"]}}]),
]
QUESTIONS = [
    "Which counterparty groups are closest to their limits?",
    "How has total exposure changed month by month since April 2025?",
    "What is our exposure to Vietnam by sector at the latest month end?",
    "Show exposure in yen by booking branch at the latest month end.",
    "Which booking branch has the highest share of trade finance in arrears?",
]
BENCHMARKS = [
    ("Total exposure in USD at 30 Sep 2026",
     f"SELECT sum(exposure_usd) FROM {CAT}.gold_facility_exposure WHERE as_of_date = '2026-09-30'"),
    ("Which groups were above 90% of their limit at the end of FY2026 H1?",
     f"SELECT group_name, utilisation_pct FROM {CAT}.gold_group_exposure WHERE as_of_date = '2026-09-30' AND utilisation_pct > 90"),
    ("Top 5 groups by exposure at the end of June 2026",
     f"SELECT group_name, exposure_usd FROM {CAT}.gold_group_exposure WHERE as_of_date = '2026-06-30' ORDER BY exposure_usd DESC LIMIT 5"),
    ("Utilisation by month in FY2026 for the most utilised group",
     f"SELECT as_of_date, utilisation_pct FROM {CAT}.gold_group_exposure WHERE parent_group_id = (SELECT parent_group_id FROM "
     f"{CAT}.gold_group_exposure WHERE as_of_date = '2026-09-30' ORDER BY utilisation_pct DESC LIMIT 1) AND as_of_date >= '2026-04-30' ORDER BY as_of_date"),
    ("Share of SGN trade-finance exposure in arrears at 30 Sep 2026",
     f"SELECT 100 * sum(CASE WHEN days_past_due > 30 THEN exposure_usd ELSE 0 END) / sum(exposure_usd) FROM {CAT}.gold_facility_exposure "
     "WHERE as_of_date = '2026-09-30' AND booking_branch = 'SGN' AND source_system = 'TRADE_FIN'"),
]


def oid():
    return uuid.uuid4().hex


def lines(text):
    parts = text.split("\n")
    return [p + "\n" for p in parts[:-1]] + [parts[-1]]


def build(variant):
    if variant == "secured":
        tables = [{"identifier": f"{CAT}.gold_facility_exposure_secured"}]
        text = SECURED_NOTE
        examples, questions, benchmarks, joins = [], ["What is our total exposure by booking branch at the latest month end?"], [], []
    else:
        matching = {"group_name", "counterparty_name", "sector", "country_code", "booking_branch", "product_type"}
        def cfg(cols):
            return [{"column_name": c, "enable_format_assistance": True, **({"enable_entity_matching": True} if c in matching else {})}
                    for c in sorted(cols)]
        tables = [
            {"identifier": f"{CAT}.gold_facility_exposure",
             "column_configs": cfg(["booking_branch", "counterparty_name", "country_code", "group_name", "product_type", "sector"])},
            {"identifier": f"{CAT}.gold_group_exposure", "column_configs": cfg(["group_name"])},
        ]
        text = STARTER + ("\n\n" + FISCAL_YEAR if variant == "reference" else "")
        examples, questions = EXAMPLES, QUESTIONS
        benchmarks = BENCHMARKS if variant == "reference" else []
        joins = [{"id": oid(),
                  "left": {"identifier": f"{CAT}.gold_facility_exposure", "alias": "gold_facility_exposure"},
                  "right": {"identifier": f"{CAT}.gold_group_exposure", "alias": "gold_group_exposure"},
                  "sql": ["`gold_facility_exposure`.`parent_group_id` = `gold_group_exposure`.`parent_group_id` AND "
                          "`gold_facility_exposure`.`as_of_date` = `gold_group_exposure`.`as_of_date`",
                          "--rt=FROM_RELATIONSHIP_TYPE_MANY_TO_ONE--"]}]
    space = {
        "version": 2,
        "config": {"sample_questions": [{"id": oid(), "question": [q]} for q in questions]},
        "data_sources": {"tables": sorted(tables, key=lambda t: t["identifier"])},
        "instructions": {
            "text_instructions": [{"id": oid(), "content": lines(text)}],
            "example_question_sqls": [
                {"id": oid(), "question": [q], "sql": lines(sql), **({"parameters": params} if params else {})}
                for q, sql, params in examples],
            **({"join_specs": joins} if joins else {}),
        },
        **({"benchmarks": {"questions": [
            {"id": oid(), "question": [q], "answer": [{"format": "SQL", "content": lines(sql)}]} for q, sql in benchmarks]}}
           if benchmarks else {}),
    }
    # The API wants ids sorted within each collection.
    space["config"]["sample_questions"].sort(key=lambda x: x["id"])
    space["instructions"]["example_question_sqls"].sort(key=lambda x: x["id"])
    if "benchmarks" in space:
        space["benchmarks"]["questions"].sort(key=lambda x: x["id"])
    return space


def find(title, parent):
    """ID of the agent called `title` in folder `parent`, or None. Agents elsewhere are never matched."""
    folder = parent.rstrip("/").removeprefix("/Workspace")
    token = None
    while True:
        page = api("get", "/api/2.0/genie/spaces", {"page_size": 100, **({"page_token": token} if token else {})})
        for space in page.get("spaces", []):
            if space.get("title") == title:
                details = api("get", f"/api/2.0/genie/spaces/{space['space_id']}")
                if (details.get("parent_path") or "").removeprefix("/Workspace") == folder:
                    return space["space_id"]
        token = page.get("next_page_token")
        if not token:
            return None


def create_or_update(title, variant, warehouse, parent, description=None):
    """Create the agent, or replace its configuration if it already exists in `parent`. Returns (space_id, created)."""
    body = {"title": title, "description": description or DESCRIPTIONS[variant], "warehouse_id": warehouse,
            "serialized_space": json.dumps(build(variant))}
    existing = find(title, parent)
    if existing:
        api("patch", f"/api/2.0/genie/spaces/{existing}", body)
        return existing, False
    return api("post", "/api/2.0/genie/spaces", {**body, "parent_path": parent})["space_id"], True


def ask(space_id, question, conversation=None, show=True):
    """Ask one question and wait for the answer. Returns status, text, SQL, columns and rows."""
    path = (f"/api/2.0/genie/spaces/{space_id}/conversations/{conversation}/messages" if conversation
            else f"/api/2.0/genie/spaces/{space_id}/start-conversation")
    msg = api("post", path, {"content": question})
    conv = msg.get("conversation_id") or conversation
    mid = msg.get("message_id") or msg.get("id") or msg.get("message", {}).get("id")
    started = time.time()
    while True:
        m = api("get", f"/api/2.0/genie/spaces/{space_id}/conversations/{conv}/messages/{mid}")
        if m.get("status") in ("COMPLETED", "FAILED", "CANCELLED", "QUERY_RESULT_EXPIRED") or time.time() - started > 300:
            break
        time.sleep(3)
    answer = {"conversation_id": conv, "status": m.get("status"), "seconds": round(time.time() - started),
              "error": m.get("error"), "text": "", "sql": "", "columns": [], "rows": []}
    for att in m.get("attachments", []) or []:
        if att.get("text"):
            answer["text"] += att["text"].get("content", "")
        if att.get("query"):
            answer["sql"] = att["query"].get("query", "")
            try:
                res = api("get", f"/api/2.0/genie/spaces/{space_id}/conversations/{conv}/messages/{mid}"
                                 f"/attachments/{att['attachment_id']}/query-result")
                sr = res.get("statement_response", res)
                answer["columns"] = [c["name"] for c in sr.get("manifest", {}).get("schema", {}).get("columns", [])]
                answer["rows"] = sr.get("result", {}).get("data_array", []) or []
            except workspace_api.ApiError as err:
                answer["error"] = str(err)[:300]
    if show:
        print(f"Q: {question}\n   status={answer['status']} conversation={conv} ({answer['seconds']}s)")
        if answer["error"]:
            print("   error:", json.dumps(answer["error"])[:500])
        if answer["text"]:
            print("   TEXT:", " ".join(answer["text"].split())[:900])
        if answer["sql"]:
            print("   SQL :", " ".join(answer["sql"].split())[:900])
            print("   ROWS:", answer["columns"])
            for r in answer["rows"][:8]:
                print("        ", r)
            if len(answer["rows"]) > 8:
                print(f"         ... {len(answer['rows'])} rows")
    return answer


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd")
    ap.add_argument("args", nargs="*")
    ap.add_argument("--variant", default="reference")
    ap.add_argument("--title", default="Credit Risk (reference)")
    ap.add_argument("--description")
    ap.add_argument("--profile", "-p", default="DEFAULT")
    ap.add_argument("--warehouse", default="", help="SQL warehouse name or ID (create/patch; default: pick one you can use)")
    ap.add_argument("--parent", help="workspace folder for the agent (create)")
    ap.add_argument("--conversation")
    a = ap.parse_args()
    workspace_api.use_profile(a.profile)
    if a.cmd in ("create", "patch"):
        a.warehouse = workspace_api.pick_warehouse(a.warehouse)["id"]
    if a.cmd == "build":
        print(json.dumps(build(a.variant), indent=2))
    elif a.cmd == "create":
        space_id, created = create_or_update(a.title, a.variant, a.warehouse, a.parent, a.description)
        print(space_id, "(created)" if created else "(updated)")
    elif a.cmd == "patch":
        body = {"title": a.title, "description": a.description or DESCRIPTIONS[a.variant], "warehouse_id": a.warehouse,
                "serialized_space": json.dumps(build(a.variant))}
        r = api("patch", f"/api/2.0/genie/spaces/{a.args[0]}", body)
        print("patched", r.get("space_id", a.args[0]))
    elif a.cmd == "ask":
        ask(a.args[0], a.args[1], a.conversation)
    elif a.cmd == "share":
        space, principal, level = a.args
        workspace_api.share("genie", space, principal, level)
        print("shared", space, "with", principal, level)
    elif a.cmd == "delete":
        api("delete", f"/api/2.0/genie/spaces/{a.args[0]}")
        print("deleted", a.args[0])
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    try:
        main()
    except workspace_api.ApiError as err:
        sys.exit(str(err))
