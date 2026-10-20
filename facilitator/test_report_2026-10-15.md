# Test report: FEVM workspace `fe-vm-zh-serverless-ws`, 15 Oct 2026 (internal)

> **Since 20 Oct the setup needs no groups.** It assumes attendees have access to `smbc_workshop`, uses an existing SQL warehouse instead of creating one, shares with the workspace's built-in `users` group, and recognises facilitators by email. The results below are for the earlier, group-based version; the group and grant steps they describe no longer apply.

Everything was deployed with the repo scripts and tested through the APIs. A service principal, **meridian-ava**, stood in for a non-admin attendee: it has Workspace access and Databricks SQL access, and no admin rights.

## What's deployed

| Resource | Where |
|---|---|
| Catalog `smbc_workshop`: `raw` (volumes `landing`, `facilitator`), `checkpoint`, `ops`, plus one attendee schema | Tags `synthetic_data`, `workshop_date`, `RemoveAfter = 20261130` |
| Notebooks `00`–`08`, the tools in `setup/tools/`, the data scripts and the lab workbook notebook | `/Workspace/Users/zhihan.tan@databricks.com/smbc_workshop` |
| Serverless SQL warehouse **SMBC Workshop** (Small, 1–4 clusters, auto-stop 30 min), created by `06`; the dashboards and Genie Agents run on it | `/sql/warehouses/d77a3b548f320522` |
| Notebook **Lab workbook** (attendee copy, CAN READ for the attendee group), copied by `06` | `…/smbc_workshop/Lab workbook` |
| Dashboard **Credit Committee: APAC exposure (reference)** | `/dashboardsv3/01f1c87fd2241ba5b071f84d27491f1b/published` |
| Dashboard **SMBC Workshop: progress board** | `/dashboardsv3/01f1c87fd50c1c419be94a75eba9a44c/published` |
| Genie Agent **Credit Risk (reference)** | `/genie/rooms/01f1c87fefc61f9ea18ee130571bec81` |
| Genie Agent **Credit Risk (secured demo)**, shared CAN RUN with meridian-ava | `/genie/rooms/01f1c8817ae7196bb8c225765b8785f3` |

## Results

| Area | Test | Result |
|---|---|---|
| Setup | `01` → `02` → `03` as a serverless job | ✅ 18/18 checks pass; data generated in the workspace is byte-identical to the local run |
| Permissions (as attendee) | Read checkpoint tables and the landing volume; read the `.xlsx` with `read_files(format => 'excel')` | ✅ |
| | Read the facilitator volume; write to `checkpoint` | ✅ both denied, as intended |
| | Check-in insert, Lab 2 answer insert, write to own schema; own total matches the reference (USD 27,239.8m) | ✅ |
| Governance | Secured table and secured Genie Agent: facilitator sees 12 branches; attendee sees SIN only, with names masked | ✅ |
| Dashboards | All 11 dataset queries; definitions linted; create, update in place, publish | ✅ |
| Progress board | Shows the test attendee: 1 checked in, 1 Lab 1 finished, 1 correct Lab 2 answer | ✅ |
| Genie: Lab 2 questions | Closest to limits → Orchid 94%; June top 5 → Pacific Crown, then Orchid; arrears → SGN; Japanese question → correct, answered in Japanese; about 20 s per answer | ✅ |
| Genie: fiscal-year test | Without the instruction: "FY2026 H1" ✅, but "Q1 FY2026" → Jan–Mar ❌ and "FY2025" → calendar 2025 ❌. With the instruction, all ✅ | ✅ (Lab 2 step 4 rewritten to use the phrasings that fail) |
| Jobs | File-arrival trigger on a volume: run started 17 s after the file landed | ✅ (test job and volume deleted afterwards) |

## Problems found and fixed

1. **Governed tag policies** on the metastore rejected `data_classification = synthetic` (allowed: `u-nnpi`, `cui`, `pii`) and `workshop = smbc-2026-10-22` (allowed: `yes`, `no`). Tags are now applied one at a time; any rejected tag is skipped.
2. **Groups created through the workspace API are workspace-local.** Unity Catalog reports "Could not find principal", so every grant failed silently. The setup notebook now **stops with an explicit error** if any grant fails, and the guide (§3.5) says the groups must be **account-level**. For this test, grants went to meridian-ava and to Zhi Han directly, and the governance demo used the account group `meridian-admin` as the facilitator group.
3. **Arrears realism:** the planted arrears had been filled with many small facilities, so the share by count was 42.6% against 9.6% by exposure. The generator now picks typical-sized facilities: SGN is 13.0% by count and 9.6% by exposure. Every other planted answer is unchanged.
4. **Dashboard update path:** finding an existing dashboard by listing failed (paths lack the `/Workspace` prefix, and listings are paginated). It now looks up `<parent>/<name>.lvdash.json` directly.
5. **Genie isn't deterministic.** The same arrears question was answered by count in one run and by exposure in another, when Genie asked which we meant. The guide says so, and uses it as a curation lesson.

