# SMBC Data & AI Workshop

Materials for a hands-on workshop of 3 hours 15 minutes for SMBC APAC data analysts and data engineers: Lakeflow Designer and Jobs, AI/BI dashboards and Genie Agents, and Genie Code. All data is synthetic: a made-up SMBC APAC corporate lending book with fictional borrowers.

## The story

It's 8:00 on Monday at SMBC's APAC hub. The Credit Committee meets at 10:00 and wants the top counterparty-group exposures across all 12 booking branches, in USD and JPY. Behind it is the question the CDAO asks the room at the start of the workshop: *"Which client groups are closest to their limits, and why?"*

**The problem.** A group's exposure is spread across subsidiaries in several countries, booked in different branches and currencies, so no single system adds it up. Answering means four system extracts, the risk team's spreadsheet of limits and days of reconciliation. The extracts arrive with real-world problems: duplicate customers, hand-typed currency codes, two date formats, a re-sent branch extract, FX rates taken on the last business day, and facilities booked before their customer record existed. A group can creep towards its limit without any one report showing it. And the committee asks in the bank's own terms, such as *"the end of FY2026 H1"*, which a tool that assumes a calendar year gets wrong.

**The solution,** which attendees build themselves, one session at a time:
1. **Lab 1, automate it:** a Lakeflow Designer pipeline turns the raw extracts into one trusted exposure figure per group and month, with bad rows held back and every step traceable in Unity Catalog, and runs daily as a Lakeflow job.
2. **Lab 2, make it self-service:** an AI/BI dashboard answers the questions the committee always asks. A Genie Agent, taught the April-to-March fiscal year, answers new ones in English or Japanese and shows its SQL. Genie One puts both in front of business users.
3. **Genie Code, find out why:** explore what changed since April, split a group's rise into currency movements and new lending, and modernise a legacy SQL procedure.

Unity Catalog's permissions follow the data throughout, into the dashboard and the Genie Agent's answers. By the end, the room can answer the CDAO's question with numbers it can trace back to the source files. The findings are in the [answer key](facilitator/answer_key.md), for facilitators.

**The assets `setup/00_master_setup` creates for the story:**

| Asset | What it is | Its part in the story |
|---|---|---|
| Volume `smbc_workshop.raw.landing` | The four system extracts and the limits spreadsheet as the source systems deliver them, plus an optional ESG file | Monday morning's inbox |
| Schemas `bronze`, `silver` and `gold` | The extracts as tables, and `bronze.exposure_staging`: the extracts joined and converted, but not yet checked. Then the cleaned data, with rejected rows in `silver.quarantine_facilities`; and `gold.group_exposure` and `gold.facility_exposure` | The staging table is where Lab 1 starts. The trusted tables are Lab 1's reference answer, and the source for everything below |
| Dashboard **Credit Committee: APAC exposure (reference)** | Total exposure, the groups above 80% and 90% of their limits, the top 10 groups, the monthly trend, exposure by country, the five largest groups' utilisation, a watchlist and trade-finance arrears | The Monday report, on one page |
| Genie Agent **Credit Risk (reference)** | Plain-language questions over the gold tables, with the bank's definitions and fiscal-year rules, example SQL and benchmark questions | The questions nobody has asked yet |
| Genie Agent **Credit Risk (secured demo)** | The same data behind a Unity Catalog row filter and column mask | Proof that permissions follow the data into AI answers |
| Job **SMBC Workshop: daily data refresh** | Regenerates the extracts, then rebuilds and validates the tables, every day at 06:00 Singapore time | The report is ready every morning |
| Folder **Labs** | The five attendee notebooks; *00 Start here* opens with this story | Where attendees follow it |
| Dashboard **SMBC Workshop: progress board** | Check-ins and lab progress, live | For the facilitators, on the projector |

## What's in this repository

