#!/usr/bin/env python3
"""Build, test and deploy the two SMBC workshop dashboards (Lakeview API).

From a laptop, through the Databricks CLI:

  python setup/tools/dashboards.py --profile P --warehouse W --parent /Workspace/Users/<you>/smbc_workshop test
  python setup/tools/dashboards.py --profile P --warehouse W --parent /Workspace/Users/<you>/smbc_workshop deploy

`test` runs every dataset query and prints row counts; `deploy` creates or updates the reference dashboard and the
facilitator progress board, then publishes both. Run `test` first: every query must succeed. Inside the workspace,
`setup/06_deploy_dashboards_and_agents` does the same without a laptop.
"""
import argparse, json, sys, time

import workspace_api
from workspace_api import api

WAREHOUSE, PARENT = None, None  # set by configure()
REFERENCE_NAME = "Credit Committee: APAC exposure (reference)"
PROGRESS_NAME = "SMBC Workshop: progress board"
G = "smbc_workshop.checkpoint.gold_group_exposure"
F = "smbc_workshop.checkpoint.gold_facility_exposure"
LATEST = f"(SELECT max(as_of_date) FROM {G})"
EXCLUDED = "('information_schema', 'default', 'raw', 'checkpoint', 'ops')"

REFERENCE = {
    "ds_kpis": ("Headline KPIs (latest month end)",
        f"SELECT max(as_of_date) AS as_of_date, round(sum(exposure_usd) / 1e6, 1) AS total_exposure_usd_m, "
        f"sum(CASE WHEN utilisation_pct > 80 THEN 1 ELSE 0 END) AS groups_above_80, "
        f"sum(CASE WHEN utilisation_pct > 90 THEN 1 ELSE 0 END) AS groups_above_90 "
        f"FROM {G} WHERE as_of_date = {LATEST}"),
    "ds_top_groups": ("Top 10 groups (latest month end)",
        f"SELECT group_name, round(exposure_usd / 1e6, 1) AS exposure_usd_m, utilisation_pct, "
        f"CASE WHEN utilisation_pct > 90 THEN 'Above 90%' WHEN utilisation_pct > 80 THEN '80-90%' ELSE 'Below 80%' END "
        f"AS utilisation_band FROM {G} WHERE as_of_date = {LATEST} ORDER BY exposure_usd DESC LIMIT 10"),
    "ds_trend": ("Total exposure by month",
        f"SELECT as_of_date AS month_end, round(sum(exposure_usd) / 1e6, 1) AS exposure_usd_m FROM {G} GROUP BY as_of_date"),
    "ds_country": ("Exposure by country (latest month end)",
        f"SELECT country_code, round(sum(exposure_usd) / 1e6, 1) AS exposure_usd_m FROM {F} "
        f"WHERE as_of_date = (SELECT max(as_of_date) FROM {F}) GROUP BY country_code"),
    "ds_top5_util": ("Utilisation of the five largest groups",
        f"WITH top5 AS (SELECT parent_group_id FROM {G} WHERE as_of_date = {LATEST} ORDER BY exposure_usd DESC LIMIT 5) "
        f"SELECT g.as_of_date AS month_end, g.group_name, g.utilisation_pct FROM {G} g JOIN top5 USING (parent_group_id)"),
    "ds_watchlist": ("Groups above 80% of limit (latest month end)",
        f"SELECT group_name, round(exposure_usd / 1e6, 1) AS exposure_usd_m, round(group_limit_usd / 1e6, 1) AS limit_usd_m, "
        f"utilisation_pct, counterparties FROM {G} WHERE as_of_date = {LATEST} AND utilisation_pct > 80 ORDER BY utilisation_pct DESC"),
    "ds_arrears": ("Trade finance in arrears by month",
        f"SELECT as_of_date AS month_end, CASE WHEN booking_branch = 'SGN' THEN 'Ho Chi Minh City (SGN)' ELSE 'All other branches' END "
        f"AS branch_group, round(100 * sum(CASE WHEN days_past_due > 30 THEN exposure_usd ELSE 0 END) / sum(exposure_usd), 2) AS arrears_pct "
        f"FROM {F} WHERE source_system = 'TRADE_FIN' GROUP BY 1, 2"),
}