## Update, evening of 15 Oct: deploying from inside the workspace

Setup no longer needs a laptop or CLI. The dashboard and Genie Agent tools now run from a notebook as well. They were tested end to end as one serverless job: `01` → `06` → `07`, then `08` in dry-run mode. Two existing **account-level** groups stood in for the SMBC groups: `meridian-support` (attendees; it contains meridian-ava) and `meridian-admin` (facilitators).

| Notebook | Result |
|---|---|
| `01_setup_workspace` with account-level groups | ✅ All grants succeeded. Earlier they failed because the test groups were workspace-local |
| `06_deploy_dashboards_and_agents` | ✅ Created the serverless warehouse **SMBC Workshop** (Small, 1–4 clusters). All 11 dashboard queries passed. Both dashboards and both Genie Agents were updated in place (same IDs and links as above), and all 10 permissions applied. The dashboards and agents now run on the SMBC Workshop warehouse |
| `07_check_requirements` | ✅ 13/13 PASS, including "groups are account-level" and a live question to the reference agent (Orchid Group found in 19 s). A first run flagged a bug in the check itself: the Excel row count included the header row. Fixed, with `headerRows => 1` |
| `08_reset_or_teardown`, dry run | ✅ `reset_progress`, `drop_attendee_schemas` and `teardown` each list exactly the workshop's objects. The other Genie spaces in the workspace aren't touched |
| Lab workbook notebook, run as a serverless job | ✅ All 28 cells ran. The check-in and Lab 2 inserts worked, and the comparison cell worked out the schema from the login (`zhihan_tan`, a temporary copy of the reference) and returned USD 27,239.8m for both totals |
| `06` again, with the workbook in the repo | ✅ It copied **Lab workbook** into the folder and shared it (12 permissions in total) |
| **`00_master_setup`**, run as one serverless job with the stand-in groups and data generation on | ✅ The pre-flight checks passed. Then `01` (42 s), `02` (82 s), `03` (31 s), `05` (32 s), `06` (42 s) and `07` (52 s) ran in order: about 5 minutes in total, ending with "13 requirement checks, none failed". `05` is now a Python notebook that takes the two groups as settings, so the master can pass them on; it replaced the test-only variant used earlier |
| Japanese demo question for the analytics intro: 「2026年度第2四半期末時点の、計上店別の円建てエクスポージャーを教えてください。」 | ✅ Read as 30 Sep 2026 and answered from `exposure_jpy` by booking branch, in Japanese, in 24 s. It doesn't give away the Lab 2 answer, unlike the question used in Lab 2's stretch exercise |
| Renamed the setting from the fictional "Meridian Bank APAC" to a synthetic **SMBC APAC** lending book | ✅ The data files are byte-identical; only wording changed. After re-running `00_master_setup` (13 checks, none failed), neither Genie Agent, neither dashboard, the Lab workbook nor any Unity Catalog comment mentions Meridian. The `meridian-*` accounts are existing test principals in this workspace, not part of the materials |

## Not tested (needs a person in the UI on Mon 19 Oct)

- **Lakeflow Designer:** the canvas steps, Genie Code prompts, Guardrails, the Unique operator, Excel drag-and-drop from a laptop, and the Schedule button. These are UI-only; the underlying data and grants are verified.
- **Genie Code** in notebooks (agent mode, approvals, the legacy-SQL conversion), **AI-generated comments**, and **Lineage**.
- **Genie Agents agent mode**, companion Genie on dashboards, and **Genie One** chat and homepage pinning. There was no consumer-access-only test user.
- Timing of the Lab 1 core path for a first-time user.

## Before the dry run

- **Done (15 Oct, evening):** `08_reset_or_teardown` → `drop_attendee_schemas` emptied the progress board and dropped meridian-ava's schema and the temporary `zhihan_tan` schema. The workspace is ready for the dry-run setup in section 6 of the [run of show](run_of_show.md); run the same reset again after the dry run.
- For the test, `meridian-support` (attendees) and `meridian-admin` (facilitators) hold the workshop's grants and sharing. For the dry run, section 6 of the run of show switches them to `account users` and `users`.
- The FEVM workspace expires on **28 Oct**, and its 3 Oct extension request is still pending. The workshop on 22 Oct falls inside that window.
- On SMBC's workspace, run `00_master_setup` with the account-level groups. Its pre-flight checks stop before anything is created if a group is missing or workspace-local.
