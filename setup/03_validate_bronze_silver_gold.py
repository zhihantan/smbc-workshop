# Databricks notebook source
# MAGIC %md
# MAGIC # 03 · Validate the bronze, silver and gold tables against the answer key
# MAGIC
# MAGIC Recomputes the planted answers from the `bronze`, `silver` and `gold` schemas of `smbc_workshop` and compares them with
# MAGIC `/Volumes/smbc_workshop/raw/facilitator/answer_key.json`. Every row should say PASS. If one fails, the
# MAGIC quiz answers and facilitator talking points won't match what participants see, so fix it before the day.

# COMMAND ----------

import json

dbutils.widgets.text("catalog", "smbc_workshop", "Catalog")
catalog = dbutils.widgets.get("catalog").strip()
bronze, silver, gold = (f"`{catalog}`.{layer}" for layer in ("bronze", "silver", "gold"))
with open(f"/Volumes/{catalog}/raw/facilitator/answer_key.json", encoding="utf-8") as fh:
    key = json.load(fh)

results = []


def check(label, actual, expected, tolerance=0.0):
    if isinstance(expected, (int, float)) and not isinstance(expected, bool):
        ok = actual is not None and abs(float(actual) - expected) <= tolerance
    else:
        ok = actual == expected
    results.append((label, "PASS" if ok else "FAIL", str(actual)[:120], str(expected)[:120]))


def scalar(sql):
    return spark.sql(sql).collect()[0][0]


def column(sql):
    return [row[0] for row in spark.sql(sql).collect()]

# COMMAND ----------

rows, dq, totals, groups = key["row_counts"], key["planted_data_quality"], key["totals_2026_09_30"], key["groups"]

check("unique counterparties", scalar(f"SELECT count(*) FROM {silver}.counterparties"), rows["counterparties_unique"])
check("counterparty rows in file", scalar(f"SELECT count(*) FROM {bronze}.counterparties"),
      rows["counterparty_rows_in_file"])
check("facilities", scalar(f"SELECT count(*) FROM {bronze}.facilities"), rows["facilities"])
check("balance rows in file", scalar(f"SELECT count(*) FROM {bronze}.balances"), rows["balance_rows_in_file"])
check("unique balance rows", scalar(f"SELECT count(*) FROM {silver}.balances"), rows["balance_rows_unique"])
check("groups with a limit", scalar(f"SELECT count(*) FROM {silver}.group_limits"), rows["groups"])
check("quarantine counts",
      {r[0]: r[1] for r in spark.sql(f"SELECT quarantine_reason, count(*) FROM {silver}.quarantine_facilities "
                                     "GROUP BY 1").collect()},
      dq["quarantine_counts"])

check("total exposure USD at 2026-09-30",
      scalar(f"SELECT sum(exposure_usd) FROM {gold}.facility_exposure WHERE as_of_date = '2026-09-30'"),
      totals["exposure_usd"], 5.0)
check("total exposure JPY at 2026-09-30",
      scalar(f"SELECT sum(exposure_jpy) FROM {gold}.facility_exposure WHERE as_of_date = '2026-09-30'"),
      totals["exposure_jpy"], 1000.0)

for label, date in [("2026_06_30", "2026-06-30"), ("2026_09_30", "2026-09-30")]:
    check(f"top 10 groups {date}",
          column(f"SELECT parent_group_id FROM {gold}.group_exposure WHERE as_of_date = '{date}' "
                 "ORDER BY exposure_usd DESC LIMIT 10"),
          [r["group_id"] for r in groups[f"top10_by_exposure_{label}"]])
    check(f"groups over 90% at {date}",
          column(f"SELECT group_name FROM {gold}.group_exposure WHERE as_of_date = '{date}' "
                 "AND utilisation_pct > 90 ORDER BY group_name"),
          groups[f"over_90pct_of_limit_{label}"])