PROGRESS = {
    "pb_kpis": ("Headline counters",
        f"WITH participant_schemas AS (SELECT schema_name FROM smbc_workshop.information_schema.schemata WHERE schema_name NOT IN {EXCLUDED}), "
        f"lab1 AS (SELECT DISTINCT table_schema FROM smbc_workshop.information_schema.tables "
        f"WHERE table_schema IN (SELECT schema_name FROM participant_schemas) AND lower(table_name) LIKE '%group_exposure%') "
        f"SELECT (SELECT count(DISTINCT user_email) FROM smbc_workshop.ops.checkin) AS checked_in, (SELECT count(*) FROM lab1) AS lab1_finished, "
        f"(SELECT count(DISTINCT user_email) FROM smbc_workshop.ops.lab_answers WHERE lab = 'lab2' AND lower(answer) LIKE '%orchid%') AS lab2_found_orchid"),
    "pb_people": ("Per-person progress",
        f"WITH participant_schemas AS (SELECT schema_name FROM smbc_workshop.information_schema.schemata WHERE schema_name NOT IN {EXCLUDED}), "
        f"tables AS (SELECT table_schema, lower(table_name) AS table_name, created FROM smbc_workshop.information_schema.tables) "
        f"SELECT p.schema_name AS participant, count(t.table_name) AS tables_written, "
        f"max(CASE WHEN t.table_name LIKE '%quarantine%' THEN 'yes' ELSE '' END) AS quarantine_table, "
        f"max(CASE WHEN t.table_name LIKE '%group_exposure%' THEN 'yes' ELSE '' END) AS lab1_done, "
        f"min(t.created) AS first_table_at FROM participant_schemas p LEFT JOIN tables t ON t.table_schema = p.schema_name "
        f"GROUP BY p.schema_name ORDER BY lab1_done DESC, tables_written DESC, first_table_at"),
    "pb_first": ("First to finish Lab 1",
        f"SELECT table_schema AS participant, min(created) AS finished_at FROM smbc_workshop.information_schema.tables "
        f"WHERE lower(table_name) LIKE '%group_exposure%' AND table_schema NOT IN {EXCLUDED} GROUP BY table_schema ORDER BY finished_at LIMIT 10"),
    "pb_answers": ("Lab 2 answers",
        "SELECT user_email, answer, submitted_at, CASE WHEN lower(answer) LIKE '%orchid%' THEN 'correct' ELSE 'not yet' END AS result "
        "FROM smbc_workshop.ops.lab_answers WHERE lab = 'lab2' ORDER BY submitted_at"),
}


def configure(warehouse, parent):
    global WAREHOUSE, PARENT
    WAREHOUSE, PARENT = warehouse, parent.rstrip("/")


def run_sql(sql):
    r = api("post", "/api/2.0/sql/statements", {"warehouse_id": WAREHOUSE, "statement": sql, "wait_timeout": "50s"})
    while r["status"]["state"] in ("PENDING", "RUNNING"):  # e.g. while the warehouse starts
        time.sleep(3)
        r = api("get", f"/api/2.0/sql/statements/{r['statement_id']}")
    state = r["status"]["state"]
    if state != "SUCCEEDED":
        return state, r["status"].get("error", {}).get("message", "")[:400], [], []
    cols = [c["name"] for c in r["manifest"]["schema"]["columns"]]
    return state, "", cols, r.get("result", {}).get("data_array", []) or []


def test():
    """Run every dataset query; return the number that failed."""
    bad = 0
    for spec in (REFERENCE, PROGRESS):
        for key, (title, sql) in spec.items():
            state, err, cols, rows = run_sql(sql)
            bad += state != "SUCCEEDED"
            print(f"{key:<14} {state:<9} rows={len(rows):<4} cols={cols} {err}")
            for r in rows[:3]:
                print("               ", r)
    return bad


def text(name, md, y):
    return {"widget": {"name": name, "multilineTextboxSpec": {"lines": [md]}}, "position": {"x": 0, "y": y, "width": 6, "height": 1}}


def counter(name, ds, field, title, x, y):
    return {"widget": {"name": name, "queries": [{"name": "main_query", "query": {"datasetName": ds, "fields": [
        {"name": field, "expression": f"`{field}`"}], "disaggregated": True}}],
        "spec": {"version": 2, "widgetType": "counter", "encodings": {"value": {"fieldName": field, "displayName": title}},
                 "frame": {"showTitle": True, "title": title}}},
        "position": {"x": x, "y": y, "width": 2, "height": 3}}


