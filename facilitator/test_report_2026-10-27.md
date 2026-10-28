# Test report: Lab 1 in Lakeflow Designer, workspace `smbc-workshop`, 27 Oct 2026 (internal)

> **In progress.** This is the first hands-on run of Lab 1 in the Designer UI. It followed a fresh setup in the Azure FEVM workspace `smbc-workshop` (westus2). The 15 Oct tests ([report](test_report_2026-10-15.md)) went through the APIs and couldn't reach the canvas. Each finding lists the change to make. The changes will be applied in one pass when the test is finished, followed by the rebuild at the end of this report.
>
> **Applied on 28 Oct, in three passes:**
> 1. The corrected 9-step Lab 1 below went into guide §7, kit A.2, Appendix B and the cheat sheet.
> 2. The agenda moved to a 20-minute Lab 1. The workshop now runs 3 hours 15 minutes, and every segment after Lab 1 starts 20 minutes earlier.
> 3. Lab 1 was redesigned as 3 steps in 15 minutes, starting from a staging table rather than the raw files. A pre-built "starter canvas" was considered first and dropped: Designer files can only be made in the UI.
>
> **The redesign:**
> - **Setup:** `02` now builds `bronze.exposure_staging`. It holds the extracts joined to facilities, customers and FX rates, in USD and JPY, with the duplicates and bad rows still in. `03` checks that Lab 1's Unique and Guardrails steps on it reproduce `gold` exactly. `07` checks that the table exists and that attendees can read it.
> - **Attendees:** they build Source → Unique → Guardrails (Failed → quarantine Output) → Aggregate → Output → Schedule. Those are only operators confirmed in this test.
> - **Tested on 28 Oct in `smbc-workshop`:** the staging table, the lab's steps (as SQL) and the new `03` checks. The numbers are below.
> - **Materials updated:** guide §1, §2, §3.6, §4, §6, §7, A.2 and Appendix B; the slides (Lab 1 is now 7 slides); run of show §1, §4, §5, §6 and §8; the polls; the cheat sheet; the README. The workbook, lab notebooks, PDFs and walkthrough were rebuilt.
>
> Most of the corrected 9-step text below is superseded. Its formulas and joins live on in the staging table and in kit A.2's *Start from the raw files* stretch.
>
> **The new Lab 1's numbers** (all rows, at 30 Sep 2026; totals in USD m):
>
> | Step | Rows | Total |
> |---|---|---|
> | Source: `bronze.exposure_staging` | 76,166 | 28,287.1 |
> | After Unique on `facility_id` + `as_of_date`, latest `extract_ts`: removes 42 re-sent rows and 1,367 copies from 45 duplicate customer records | 74,757 | 27,459.0 |
> | After Guardrails: 474 rows fail, from 36 facilities (12 negative commitments, 9 maturities before start, 15 with no customer record) | 74,283 passed | 27,239.8, the checkpoint figure |
> | After Aggregate | 7,174 | 27,239.8 |
>
> **Still to do:**
> - **Run the new Lab 1 in Designer once:** step 3's Run all and Schedule haven't been confirmed in the UI yet.
> - **Commit and push,** then pull into the workspace's Git folder, so the daily job and `00` build the staging table. It was created by hand on 28 Oct.
> - **Finding 8:** the Lakeflow demo's canvas prompt and smoke test 3.
> - **The walkthrough:** update its Google Doc.

## Findings and changes to make

1. **Previews read only the first 1,000 rows of each source** (steps 3, 5, 6 and 7).
   - **Seen:** Unique on `counterparties` showed 1,000 → 992 rows instead of 2,370 → 2,325. Guardrails found 3 failed rows instead of 21. The first 1,000 balance rows contain no duplicates, so step 6's Unique shows no change at all.
   - **Change:** in step 1, attendees open the **Preview** menu in the canvas toolbar and select **All rows**; the dataset is small enough for this. Say that the lab's row counts are for all rows. Right-clicking an operator and choosing **Run up to this operator** also shows exact counts.
   - **Files:** guide §7, steps 1, 3, 5, 6 and 7; run of show §8 (expected results); slide *Lab 1 at a glance* and the step slides.