orchid = key["orchid_group"]
check("Orchid utilisation by month",
      column(f"SELECT utilisation_pct FROM {gold}.group_exposure WHERE parent_group_id = '{orchid['group_id']}' "
             "ORDER BY as_of_date"),
      [round(m["utilisation_pct"], 2) for m in orchid["monthly"]])
check("max utilisation of any other group",
      scalar(f"SELECT max(utilisation_pct) FROM {gold}.group_exposure "
             f"WHERE parent_group_id <> '{orchid['group_id']}'"),
      groups["max_utilisation_pct_excluding_orchid_any_month"], 0.01)

decomposition = spark.sql(f"""
  WITH a AS (SELECT facility_id, drawn_amount_local AS d, usd_rate AS r FROM {gold}.facility_exposure
             WHERE parent_group_id = '{orchid['group_id']}' AND as_of_date = '2026-04-30'),
       s AS (SELECT facility_id, drawn_amount_local AS d, usd_rate AS r FROM {gold}.facility_exposure
             WHERE parent_group_id = '{orchid['group_id']}' AND as_of_date = '2026-09-30')
  SELECT sum((s.d - a.d) * a.r) AS volume, sum(s.d * (s.r - a.r)) AS fx FROM s JOIN a USING (facility_id)
""").collect()[0]
change = orchid["change_apr_to_sep_2026"]
check("Orchid volume effect", decomposition.volume, change["volume_effect_usd"], 5.0)
check("Orchid FX effect", decomposition.fx, change["fx_effect_usd"], 5.0)

check("SGN trade-finance arrears trend (% of exposure > 30 DPD)",
      [round(float(x), 2) for x in column(f"""
          SELECT 100 * sum(CASE WHEN days_past_due > 30 THEN exposure_usd ELSE 0 END) / sum(exposure_usd)
          FROM {gold}.facility_exposure WHERE booking_branch = 'SGN' AND source_system = 'TRADE_FIN'
          GROUP BY as_of_date ORDER BY as_of_date""")],
      [round(m["share_of_exposure_over_30_dpd_pct"], 2) for m in key["dpd_creep"]["by_month"]])

# Lab 1 starts from bronze.exposure_staging. Its Unique and Guardrails steps must reproduce the reference tables.
staging = f"{bronze}.exposure_staging"
lab1 = (f"(SELECT * FROM {staging} QUALIFY row_number() OVER (PARTITION BY facility_id, as_of_date "
        "ORDER BY extract_ts DESC) = 1)")
lab1_passed = (f"(SELECT * FROM {lab1} WHERE committed_amount > 0 AND maturity_date >= start_date "
               "AND parent_group_id IS NOT NULL)")
check("Lab 1 staging has duplicates for Unique to remove",
      scalar(f"SELECT count(*) > count(DISTINCT facility_id, as_of_date) FROM {staging}"), True)
check("Lab 1 staging after Unique: one row per facility and month", scalar(f"SELECT count(*) FROM {lab1}"),
      rows["balance_rows_unique"])
check("Lab 1 staging after Guardrails: the rows in gold.facility_exposure", scalar(f"SELECT count(*) FROM {lab1_passed}"),
      scalar(f"SELECT count(*) FROM {gold}.facility_exposure"))
check("Lab 1 staging after Guardrails: total exposure USD at 2026-09-30",
      scalar(f"SELECT sum(exposure_usd) FROM {lab1_passed} WHERE as_of_date = '2026-09-30'"), totals["exposure_usd"], 5.0)
check("Lab 1 staging after Aggregate: the rows in gold.group_exposure",
      scalar(f"SELECT count(DISTINCT as_of_date, parent_group_id) FROM {lab1_passed}"),
      scalar(f"SELECT count(*) FROM {gold}.group_exposure"))

failed = [r for r in results if r[1] == "FAIL"]
display(spark.createDataFrame(results, "check string, result string, actual string, expected string"))
print(f"{len(results) - len(failed)} passed, {len(failed)} failed")
assert not failed, "Some checks failed: see the table above"