def chart(name, kind, ds, x_field, x_scale, y_expr_name, y_expr, title, pos, color=None, sort=None, y_title=None, x_title=None):
    fields = [{"name": x_field, "expression": f"`{x_field}`"}, {"name": y_expr_name, "expression": y_expr}]
    enc = {"x": {"fieldName": x_field, "scale": {"type": x_scale, **({"sort": {"by": sort}} if sort else {})},
                 "displayName": x_title or x_field},
           "y": {"fieldName": y_expr_name, "scale": {"type": "quantitative"}, "displayName": y_title or y_expr_name}}
    if color:
        fields.append({"name": color[0], "expression": f"`{color[0]}`"})
        enc["color"] = {"fieldName": color[0], "scale": {"type": "categorical", **({"mappings": color[1]} if color[1] else {})},
                        "displayName": color[2]}
    if kind == "bar":
        enc["label"] = {"show": True}
    return {"widget": {"name": name, "queries": [{"name": "main_query", "query": {"datasetName": ds, "fields": fields,
                                                                                   "disaggregated": False}}],
                       "spec": {"version": 3, "widgetType": kind, "encodings": enc, "frame": {"showTitle": True, "title": title}}},
            "position": pos}


def table(name, ds, cols, title, pos):
    return {"widget": {"name": name, "queries": [{"name": "main_query", "query": {"datasetName": ds, "fields": [
        {"name": c, "expression": f"`{c}`"} for c, _ in cols], "disaggregated": True}}],
        "spec": {"version": 2, "widgetType": "table", "encodings": {"columns": [{"fieldName": c, "displayName": d} for c, d in cols]},
                 "frame": {"showTitle": True, "title": title}}},
        "position": pos}


def datasets(spec):
    return [{"name": k, "displayName": v[0], "queryLines": [v[1]]} for k, v in spec.items()]


def reference_dashboard():
    band = [{"value": "Above 90%", "color": "#FF3621"}, {"value": "80-90%", "color": "#FFAB00"}, {"value": "Below 80%", "color": "#00A972"}]
    layout = [
        text("title", "## Credit Committee: APAC exposure", 0),
        text("subtitle", "SMBC APAC: month-end drawn exposure and group limit utilisation. *Synthetic data for the SMBC Data & AI Workshop.*", 1),
        counter("kpi_total", "ds_kpis", "total_exposure_usd_m", "Total exposure, latest month end (USD m)", 0, 2),
        counter("kpi_80", "ds_kpis", "groups_above_80", "Groups above 80% of limit", 2, 2),
        counter("kpi_90", "ds_kpis", "groups_above_90", "Groups above 90% of limit", 4, 2),
        chart("top_groups", "bar", "ds_top_groups", "group_name", "categorical", "sum(exposure_usd_m)", "SUM(`exposure_usd_m`)",
              "Top 10 counterparty groups by exposure (USD m), latest month end", {"x": 0, "y": 5, "width": 3, "height": 6},
              color=("utilisation_band", band, "Limit utilisation"), sort="y-reversed", y_title="Exposure (USD m)", x_title="Group"),
        chart("trend", "line", "ds_trend", "month_end", "temporal", "sum(exposure_usd_m)", "SUM(`exposure_usd_m`)",
              "Total exposure by month (USD m)", {"x": 3, "y": 5, "width": 3, "height": 6}, y_title="Exposure (USD m)", x_title="Month end"),
        chart("top5_util", "line", "ds_top5_util", "month_end", "temporal", "sum(utilisation_pct)", "SUM(`utilisation_pct`)",
              "Limit utilisation (%) of the five largest groups", {"x": 0, "y": 11, "width": 3, "height": 6},
              color=("group_name", None, "Group"), y_title="Utilisation (%)", x_title="Month end"),
        chart("country", "bar", "ds_country", "country_code", "categorical", "sum(exposure_usd_m)", "SUM(`exposure_usd_m`)",
              "Exposure by borrower country (USD m), latest month end", {"x": 3, "y": 11, "width": 3, "height": 6},
              sort="y-reversed", y_title="Exposure (USD m)", x_title="Country"),
        table("watchlist", "ds_watchlist", [("group_name", "Group"), ("exposure_usd_m", "Exposure (USD m)"), ("limit_usd_m", "Limit (USD m)"),
                                            ("utilisation_pct", "Utilisation (%)"), ("counterparties", "Subsidiaries")],
              "Watchlist: groups above 80% of limit, latest month end", {"x": 0, "y": 17, "width": 3, "height": 6}),
        chart("arrears", "line", "ds_arrears", "month_end", "temporal", "sum(arrears_pct)", "SUM(`arrears_pct`)",
              "Trade finance more than 30 days past due (% of exposure)", {"x": 3, "y": 17, "width": 3, "height": 6},
              color=("branch_group", None, "Booking branch"), y_title="% of exposure", x_title="Month end"),
    ]
    return {"datasets": datasets(REFERENCE), "pages": [{"name": "overview", "displayName": "Overview", "pageType": "PAGE_TYPE_CANVAS",
                                                         "layout": layout}],
            "uiSettings": {"theme": {"widgetHeaderAlignment": "ALIGNMENT_UNSPECIFIED"}, "applyModeEnabled": False}}