2. **The canvas Genie Code prompt failed in step 4.**
   - **Seen:** Genie Code reported that it doesn't have the configuration format for the request. Exact message: TBC.
   - **Change:** build the Prepare step by hand from three **Formula** actions with exact expressions (corrected step 4 below). Describing each formula in plain English in its expression editor becomes optional.
   - **Files:** guide §7 step 4 and A.2; slide *Lab 1 · Steps 3–4*.
3. **Formulas described in plain English came out wrong** (step 6).
   - **Change:** give the exact expression for every Formula in steps 4, 6, 7 and 8; Designer writes the description from it. The date formulas need `try_to_timestamp()`. It returns null for the format a value isn't written in, so `coalesce()` moves on to the other format, whereas `to_date()` can raise an error.
   - **Files:** guide §7 and A.2; slide *Lab 1 · Step 6*.
4. **Guardrails' Value range check includes its bounds** (step 5).
   - **Seen:** the check reads `committed_amount` ≥ 0, not > 0. On this data the result is the same 21 rows, because no facility has a commitment of exactly 0, but it isn't the rule.
   - **Change:** use an **Expression** check: `committed_amount > 0`.
   - **Files:** guide §7 step 5; slide *Lab 1 · Step 5*.
5. **Step 6 asks for a Formula on `fx_rates` without a Prepare step.** A Formula is an action inside a Prepare step.
   - **Change:** "add a **Prepare** step with one **Formula** action". Also say that the two balance formulas must stay in order: `month` uses the parsed `as_of_date`.
6. **The canvas Genie Code prompt for the joins didn't work** (step 7).
   - **Change:** build three Joins and a Prepare step by hand, in the order of the corrected step 7 below, so that each **Left unmatched** output shows what the guide describes.
   - **Files:** guide §7 step 7 and A.2; slide *Lab 1 · Step 7*; run of show §8.
7. **Step 8 doesn't say what to name the Aggregate's output columns.**
   - **Seen:** Aggregate asks for a name for each output column, and the guide doesn't give one.
   - **Change:** say the names must be `exposure_usd` and `exposure_jpy`. Otherwise the `utilisation_pct` formula and the checkpoint query don't work.
   - **Status:** the corrected step 8 below was confirmed in the UI on 28 Oct.
8. **Check everything else that relies on the canvas prompt,** and change it if smoke test 3 fails as well:
   - smoke test 3 (guide §3.8): *"Trim and upper-case the currency column"*;
   - the Lakeflow demo: run of show §4 (0:25), §6 and recording 1, and the slide *Live demo: what you'll see*;
   - the objective in guide §1, "use Genie Code to generate steps from plain English";
   - the contingency in run of show §5, which becomes the main path for steps 4 and 7.
9. **Join b is easy to connect to the wrong facilities output** (step 7).
   - **Seen:** Join b's right input came from the Guardrails **Passed** output instead of Join a's **Matched** output. Both carry facility rows, but only Join a adds the customer and group columns. Join b showed 74,485 matched rows instead of 74,283. `parent_group_id` was missing from the Aggregate's **Group by** list in step 8.
   - **Change:** in step 7, say explicitly that Join b takes Join a's **Matched** output, not Guardrails **Passed**. Add the first row of *Troubleshooting rows to add* below. To check the wiring, select an operator: the canvas highlights its lineage.
   - **Files:** guide §7 step 7 and Appendix B; run of show §8.
10. **Step 6's `month` column is easy to leave out, and nothing shows it's missing until step 8** (steps 6–8).
   - **Seen:** the balances Prepare step had only the `as_of_date` formula. Without `month`, Join c could join on currency alone, so every balance matched all 18 months of FX rates. Join c showed 1,337,094 matched rows instead of 74,283, and most group-months came out with `utilisation_pct` far above 100.
   - **Change:**
     - Step 6: list the two formulas as separate, numbered actions. Then add a check: the output has a new `month` column, so 2025-04-30 becomes 2025-04-01.
     - Step 7: say that Join c needs **two** join expressions. Add a check: Join c's **Matched** count must equal Join b's (74,283).
     - Add the last two rows of *Troubleshooting rows to add* below.
   - **Files:** guide §7 steps 6 and 7, and Appendix B; run of show §8; slides *Lab 1 · Step 6* and *Lab 1 · Step 7*.
11. **Still to find out:**
   - the exact error text in step 4;
   - the expressions Genie Code wrote in step 6;
   - whether dragging `group_limits.xlsx` onto the canvas worked (step 2).

