# SMBC Data & AI Workshop · 22 October 2026

Materials for a 3.5-hour hands-on workshop for SMBC APAC data analysts and data engineers: Lakeflow Designer and Jobs, AI/BI dashboards and Genie Agents, and Genie Code. All data is synthetic: a made-up SMBC APAC corporate lending book with fictional borrowers.

| Path | What it is | Share with SMBC? |
|---|---|---|
| [`docs/SMBC_Workshop_Guide.md`](docs/SMBC_Workshop_Guide.md) | The workshop document: agenda, **what must be enabled** (§3, for the SAG team), setup runbook, lab instructions, copy-paste kit | Yes |
| [`slides/Workshop_Slides.md`](slides/Workshop_Slides.md) | Slide content for the labs and hands-on segments, with speaker notes, in Markdown (Marp-compatible) to generate the deck from | Yes |
| [`handouts/`](handouts) | Built by `build_handouts.py` from the guide: the participant **lab workbook** (PDF, and a notebook copy for the workspace), the one-page **cheat sheet**, and PDFs of the guide and of §3 on its own | Yes |
| [`data/generate_data.py`](data/generate_data.py) | Builds the synthetic dataset and its answer key (standard library only; runs locally or in a Databricks notebook) | |
| [`data/validate_data.py`](data/validate_data.py) | Re-derives every planted answer from the files and checks the answer key (needs pandas) | |
| [`setup/`](setup) | Databricks notebooks. **`00_master_setup` creates everything in one run.** It runs the others in order: `01` workspace setup, `02` checkpoint tables (Lab 1 reference solution), `03` validation, `05` governance demo, `06` dashboards, Genie Agents and lab workbook, `07` requirement checks. Also: `04` progress-board queries, `08` reset or teardown | |
| [`setup/tools/`](setup/tools) | `dashboards.py` and `genie_agents.py`, used by `06`; they also run from a laptop through the Databricks CLI | |
| [`facilitator/`](facilitator) | Answer key, quiz, [run of show](facilitator/run_of_show.md) with the helper briefing, polls and survey, the [15 Oct test report](facilitator/test_report_2026-10-15.md), and the **full walkthrough** (facilitator guide, attendee guide, setup and presenter script in one Word document and [Google Doc](https://docs.google.com/document/d/1MLrO4tmZqqT-gfEZGgpPYdAxb23aSw9SOWwzn88GN90), built by `build_walkthrough.py` and `publish_walkthrough.py`) | **No** |
| [`workshop-brainstorm.md`](workshop-brainstorm.md) | Planning notes, including account context | **No** (internal) |

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