| Path | What it is | Share with SMBC? |
|---|---|---|
| [`docs/SMBC_Workshop_Guide.md`](docs/SMBC_Workshop_Guide.md) | The workshop document: agenda, **what must be enabled** (§3, for the SAG team), setup runbook, lab instructions, copy-paste kit | Yes |
| [`slides/Workshop_Slides.md`](slides/Workshop_Slides.md) | Slide content for the labs and hands-on segments, with speaker notes, in Markdown (Marp-compatible) to generate the deck from | Yes |
| [`labs/`](labs) | **The notebooks attendees open and run**, one per session: `00` start here (check-in), `01` Lab 1, `02` Lab 2, `03` Genie Code, `04` copy-paste kit and help. Built from the guide by `handouts/build_handouts.py`; `setup/06` copies them into a shared **Labs** folder | Yes |
| [`handouts/`](handouts) | Built by `build_handouts.py` from the guide: the participant **lab workbook** (PDF), the one-page **cheat sheet**, and PDFs of the guide and of §3 on its own | Yes |
| [`data/generate_data.py`](data/generate_data.py) | Builds the synthetic dataset and its answer key (standard library only; runs locally or in a Databricks notebook) | |
| [`data/validate_data.py`](data/validate_data.py) | Re-derives every planted answer from the files and checks the answer key (needs pandas) | |
| [`setup/`](setup) | Databricks notebooks. **`00_master_setup` creates everything in one run.** It runs the others in order: `01` workspace setup (schemas `raw`, `bronze`, `silver`, `gold`, `ops`), `02` the bronze, silver and gold reference tables (Lab 1 reference solution), `03` their validation, `05` governance demo, `06` dashboards, Genie Agents, the Labs folder and a job that rebuilds the data daily at 06:00 Singapore time, `07` requirement checks. Also: `04` progress-board queries, `08` reset or teardown | |
| [`setup/tools/`](setup/tools) | `dashboards.py`, `genie_agents.py` and `data_job.py`, used by `06`; they also run from a laptop through the Databricks CLI | |
| [`facilitator/`](facilitator) | Answer key, quiz, [run of show](facilitator/run_of_show.md) with the helper briefing, polls and survey, the [15 Oct test report](facilitator/test_report_2026-10-15.md), and the **full walkthrough** (facilitator guide, attendee guide, setup and presenter script in one Word document and [Google Doc](https://docs.google.com/document/d/1MLrO4tmZqqT-gfEZGgpPYdAxb23aSw9SOWwzn88GN90), built by `build_walkthrough.py` and `publish_walkthrough.py`) | **No** |

## Set up a workspace

As someone who can create a catalog and run queries on a pro or serverless SQL warehouse (no groups are needed):
1. Import this repo as a Git folder.
2. Open `setup/00_master_setup`. Every setting is optional: a SQL warehouse to use (blank picks one you can use), the other facilitators' emails, and a managed location only if creating the catalog asks for one.
3. Attach it to **Serverless** and click **Run all**. It checks the prerequisites, builds everything, and ends with the links and the requirement checks (about 5–15 minutes; safe to re-run).
4. Give attendees access to `smbc_workshop` with the three grants in §3.6 of the guide. Then do the other hand-run steps at the end of the notebook: the Genie One homepage, a Consumer-access demo user, and the smoke tests in §3.8.

## Rebuild the data and materials locally

```bash
# Generate and check the data (optional: 00_master_setup generates it in the workspace)
python3 data/generate_data.py --out data/output
uv venv .venv && uv pip install --python .venv/bin/python pandas openpyxl segno markdown pypandoc_binary lxml
.venv/bin/python data/validate_data.py --data data/output     # expect: 51 checks passed, 0 failed

# Rebuild the handouts after editing the guide (they use headless Google Chrome for the PDFs)
.venv/bin/python handouts/build_handouts.py --workspace-url https://<workspace>.azuredatabricks.net

# Rebuild the walkthrough and update its Google Doc (needs pypandoc_binary, and gcloud credentials with Drive access)
.venv/bin/python facilitator/build_walkthrough.py
CLOUDSDK_PYTHON=.venv/bin/python .venv/bin/python facilitator/publish_walkthrough.py --doc-id 1MLrO4tmZqqT-gfEZGgpPYdAxb23aSw9SOWwzn88GN90
```

The generator is deterministic (seed `20261022`): it produces identical files on any Python version, so the numbers in `facilitator/answer_key.md`, the quiz and the slides always match what participants see.