## Corrected steps (drop-in text for guide §7)

**1.** *(add)* In the canvas toolbar, open **Preview** and select **All rows**, so each operator shows the row counts given in this lab. By default, previews process only the first 1,000 rows of each source.

**4. Clean the facilities (4 min).** After the `facilities` Source, add a **Prepare** step with three **Formula** actions. Each one overwrites the column it names. For each one, enter the column name, open the expression editor and paste the expression. Designer writes its plain-English description.

| Column | Expression |
|---|---|
| `currency` | `CASE upper(trim(currency)) WHEN 'US$' THEN 'USD' WHEN 'S$' THEN 'SGD' WHEN 'RMB' THEN 'CNY' ELSE upper(trim(currency)) END` |
| `start_date` | `coalesce(to_date(try_to_timestamp(start_date, 'yyyy-MM-dd')), to_date(try_to_timestamp(start_date, 'dd/MM/yyyy')))` |
| `maturity_date` | `coalesce(to_date(try_to_timestamp(maturity_date, 'yyyy-MM-dd')), to_date(try_to_timestamp(maturity_date, 'dd/MM/yyyy')))` |

Then open **Table of contents** in the left panel, select the operator, and expand **Generated code**.

**5. Quarantine bad rows with Guardrails (4 min).** Add **Guardrails** after the Prepare step, with these checks:
- **Expression:** `committed_amount > 0`. Don't use a Value range check here: it includes 0.
- **Expression:** `maturity_date >= start_date`
- **Not null:** `start_date`, `maturity_date`

Set **When a check fails** to **Warn and continue with passed rows**, and connect **Failed** to an **Output** that writes the table `quarantine_facilities` to your schema. 21 rows fail: 12 have a negative commitment and 9 mature before they start. 6,026 pass.

**6. Fix the balances and FX dates (3 min).**
- On `monthly_balances`, add a **Prepare** step with two **Formula** actions, in this order:
  1. `as_of_date` (overwrites the column): `coalesce(to_date(try_to_timestamp(as_of_date, 'yyyy-MM-dd')), to_date(try_to_timestamp(as_of_date, 'dd/MM/yyyy')))`
  2. `month` (new column): `trunc(as_of_date, 'MM')`

  Check the output: `as_of_date` is a date, and the new `month` column holds the first of the month (2025-04-30 → 2025-04-01). Join c needs `month` in step 7.
- Then add **Unique** → **Selected columns** `facility_id`, `as_of_date` → **Order by** `extract_ts` descending. Rows: 74,799 → 74,757.
- On `fx_rates`, add a **Prepare** step with one **Formula** action that creates the new column `rate_month`: `trunc(CAST(rate_date AS DATE), 'MM')`. Rates are dated on the last business day of the month, such as 2025-05-30. `rate_month` turns that into 2025-05-01, the same value as the balances' `month`.

**7. Join and convert (5 min).** Add three **Join** operators. Keep each one's default three outputs.

| Join | Left input | Right input | Join condition | Check |
|---|---|---|---|---|
| a | Guardrails **Passed** | `counterparties` after Unique | `counterparty_id` = `counterparty_id` | **Left unmatched:** 15 facilities whose customer isn't in the master yet (send them to a second quarantine Output if you like). **Matched:** 6,011 |
| b | `monthly_balances` after Unique | Join a **Matched**. Not Guardrails **Passed**: only Join a adds the customer and group columns | `facility_id` = `facility_id` | **Matched:** 74,283. **Left unmatched:** 474 balance rows, all from the 36 facilities held back |
| c | Join b **Matched** | `fx_rates` after Prepare | `currency` = `currency_code`; then **+ Add join expression**: `month` = `rate_month` | **Matched** must equal Join b's 74,283: a larger count means a join expression is missing. **Left unmatched** must be empty: `US$`, `S$` or `RMB` there means step 4 missed a mapping |

After Join c's **Matched** output, add a **Prepare** step with two **Formula** actions: `exposure_usd` = `drawn_amount * usd_rate` and `exposure_jpy` = `drawn_amount * jpy_rate`. At 30 Sep 2026 that's 4,092 rows, totalling USD 27,239.8m, which is already the checkpoint figure.

