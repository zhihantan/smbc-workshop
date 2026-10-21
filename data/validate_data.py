#!/usr/bin/env python3
"""Check the generated workshop data against its answer key.

Reads only the files a participant would see, applies the Lab 1 cleaning rules
(the same rules as setup/02_build_bronze_silver_gold.sql), recomputes every planted
answer, and compares it with facilitator/answer_key.json. Also writes
facilitator/answer_key.md, a one-page summary for facilitators.

    python validate_data.py --data ./output

Needs pandas (and openpyxl to read the .xlsx; otherwise the CSV copy is used).
"""

import argparse
import json
import math
import os
import sys

import pandas as pd

CURRENCY_FIXES = {"US$": "USD", "S$": "SGD", "RMB": "CNY"}
JUN26, SEP26, APR26 = pd.Timestamp("2026-06-30"), pd.Timestamp("2026-09-30"), pd.Timestamp("2026-04-30")


def parse_dates(series):
    iso = pd.to_datetime(series, format="%Y-%m-%d", errors="coerce")
    ddmm = pd.to_datetime(series, format="%d/%m/%Y", errors="coerce")
    return iso.fillna(ddmm)


def load(root):
    land = os.path.join(root, "landing")
    cp_raw = pd.read_csv(os.path.join(land, "counterparties", "counterparties.csv"), dtype=str,
                         keep_default_na=False)
    fac_raw = pd.read_json(os.path.join(land, "facilities", "facilities.json"), lines=True, dtype=False)
    bal_raw = pd.read_csv(os.path.join(land, "monthly_balances", "monthly_balances.csv"), dtype=str)
    fx = pd.read_csv(os.path.join(land, "fx_rates", "fx_rates.csv"), dtype={"currency_code": str})
    try:
        limits = pd.read_excel(os.path.join(land, "group_limits", "group_limits.xlsx"))
    except ImportError:
        limits = pd.read_csv(os.path.join(root, "facilitator", "group_limits.csv"))
    return cp_raw, fac_raw, bal_raw, fx, limits


def clean(cp_raw, fac_raw, bal_raw, fx, limits):
    """The Lab 1 rules. Returns silver tables, the quarantine, and gold facility-month exposure."""
    cp = cp_raw.drop_duplicates()

    fac = fac_raw.copy()
    fac["currency_std"] = fac["currency"].str.strip().str.upper().replace(CURRENCY_FIXES)
    fac["start"] = parse_dates(fac["start_date"])
    fac["maturity"] = parse_dates(fac["maturity_date"])
    known_cp = set(cp["counterparty_id"])
    known_ccy = set(fx["currency_code"])
    reason = pd.Series(None, index=fac.index, dtype=object)
    for mask, why in [
        (~fac["counterparty_id"].isin(known_cp), "UNKNOWN_COUNTERPARTY"),
        (fac["committed_amount"] <= 0, "NON_POSITIVE_COMMITMENT"),
        (fac["maturity"] < fac["start"], "MATURITY_BEFORE_START"),
        (~fac["currency_std"].isin(known_ccy), "UNKNOWN_CURRENCY"),
        (fac["start"].isna() | fac["maturity"].isna(), "BAD_DATE"),
    ]:
        reason = reason.where(reason.notna() | ~mask, why)
    fac["quarantine_reason"] = reason
    quarantine = fac[fac["quarantine_reason"].notna()]
    fac_ok = fac[fac["quarantine_reason"].isna()]

    bal = bal_raw.copy()
    bal["as_of"] = parse_dates(bal["as_of_date"])
    bal["drawn_amount"] = bal["drawn_amount"].astype(float)
    bal["days_past_due"] = bal["days_past_due"].astype(int)
    bal = bal.sort_values("extract_ts").drop_duplicates(["facility_id", "as_of"], keep="last")

    fx = fx.copy()
    fx["month"] = pd.to_datetime(fx["rate_date"]).dt.to_period("M")

    gold = (bal.merge(fac_ok[["facility_id", "counterparty_id", "product_type", "currency_std",
                              "booking_branch", "source_system"]], on=["facility_id"], suffixes=("_bal", ""))
            .merge(cp[["counterparty_id", "counterparty_name", "parent_group_id", "country_code", "sector"]],
                   on="counterparty_id")
            .merge(limits[["group_id", "group_name", "group_limit_usd"]], left_on="parent_group_id",
                   right_on="group_id"))
    gold["month"] = gold["as_of"].dt.to_period("M")
    gold = gold.merge(fx[["month", "currency_code", "usd_rate", "jpy_rate"]],
                      left_on=["month", "currency_std"], right_on=["month", "currency_code"])
    gold["exposure_usd"] = gold["drawn_amount"] * gold["usd_rate"]
    gold["exposure_jpy"] = gold["drawn_amount"] * gold["jpy_rate"]
    return cp, fac, quarantine, bal, gold