def progress_board():
    layout = [
        text("title", "## SMBC Data & AI Workshop: progress board", 0),
        text("subtitle", "Live from Unity Catalog. Lab 1 is done when your schema has a *gold_group_exposure* table; Lab 2 when you submit the group you found.", 1),
        counter("checked_in", "pb_kpis", "checked_in", "Checked in", 0, 2),
        counter("lab1", "pb_kpis", "lab1_finished", "Lab 1 finished", 2, 2),
        counter("lab2", "pb_kpis", "lab2_found_orchid", "Lab 2: found the group", 4, 2),
        table("people", "pb_people", [("participant", "Participant"), ("tables_written", "Tables written"),
                                      ("quarantine_table", "Quarantine table"), ("lab1_done", "Lab 1 done"), ("first_table_at", "First table at")],
              "Progress by participant", {"x": 0, "y": 5, "width": 4, "height": 7}),
        table("first", "pb_first", [("participant", "Participant"), ("finished_at", "Finished at")], "First to finish Lab 1",
              {"x": 4, "y": 5, "width": 2, "height": 7}),
        table("answers", "pb_answers", [("user_email", "Who"), ("answer", "Answer"), ("submitted_at", "Submitted"), ("result", "Result")],
              "Lab 2 answers", {"x": 0, "y": 12, "width": 6, "height": 5}),
    ]
    return {"datasets": datasets(PROGRESS), "pages": [{"name": "board", "displayName": "Board", "pageType": "PAGE_TYPE_CANVAS",
                                                        "layout": layout}],
            "uiSettings": {"theme": {"widgetHeaderAlignment": "ALIGNMENT_UNSPECIFIED"}, "applyModeEnabled": False}}


def deploy(name, body):
    """Create the dashboard, or update it in place if <parent>/<name>.lvdash.json already exists, then publish."""
    payload = {"display_name": name, "warehouse_id": WAREHOUSE, "serialized_dashboard": json.dumps(body)}
    existing = (workspace_api.get_status(f"{PARENT}/{name}.lvdash.json") or {}).get("resource_id")
    if existing:
        dash = api("patch", f"/api/2.0/lakeview/dashboards/{existing}", payload)
    else:
        dash = api("post", "/api/2.0/lakeview/dashboards", {**payload, "parent_path": PARENT})
    api("post", f"/api/2.0/lakeview/dashboards/{dash['dashboard_id']}/published", {"warehouse_id": WAREHOUSE, "embed_credentials": True})
    print(f"{name}: {dash['dashboard_id']} ({'updated' if existing else 'created'} and published)")
    return dash["dashboard_id"]


def deploy_all():
    """Deploy both dashboards; return {name: dashboard_id}."""
    return {REFERENCE_NAME: deploy(REFERENCE_NAME, reference_dashboard()),
            PROGRESS_NAME: deploy(PROGRESS_NAME, progress_board())}


def main():
    ap = argparse.ArgumentParser(description="SMBC workshop dashboards")
    ap.add_argument("--profile", default="DEFAULT", help="Databricks CLI profile")
    ap.add_argument("--warehouse", required=True, help="SQL warehouse ID")
    ap.add_argument("--parent", required=True, help="workspace folder for the dashboards")
    ap.add_argument("action", choices=["test", "deploy"])
    a = ap.parse_args()
    workspace_api.use_profile(a.profile)
    configure(a.warehouse, a.parent)
    if a.action == "test":
        sys.exit(1 if test() else 0)
    deploy_all()


if __name__ == "__main__":
    try:
        main()
    except workspace_api.ApiError as err:
        sys.exit(str(err))