**8. Roll up to the group and compare with limits (3 min).**
- **Aggregate:** name the outputs `exposure_usd` (SUM of `exposure_usd`) and `exposure_jpy` (SUM of `exposure_jpy`). Expect 7,174 rows, one per group and month.
- **Join with the limits:** every group with balances has a limit, so **Matched** is 7,174 and **Left unmatched** is empty. **Right unmatched** is 1: Eastern Star Holdings (`GRP0130`) has a limit but no facilities.
- **`utilisation_pct` Formula:** `ROUND(100 * exposure_usd / group_limit_usd, 2)`.

## Expected counts with Preview → All rows

These replace the expected results in run of show §8.

| Where | Expected |
|---|---|
| Unique on `counterparties` (step 3) | 2,370 → 2,325 |
| Guardrails (step 5) | 21 failed, 6,026 passed |
| Unique on the balances (step 6) | 74,799 → 74,757 |
| Join a: Left unmatched, Matched | 15, 6,011 |
| Join b: Matched, Left unmatched | 74,283, 474 |
| Join c: Left unmatched, Matched | 0, 74,283 |
| Rows at 30 Sep 2026 after step 7 | 4,092, totalling USD 27,239.8m |
| Aggregate (step 8) | 7,174 |
| Join with the limits (step 8): Matched, Left unmatched, Right unmatched | 7,174, 0, 1 |

With the default 1,000-row preview, attendees see 1,000 → 992 in step 3, 3 failed rows in step 5 and no change in step 6.

## Troubleshooting rows to add (guide Appendix B and the helper briefing)

| Symptom | Likely cause | Fix |
|---|---|---|
| `parent_group_id` isn't in the Aggregate's **Group by** list (step 8) | Join b is connected to the Guardrails **Passed** output, so the customer columns never joined in. Join b's **Matched** shows 74,485 instead of 74,283 | Delete that connection and connect Join a's **Matched** output to Join b; set its condition again |
| `month` isn't available for Join c's join expression (step 7) | The balances Prepare step in step 6 is missing the `month` Formula, or it has another name | Add a Formula that creates `month`: `trunc(as_of_date, 'MM')` |
| `utilisation_pct` is over 100 (step 8). Nothing should be: the maximum is 94.0 | Check Join c's **Matched** count (all rows). **1,337,094:** no `month` = `rate_month` expression, so each balance matched all 18 months of rates. **1,039,962:** no `currency` = `currency_code` expression, so each balance matched all 14 currencies. **74,283:** USD and JPY are mixed up; the checkpoint total is then about 3,833,800 instead of 27,239.8 | Add the missing join expression. For a mix-up, make `exposure_usd` = `drawn_amount * usd_rate`, and give the SUM of `exposure_usd` the name `exposure_usd` in the Aggregate |

## Other items noted, 24–27 Oct

- **Guide version:** the guide's header still says "Version 0.1, draft of 15 October 2026".
- **Peter Butsch's title:** the planning notes flagged his title in guide §2 for a check before printing.
- **README claim:** `README.md` says the generator writes identical files on any Python version. The exception is `group_limits.xlsx`: `limit_approved_on` is a date when openpyxl is installed, and text otherwise. No answer depends on it.
- **15 Oct report:** [it](test_report_2026-10-15.md) still says the FEVM workspace expires on 28 Oct. The extension was approved on 15 Oct, and it now expires on 1 Jan 2027.
- **Public repo:** the GitHub repo is public. It includes `facilitator/` (answer key, quiz answers, internal test reports and the walkthrough), which the README marks as not for SMBC, and it names SMBC and its executives. Decide what to do before SMBC clones it.
- **Setup runbook:** the runbook written on 27 Oct could go into guide §4 and the README.

## When the test is finished

1. Make the changes above in `docs/SMBC_Workshop_Guide.md`, `slides/Workshop_Slides.md` and `facilitator/run_of_show.md`.
2. Rebuild the workbook, the lab notebooks and the PDFs: `.venv/bin/python handouts/build_handouts.py`. Add `--workspace-url` once SMBC's workspace URL is known.
3. Rebuild the walkthrough with `facilitator/build_walkthrough.py`, then update its Google Doc with `facilitator/publish_walkthrough.py`.
4. Pull the changes into the workspace's Git folder and re-run `06_deploy_dashboards_and_agents`, so that the Labs folder gets the new notebooks.