class Checker:
    def __init__(self):
        self.failures, self.passed = [], 0

    def eq(self, label, actual, expected, tol=0.0):
        ok = (abs(actual - expected) <= tol) if isinstance(expected, (int, float)) and not isinstance(
            expected, bool) else actual == expected
        if ok:
            self.passed += 1
        else:
            self.failures.append(f"{label}: got {actual!r}, expected {expected!r}")


def validate(root):
    key = json.load(open(os.path.join(root, "facilitator", "answer_key.json"), encoding="utf-8"))
    cp_raw, fac_raw, bal_raw, fx, limits = load(root)
    cp, fac, quarantine, bal, gold = clean(cp_raw, fac_raw, bal_raw, fx, limits)
    chk = Checker()
    money = 1.0  # USD tolerance for re-summed totals

    rc = key["row_counts"]
    chk.eq("counterparty rows", len(cp_raw), rc["counterparty_rows_in_file"])
    chk.eq("unique counterparties", len(cp), rc["counterparties_unique"])
    chk.eq("facilities", len(fac_raw), rc["facilities"])
    chk.eq("balance rows", len(bal_raw), rc["balance_rows_in_file"])
    chk.eq("unique balance rows", len(bal), rc["balance_rows_unique"])
    chk.eq("groups in limits file", len(limits), rc["groups"])

    dq = key["planted_data_quality"]
    chk.eq("duplicate counterparty rows", len(cp_raw) - len(cp), dq["counterparty_duplicate_rows"])
    messy = fac_raw.loc[fac_raw["currency"] != fac["currency_std"], "currency"].value_counts().to_dict()
    chk.eq("currency codes needing cleanup", dict(sorted(messy.items())), dq["currency_codes_needing_cleanup"])
    chk.eq("quarantine counts", dict(sorted(quarantine["quarantine_reason"].value_counts().to_dict().items())),
           dq["quarantine_counts"])
    chk.eq("re-run duplicate balance rows", len(bal_raw) - len(bal), dq["balance_rerun_duplicate_rows"])
    chk.eq("DD/MM/YYYY balance rows", int(bal_raw["as_of_date"].str.contains("/").sum()),
           dq["balance_rows_with_dd_mm_yyyy_dates"])
    chk.eq("DD/MM/YYYY facility rows", int(fac_raw["start_date"].str.contains("/").sum()),
           dq["facility_rows_with_dd_mm_yyyy_dates"])
    fx_dates = pd.to_datetime(fx["rate_date"]).drop_duplicates()
    not_month_end = sorted((d + pd.offsets.MonthEnd(0)).date().isoformat() for d in fx_dates if not d.is_month_end)
    chk.eq("FX months dated before month-end", not_month_end, dq["fx_months_where_rate_date_is_not_month_end"])

    # Totals and what each shortcut would have done to them
    sep = gold[gold["as_of"] == SEP26]
    tot = key["totals_2026_09_30"]
    chk.eq("total exposure USD", sep["exposure_usd"].sum(), tot["exposure_usd"], money)
    chk.eq("total exposure JPY", sep["exposure_jpy"].sum(), tot["exposure_jpy"], 200.0)

    def exposure_with(bal_table, cp_table, fac_table):
        g = (bal_table[bal_table["as_of"] == SEP26]
             .merge(fac_table[["facility_id", "counterparty_id", "currency_std"]], on="facility_id")
             .merge(cp_table[["counterparty_id", "parent_group_id"]], on="counterparty_id"))
        g["month"] = g["as_of"].dt.to_period("M")
        g = g.merge(fx.assign(month=pd.to_datetime(fx["rate_date"]).dt.to_period("M")),
                    left_on=["month", "currency_std"], right_on=["month", "currency_code"])
        return (g["drawn_amount"] * g["usd_rate"]).sum()

    bal_all = bal_raw.assign(as_of=parse_dates(bal_raw["as_of_date"]),
                             drawn_amount=bal_raw["drawn_amount"].astype(float))
    fac_ok = fac[fac["quarantine_reason"].isna()]
    clean_total = exposure_with(bal, cp, fac_ok)
    chk.eq("clean total (recomputed)", clean_total, tot["exposure_usd"], money)
    chk.eq("overstatement: re-run not removed", exposure_with(bal_all, cp, fac_ok) - clean_total,
           tot["overstatement_if_rerun_not_deduplicated_usd"], money)
    chk.eq("overstatement: counterparties not deduplicated", exposure_with(bal, cp_raw, fac_ok) - clean_total,
           tot["overstatement_if_counterparties_not_deduplicated_usd"], money)
    fac_q_known = fac[fac["quarantine_reason"].isin(["NON_POSITIVE_COMMITMENT", "MATURITY_BEFORE_START"])]
    orphan_ids = set(fac.loc[fac["quarantine_reason"] == "UNKNOWN_COUNTERPARTY", "facility_id"])
    orphans = bal[(bal["as_of"] == SEP26) & bal["facility_id"].isin(orphan_ids)].merge(
        fac[["facility_id", "currency_std"]], on="facility_id")
    orphan_usd = (orphans.merge(fx[pd.to_datetime(fx["rate_date"]).dt.to_period("M") == SEP26.to_period("M")],
                                left_on="currency_std", right_on="currency_code")
                  .eval("drawn_amount * usd_rate").sum())
    chk.eq("excluded by quarantine", exposure_with(bal, cp, fac_q_known) + orphan_usd,
           tot["excluded_by_quarantine_usd"], money)
    iso_only = bal.assign(as_of=pd.to_datetime(bal["as_of_date"], format="%Y-%m-%d", errors="coerce"))
    chk.eq("lost if only ISO dates parsed", clean_total - exposure_with(iso_only, cp, fac_ok),
           tot["lost_if_only_iso_dates_parsed_usd"], money)

    # Groups
    grp = (gold.groupby(["as_of", "parent_group_id", "group_name", "group_limit_usd"], as_index=False)
           ["exposure_usd"].sum())
    grp["utilisation_pct"] = 100 * grp["exposure_usd"] / grp["group_limit_usd"]
    for when, label in [(JUN26, "2026_06_30"), (SEP26, "2026_09_30")]:
        top = grp[grp["as_of"] == when].nlargest(10, "exposure_usd")
        expected = key["groups"][f"top10_by_exposure_{label}"]
        chk.eq(f"top 10 groups {label}", list(top["parent_group_id"]), [r["group_id"] for r in expected])
        for (_, row), exp in zip(top.iterrows(), expected):
            chk.eq(f"{exp['group_name']} exposure {label}", row["exposure_usd"], exp["exposure_usd"], money)
        over = sorted(grp[(grp["as_of"] == when) & (grp["utilisation_pct"] > 90)]["group_name"])
        chk.eq(f"groups over 90% {label}", over, key["groups"][f"over_90pct_of_limit_{label}"])
    orchid_id = key["orchid_group"]["group_id"]
    chk.eq("max utilisation excluding Orchid", grp[grp["parent_group_id"] != orchid_id]["utilisation_pct"].max(),
           key["groups"]["max_utilisation_pct_excluding_orchid_any_month"], 1e-3)

    # Orchid Group
    o = key["orchid_group"]
    og = grp[grp["parent_group_id"] == orchid_id].sort_values("as_of")
    chk.eq("Orchid monthly utilisation", [round(u, 2) for u in og["utilisation_pct"]],
           [round(m["utilisation_pct"], 2) for m in o["monthly"]])
    of = gold[gold["parent_group_id"] == orchid_id]
    a = of[of["as_of"] == APR26].set_index("facility_id")
    s = of[of["as_of"] == SEP26].set_index("facility_id")
    volume = ((s["drawn_amount"] - a["drawn_amount"]) * a["usd_rate"]).sum()
    fx_effect = (s["drawn_amount"] * (s["usd_rate"] - a["usd_rate"])).sum()
    ch = o["change_apr_to_sep_2026"]
    chk.eq("Orchid volume effect", volume, ch["volume_effect_usd"], money)
    chk.eq("Orchid FX effect", fx_effect, ch["fx_effect_usd"], money)
    chk.eq("Orchid FX share %", 100 * fx_effect / (volume + fx_effect), ch["fx_share_pct"], 1e-3)
    cp_sep = sep.groupby("counterparty_id")["exposure_usd"].sum().rank(ascending=False, method="first")
    best_rank = int(min(cp_sep[sub["counterparty_id"]] for sub in o["subsidiaries"]))
    chk.eq("best Orchid subsidiary rank", best_rank,
           min(sub["rank_among_all_counterparties_2026_09_30"] for sub in o["subsidiaries"]))

    # Arrears creep
    sgn = gold[(gold["booking_branch"] == key["dpd_creep"]["booking_branch"]) & (gold["source_system"] == "TRADE_FIN")]
    shares = (sgn.assign(late=sgn["exposure_usd"].where(sgn["days_past_due"] > 30, 0.0))
              .groupby("as_of")[["late", "exposure_usd"]].sum())
    chk.eq("SGN trade-finance arrears trend", [round(100 * r.late / r.exposure_usd, 2) for r in shares.itertuples()],
           [round(m["share_of_exposure_over_30_dpd_pct"], 2) for m in key["dpd_creep"]["by_month"]])
    return key, chk


def write_summary(root, key):
    o, t, dq, g = key["orchid_group"], key["totals_2026_09_30"], key["planted_data_quality"], key["groups"]
    ch = o["change_apr_to_sep_2026"]
    m = lambda x: f"USD {x / 1e6:,.1f}m"  # noqa: E731
    lines = [
        "# Answer key (facilitators only)",
        "",
        f"Generated by `data/generate_data.py` (seed {key['generated_with']['seed']}) and checked by "
        "`data/validate_data.py`. Every number below comes from the files participants use, after the Lab 1 "
        "cleaning rules. **Don't share this with participants.**",
        "",
        "## The story in five numbers",
        "",
        f"1. **Orchid Group** (`{o['group_id']}`) uses **{o['monthly'][12]['utilisation_pct']:.0f}%** of its "
        f"{m(o['group_limit_usd'])} limit at 30 Apr 2026 and **{o['monthly'][-1]['utilisation_pct']:.0f}%** at "
        f"30 Sep 2026. It first passes 90% in **September 2026**; no other group goes above "
        f"{g['max_utilisation_pct_excluding_orchid_any_month']:.1f}% in any month.",
        f"2. It is invisible one subsidiary at a time: the largest of its 14 subsidiaries ranks only "
        f"**#{min(s['rank_among_all_counterparties_2026_09_30'] for s in o['subsidiaries'])}** among counterparties.",
        f"3. Of the {m(ch['total_change_usd'])} rise since April, **{ch['fx_share_pct']:.0f}% is FX** "
        f"({m(ch['fx_effect_usd'])}) and the rest is new drawdowns ({m(ch['volume_effect_usd'])}). "
        f"Measured on April balances instead, FX is {ch['alt_fx_share_pct']:.0f}%. "
        f"Four subsidiaries account for {o['growth_drivers_share_of_volume_change_pct']:.0f}% of the new drawdowns.",
        f"4. The re-loaded {dq['balance_rerun_extract']} overstates total exposure by "
        f"**{m(t['overstatement_if_rerun_not_deduplicated_usd'])}** unless duplicates are removed.",
        f"5. **The fiscal-year trap:** at the end of calendar H1 (30 Jun 2026) "
        f"{'no group is' if not g['over_90pct_of_limit_2026_06_30'] else ', '.join(g['over_90pct_of_limit_2026_06_30'])}"
        f" over 90%; at the end of FY2026 H1 (30 Sep 2026): **{', '.join(g['over_90pct_of_limit_2026_09_30'])}**.",
        "",
        "## Totals at 30 Sep 2026",
        "",
        "| Measure | Value |",
        "|---|---|",
        f"| Total exposure | {m(t['exposure_usd'])} (JPY {t['exposure_jpy'] / 1e9:,.1f}bn) |",
        f"| Overstated if the re-run extract isn't de-duplicated | {m(t['overstatement_if_rerun_not_deduplicated_usd'])} |",
        f"| Overstated if duplicate counterparties fan out in joins | "
        f"{m(t['overstatement_if_counterparties_not_deduplicated_usd'])} |",
        f"| Held back by quarantine | {m(t['excluded_by_quarantine_usd'])} |",
        f"| Silently lost if only ISO dates are parsed | {m(t['lost_if_only_iso_dates_parsed_usd'])} |",
        "",
        "## Top 5 groups by exposure",
        "",
        "| Rank | 30 Jun 2026 (calendar H1) | 30 Sep 2026 (FY2026 H1) |",
        "|---|---|---|",
    ]
    for a, b in zip(g["top10_by_exposure_2026_06_30"][:5], g["top10_by_exposure_2026_09_30"][:5]):
        lines.append(f"| {a['rank']} | {a['group_name']}: {m(a['exposure_usd'])}, {a['utilisation_pct']:.1f}% | "
                     f"{b['group_name']}: {m(b['exposure_usd'])}, {b['utilisation_pct']:.1f}% |")
    lines += [
        "",
        "## Orchid Group by month",
        "",
        "| Month end | Exposure | Utilisation |",
        "|---|---|---|",
    ]
    lines += [f"| {r['as_of_date']} | {m(r['exposure_usd'])} | {r['utilisation_pct']:.1f}% |" for r in o["monthly"]]
    lines += [
        "",
        "## Orchid subsidiaries at 30 Sep 2026",
        "",
        "| Subsidiary | Country | Exposure | New drawdowns since April | Rank among all counterparties |",
        "|---|---|---|---|---|",
    ]
    lines += [f"| {s['counterparty_name']}{' *(growth driver)*' if s['growth_driver'] else ''} | {s['country_code']} | "
              f"{m(s['exposure_usd_2026_09_30'])} | {m(s['volume_change_usd_apr_to_sep_2026'])} | "
              f"{s['rank_among_all_counterparties_2026_09_30']} |" for s in o["subsidiaries"]]
    lines += [
        "",
        "## Planted data-quality problems",
        "",
        f"- **Duplicate counterparty rows:** {dq['counterparty_duplicate_rows']} exact copies in `counterparties.csv`.",
        f"- **Currency codes needing cleanup:** "
        + ", ".join(f"`{k}` ×{v}" for k, v in dq["currency_codes_needing_cleanup"].items())
        + ". Designer joins ignore case and surrounding spaces by default, so only `US$`, `S$` and `RMB` "
          "show up in the join's unmatched output.",
        f"- **Quarantine:** " + ", ".join(f"{k} ×{v}" for k, v in dq["quarantine_counts"].items()) + ".",
        f"- **Re-run extract:** {dq['balance_rerun_duplicate_rows']} duplicate balance rows ({dq['balance_rerun_extract']}),"
        " identical except for a later `extract_ts`. Deduplicate on `facility_id` + `as_of_date`, keeping the latest.",
        f"- **Dates:** {dq['balance_rows_with_dd_mm_yyyy_dates']:,} balance rows and "
        f"{dq['facility_rows_with_dd_mm_yyyy_dates']:,} facility rows (trade-finance system) use DD/MM/YYYY.",
        "- **FX dated on the last business day:** an exact-date join loses "
        + ", ".join(dq["fx_months_where_rate_date_is_not_month_end"])
        + ". Join on currency and month instead.",
        "",
        "## Arrears creep: SGN (Ho Chi Minh City) trade finance, % of exposure more than 30 days past due",
        "",
        " → ".join(f"{r['as_of_date'][:7]}: {r['share_of_exposure_over_30_dpd_pct']:.1f}%"
                   for r in key["dpd_creep"]["by_month"][-7:]),
        f"(whole book at 30 Sep 2026: {key['dpd_creep']['portfolio_share_of_exposure_over_30_dpd_pct_2026_09_30']:.1f}%)",
        "",
    ]
    with open(os.path.join(root, "facilitator", "answer_key.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data", default="output", help="the --out folder used with generate_data.py")
    args = parser.parse_args()
    key, chk = validate(args.data)
    write_summary(args.data, key)
    print(f"{chk.passed} checks passed, {len(chk.failures)} failed")
    for failure in chk.failures:
        print("  FAIL", failure)
    sys.exit(1 if chk.failures else 0)


if __name__ == "__main__":
    main()
