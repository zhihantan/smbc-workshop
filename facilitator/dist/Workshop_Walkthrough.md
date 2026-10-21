**All workshop data is synthetic.** The labs use a made-up SMBC APAC corporate lending book: every borrower, group, limit and balance is fictional. No SMBC data, systems or customer information is used at any point.

This document walks through the whole workshop, from setting up the workspace to the follow-up email. It's assembled from the workshop's source materials (the workshop guide, the run of show, the attendee workbook and the presenter notes), so it matches them.

| Part | What it covers | For | Share with |
|---|---|---|---|
| 1 | The workshop at a glance: goals, agenda, storyline | Everyone | Anyone |
| 2 | Facilitator guide: roles, countdown, timeline, fallbacks, helper briefing, answer key, quiz, follow-up | Facilitators and helpers | **Facilitators only: it contains the answers** |
| 3 | Attendee guide: setup, Lab 1, Lab 2, Genie Code, copy-paste kit, troubleshooting | Attendees | Attendees (no answers) |
| 4 | Workspace setup and requirements: what must be enabled, the setup notebooks, the pre-work email | SMBC's SAG team and workspace admins | SMBC's admins |
| 5 | Presenter script: slide-by-slide speaker notes | Presenters | Facilitators |

## Contents

- **[Part 1. The workshop at a glance](#part-1-the-workshop-at-a-glance)**
  - [1.1 At a glance](#11-at-a-glance)
  - [1.2 Agenda](#12-agenda)
- **[Part 2. Facilitator guide](#part-2-facilitator-guide)**
  - [2.1 Roles](#21-roles)
  - [2.2 Countdown](#22-countdown)
  - [2.3 Presenter laptop: tabs to open before the start](#23-presenter-laptop-tabs-to-open-before-the-start)
  - [2.4 Timeline](#24-timeline)
  - [2.5 If something goes wrong](#25-if-something-goes-wrong)
  - [2.6 Dry run in the Databricks test workspace](#26-dry-run-in-the-databricks-test-workspace)
  - [2.7 Executive briefing: notes for Richard and Peter](#27-executive-briefing-notes-for-richard-and-peter)
  - [2.8 Helper briefing (print one per helper)](#28-helper-briefing-print-one-per-helper)
  - [2.9 Facilitator moments in the labs](#29-facilitator-moments-in-the-labs)
  - [2.10 Answer key](#210-answer-key)
  - [2.11 Quiz](#211-quiz)
  - [2.12 Polls and survey](#212-polls-and-survey)
  - [2.13 After the workshop](#213-after-the-workshop)
- **[Part 3. Attendee guide](#part-3-attendee-guide)**
  - [Before you start](#before-you-start)
  - [1. The scenario and the data](#1-the-scenario-and-the-data)
  - [2. Lab 1: Build the trusted exposure table](#2-lab-1-build-the-trusted-exposure-table)
  - [3. Lab 2: Credit Committee in 30 seconds](#3-lab-2-credit-committee-in-30-seconds)
  - [4. AI-assisted development with Genie Code](#4-ai-assisted-development-with-genie-code)
  - [5. Resources](#5-resources)
  - [Appendix A: Copy-paste kit](#appendix-a-copy-paste-kit)
  - [Appendix B: Troubleshooting](#appendix-b-troubleshooting)
- **[Part 4. Workspace setup and requirements](#part-4-workspace-setup-and-requirements)**
  - [3. Workspace requirements: what must be enabled](#3-workspace-requirements-what-must-be-enabled)
  - [4. Setting up the workspace](#4-setting-up-the-workspace)
  - [5. Participant pre-work](#5-participant-pre-work)
- **[Part 5. Presenter script](#part-5-presenter-script)**
  - [Welcome and check-in · 0:00](#welcome-and-check-in--000)
  - [Data engineering with Lakeflow · 0:25](#data-engineering-with-lakeflow--025)
  - [Lab 1 · 0:45](#lab-1--045)
  - [Self-service analytics · 1:40](#self-service-analytics--140)
  - [Lab 2 · 2:00](#lab-2--200)
  - [Genie Code · 2:55](#genie-code--255)
  - [Quiz and close · 3:10](#quiz-and-close--310)

# Part 1. The workshop at a glance

## 1.1 At a glance

| | |
|---|---|
| **Length** | 3 hours 35 minutes |
| **Who** | SMBC APAC data analysts and data engineers (headcount TBC) |
| **Format** | Short demos, two 40-minute hands-on labs, a Genie Code segment, and a quiz |
| **Where people work** | A dedicated workshop workspace (Azure Databricks) with serverless compute |
| **Data** | A synthetic SMBC APAC corporate lending book, with fictional borrowers |
| **What people take away** | A pipeline, a dashboard and a Genie Agent they built themselves, plus a learning path |

**By the end of the session, each participant can:**

- build a data-preparation pipeline visually in **Lakeflow Designer**, use **Genie Code** to generate steps from plain English, and schedule it with **Lakeflow Jobs**;
- build an **AI/BI dashboard** and a **Genie Agent**, teach it business rules such as the April-to-March fiscal year, and test whether it answers correctly;
- use **Genie Code** to explore data, generate SQL and Python, explain legacy code, and stay in control of what it runs;
- explain how **Unity Catalog** governs all of it: lineage, data-quality checks, and row-level security.

**One storyline runs through the day.** It's 8am on Monday at the APAC hub. The Credit Committee wants the top counterparty-group exposures across all booking branches, in USD and JPY, by 10am. Today that means four system extracts, a spreadsheet of limits, and days of reconciliation. In Lab 1 participants automate it, in Lab 2 they make it self-service, and in the Genie Code segment they investigate what they found.

---

## 1.2 Agenda

Times are relative to the start time.

| Time | Length | Segment | What happens |
|---|---|---|---|
| 0:00 | 10 min | **Welcome and environment check** | Run the one-line check-in query; a one-question poll |
| 0:10 | 15 min | **Executive briefing** | Opening by Richard Lowe (APAC CDAO) and Peter Butsch (Head of Emerging Enterprises & Digital Natives, Databricks) |
| 0:25 | 20 min | **Data engineering: Lakeflow** | Low-code ETL with Lakeflow Designer and Lakeflow Jobs, and AI-assisted pipeline creation (mostly live demo) |
| 0:45 | 40 min | **Lab 1** | Build the trusted exposure table |
| 1:25 | 15 min | Break | |
| 1:40 | 20 min | **Self-service analytics** | AI/BI dashboards, Genie Agents, and Genie One (formerly Databricks One) |
| 2:00 | 40 min | **Lab 2** | Build a Credit Committee dashboard and a Genie Agent |
| 2:40 | 15 min | Break | |
| 2:55 | 15 min | **AI-assisted development** | Genie Code: explore data, generate SQL and Python, explain results, and iterate safely |
| 3:10 | 15 min | **Quiz** | On phones, with Databricks swag for the winners |
| 3:25 | 10 min | **Next steps and resources** | Learning materials and upcoming events |

**Product names changed in 2026.** Genie spaces are now **Genie Agents**, and Databricks One is now **Genie One**. This guide uses the current names, which match the product and the documentation participants will see.

**Two logistics suggestions:**
- Open the doors 30 minutes early with a helper desk for login problems, so the 10-minute check-in slot only confirms everyone is in.
- Consider swapping the last two slots so the prize-giving closes the session, and make the feedback survey the raffle ticket.

---

# Part 2. Facilitator guide

> **Facilitators and helpers only.** This part contains the answer key and the planted findings. Don't share it with attendees.

## 2.1 Roles

| Role | Who | Does |
|---|---|---|
| Host and timekeeper | TBC | Opens, runs the transitions, owns the clock |
| Lakeflow presenter | TBC | Data engineering intro and demo; leads Lab 1 |
| Analytics presenter | TBC | Self-service analytics intro and demo; leads Lab 2 and the governance moment |
| Genie Code presenter | TBC | AI-assisted development segment |
| Quiz host | TBC | The Slido quiz and prizes |
| Helpers | About 1 per 8–10 attendees | Watch for red cards; know the helper briefing (section 8) |
| Check-in desk | 1–2 helpers, from 30 minutes before the start | Sign-in problems |
| Executive speakers | Richard Lowe (SMBC) and Peter Butsch (Databricks) | Executive briefing; Richard awards the prizes |
| SMBC IT contact | TBC | On call for SSO, proxy and network problems |

## 2.2 Countdown

| When | Task | Status |
|---|---|---|
| Done | Dataset generated and validated. Reference tables, dashboards and Genie Agents built and tested in the Databricks test workspace (test report) | ✅ |
| A week before | Send guide §3 to the SAG team and workspace admins. Confirm the start time, headcount and DA/DE split, venue Wi-Fi, whether Slido is allowed, and whether recording is allowed | ☐ |
| 3 days before | Internal dry run (section 6) | ☐ |
| 2 days before | In SMBC's workspace, run `setup/00_master_setup` (guide §4). It should finish with "none failed" and name the SQL warehouse to give attendees. Then grant attendees access to `smbc_workshop` (guide §3.6), run `07_check_requirements` again, and set up the Genie One homepage (guide §3.3) | ☐ |
| 2 days before | Smoke tests (guide §3.8) on an SMBC laptop, on the SMBC network, with 2–3 SMBC volunteers | ☐ |
| 2 days before | Send the pre-work email (guide §5), with the workspace URL and warehouse name filled in. Agree the executive briefing with Richard and Peter (section 7) | ☐ |
| The day before | Freeze the content. Set up the quiz (Quiz (Part 2)), the polls and the survey (Polls and survey (Part 2)) in Slido, and test them on a phone | ☐ |
| The day before | Print a cheat sheet per person plus spares (`handouts/dist/Cheat_Sheet.pdf`, rebuilt with the real workspace URL), and red/green cards. Record the fallback videos (section 5) | ☐ |
| The day before | Late registrations: check they can sign in and have access to `smbc_workshop`; their check-in creates their schema. Then run `08_reset_or_teardown` → `reset_progress` so the board starts at zero | ☐ |
| Day, −90 min | Arrive. Test the projector, clicker and Wi-Fi. Open the presenter tabs (section 3). Start the workshop's SQL warehouse (the one `00_master_setup` named) and, if you manage it, lengthen its auto-stop for the day. In **Jobs & Pipelines**, check that the 06:00 run of **SMBC Workshop: daily data refresh** succeeded | ☐ |
| Day, −30 min | Doors open; check-in desk opens | ☐ |

## 2.3 Presenter laptop: tabs to open before the start

1. The slides, generated from `slides/Workshop_Slides.md`, in presenter view.
2. The **progress board** (published view). It's on the projector during labs and breaks.
3. The **reference dashboard** (published view).
4. The two Genie Agents: **Credit Risk (reference)** and **Credit Risk (secured demo)**.
5. Lakeflow Designer: a new visual data prep for the demo, with `group_limits.xlsx` downloaded to the desktop.
6. A notebook with the Genie Code prompts (guide A.8) and the legacy procedure (A.9) ready to paste.
7. Genie One (`<workspace URL>/one`), signed in as the Consumer-access demo user, in a separate browser profile.
8. Slido, signed in, with the polls and the quiz ready.

## 2.4 Timeline

| Time | Segment | On the projector | What happens | Move on when |
|---|---|---|---|---|
| −0:30 | Doors open | Welcome slide | Check-in desk solves sign-in problems | |
| 0:00 | **Welcome and check-in** (10) | Welcome slide, then the progress board | Host welcomes; everyone runs the check-in line; the poll runs (*"What do you use most today?"*). Anyone not checked in by 0:05 gets a helper. | 0:10, or 90% checked in |
| 0:10 | **Executive briefing** (15) | Briefing slides | Richard 5 min, Peter 5 min, fireside 5 min (section 7). Richard asks *the CDAO's question*. | 0:25, hard stop |
| 0:25 | **Lakeflow** (20) | At most 8 min of slides, then live Designer | The demo: drag `group_limits.xlsx` onto the canvas → one Genie Code prompt → preview → open the generated code | 0:45 |
| 0:45 | **Lab 1** (40) | *Lab 1 at a glance*, then the progress board | Pairs, engineer driving. **0:55:** most pairs have their sources in (step 2). **1:10:** the core path should be done; call "stretch or catch up". **1:15:** anyone not past step 5 switches to the gold reference tables. **1:22:** facilitator close (lineage, and the USD 366.9m reveal). | 1:25 |
| 1:25 | Break (15) | Progress board, "back at" slide | Helpers sort out anyone stuck | 1:40 |
| 1:40 | **Self-service analytics** (20) | Slides, then live | The demo: reference dashboard → Genie One as the Consumer-access user → a question in English, then in Japanese → open the SQL | 2:00 |
| 2:00 | **Lab 2** (40) | *Lab 2 at a glance*, then the progress board | **2:10:** dashboards published. **2:15:** Genie Agents created. **2:24:** the fiscal-year test done. **2:25:** answers submitted (the board shows them). **2:25–2:35:** stretch; Stump the Genie entries go to a facilitator. **2:35:** governance moment, facilitator and a volunteer (3 min). **2:38:** the fiscal-year debrief slide. | 2:40 |
| 2:40 | Break (15) | Progress board | Shortlist 2–3 dashboards for the *Best dashboard* vote; pick *Best Stump the Genie* | 2:55 |
| 2:55 | **Genie Code** (15) | Live notebook | Explore → generate (the FX split) → explain and convert the legacy procedure → the safety beat | 3:10 |
| 3:10 | **Quiz** (15) | Slido quiz | 12 questions; after each one, say its teaching point (Quiz (Part 2)). Richard awards: quiz top three, *Best Stump the Genie*, *First to finish Lab 1* (the progress board's "First to finish" table), *Best dashboard* (Slido vote). | 3:25 |
| 3:25 | **Next steps** (10) | Closing slides | What you found today; resources; the 30-day Genie Agent challenge; the feedback survey, which is the raffle ticket | 3:35 |

If the organisers swap the last two slots (guide §2), the prizes close the session and the raffle draw comes straight after the survey.

## 2.5 If something goes wrong

| If | Then |
|---|---|
| SSO or the proxy blocks a few laptops | Pair them with a neighbour; the check-in desk escalates to SMBC IT |
| Nobody can reach the workspace | Present from the Databricks test workspace; people follow on the projector in pairs; play the recordings |
| Designer's Genie Code prompts don't respond | Build the step by hand from the actions in Lab 1, step 4, and check cross-Geo processing (guide §3.2) |
| Genie Agents error or are slow | Lab 2 carries on with the dashboard, Genie in pairs; check cross-Geo processing and partner-powered AI (`07_check_requirements` tests both) |
| Queries queue on the warehouse | Raise its maximum clusters in SQL Warehouses, or ask its owner to |
| The daily data job's 06:00 run failed (you get an email) | Open the run to see which task failed. If it's `generate_data`, the tables weren't touched. Otherwise fix the cause and click **Run now**, or run `00_master_setup` again; `07_check_requirements` confirms the tables |
| Lab 1 overruns | At 1:15 move everyone to the gold reference tables; Lab 2 doesn't depend on Lab 1 |
| AI output differs from the rehearsal | Say so: it's why you check the SQL. Show the recording if the difference matters |
| Slido is blocked on the SMBC network | Phones on mobile data; or read the questions from `quiz.md` and take answers by show of hands |

**Recordings to make the day before**, in SMBC's workspace if possible, otherwise in the test workspace:
1. The Designer demo (Excel → prompt → preview → generated code).
2. Lab 1's core path end to end (speed it up).
3. Genie One as a business user, including the Japanese question.
4. The Genie Code prompts (A.8) and the legacy-SQL conversion (A.9).
5. A Genie Agents agent-mode answer.

## 2.6 Dry run in the Databricks test workspace

**Goal:** time the labs with first-time users, and test what the 15 Oct tests couldn't reach through the APIs (the test report's "Not tested" list).

The set-up steps for the Databricks test workspace are in the run of show in the workshop repository.

**Time and test:**

| Area | What to check |
|---|---|
| Lab 1 | Core path per pair (target 25 min). Every Designer step: Source browse, Unique (2,370 → 2,325), the Genie Code prompt for Prepare, Guardrails (21 failed), Join outputs (Left unmatched), Aggregate, Output, Schedule. Excel drag-and-drop. Version history and Generated code. |
| Lab 2 | The AI-assisted chart prompt, Genie Agent creation and its suggested descriptions, the fiscal-year test, agent mode, Export to metric view |
| Genie One | Homepage pinning and welcome message; chat; the business-user view (needs a user with Consumer access only) |
| Genie Code | The A.8 prompts; the approval setting; *"don't run any code"*; revision history |
| Catalog Explorer | AI-suggested descriptions; lineage on `gold_group_exposure` |
| Load | 10 people asking 3 Genie questions in the same minute |

**Afterwards:**
- Note every difference between the UI and the guide, then fix the guide and rebuild the handouts (`handouts/build_handouts.py`).
- Run `08_reset_or_teardown` → `drop_attendee_schemas` again.

## 2.7 Executive briefing: notes for Richard and Peter

Agree these two days before the workshop. Fifteen minutes in three parts.

- **Richard (5 min):** why self-service *with guardrails* matters for the APAC Data Hub. Then he asks the room **the CDAO's question**: *"Which client groups are closest to their limits, and why?"* The room answers it by the end of the day.
- **Peter (5 min):** Databricks' commitment to SMBC: enablement and follow-up, such as the proposed 30-day Genie Agent challenge. *(Peter to provide content.)*
- **Fireside (5 min), two prepared questions:**
  - *"What does good look like by FY-end, March 2027?"*
  - *"Where should AI help, and where must a human stay in the loop?"* This sets up the governance thread for the day.
- Ask Richard to come back at **3:10** to award the prizes.
- Expect questions about where the AI features process data. Answer from guide §3.9; don't improvise.

## 2.8 Helper briefing (print one per helper)

**Expected results:**

| Check | Expected |
|---|---|
| Customer master after Unique (Lab 1, step 3) | 2,325 rows, from 2,370 |
| Guardrails failed rows (step 5) | 21 |
| Facilities with no customer record (Left unmatched, step 7) | 15 |
| Balances after Unique (step 6) | 74,757 rows, from 74,799 |
| FX join Left unmatched (step 7) | Empty |
| Total exposure at 30 Sep 2026 (checkpoint query) | USD 27,239.8m |
| Lab 2 checkpoint answer | Orchid Group, 94.0% at 30 Sep 2026 |

**The usual problems** (guide Appendix B has the full list):
- **Total too high:** duplicates weren't removed (step 3, or the Bangkok re-send in step 6).
- **Total too low:** only one date format was parsed, or `US$`, `S$` or `RMB` wasn't mapped. Look at the join's Left unmatched output.
- **Months missing after the FX join:** joined on the exact date; join on currency and month.
- **Permission error on Output:** the output location isn't the person's own schema.
- **Permission error at check-in:** the person doesn't have access to `smbc_workshop` yet (guide §3.6); tell the lab lead.
- **Genie reads FY2026 as a calendar year:** that's the point of step 4; add the fiscal-year instruction (A.4).

**Catching up:** anyone can carry on from the reference tables in `smbc_workshop.gold`.

**Escalation:** helper → lab lead → SMBC IT (sign-in and network).

**Don't** show participants the answer key, or tell them the planted findings before the reveals.

## 2.9 Facilitator moments in the labs

These parts of the labs are run by a facilitator and aren't in the attendee guide.

### Lab 1: facilitator close (3 min)

- Open **Catalog Explorer → `gold_group_exposure` → Lineage** and trace it back through every step to the raw files. That's lineage evidence nobody had to draw by hand.
- Then reveal what the duplicate extract would have done to the Credit Committee pack.

---

### Lab 2: the fiscal-year test, what we saw in testing

> **What we saw when testing (15 Oct).** Without the instruction, Genie treated Q1 FY2026 as January–March 2026 and answered *"70.0%, not near its limit"*, and it treated FY2025 as January–December 2025. Yet it guessed *"end of FY2026 H1"* correctly as 30 September. After adding the instruction, Q1 FY2026 ends on 30 June (79.0%), and FY2025 runs from April 2025 to March 2026. **The lesson: without explicit rules the AI guesses, and it doesn't guess the same way every time.** That's why curation and benchmarks matter before anyone shares an agent with a credit committee.

### Lab 2: governance moment (3 min)

A demo Genie Agent sits on a copy of the facility table that has a **row filter** (Singapore branch only, unless you're a facilitator) and a **column mask** on borrower names. A facilitator and a volunteer ask the same question and get different, correct answers: the Genie Agent inherits Unity Catalog permissions rather than bypassing them.

---

## 2.10 Answer key

Generated by `data/generate_data.py` (seed 20261022) and checked by `data/validate_data.py`. Every number below comes from the files participants use, after the Lab 1 cleaning rules. **Don't share this with participants.**

### The story in five numbers

1. **Orchid Group** (`GRP0137`) uses **71%** of its USD 1,500.0m limit at 30 Apr 2026 and **94%** at 30 Sep 2026. It first passes 90% in **September 2026**; no other group goes above 84.2% in any month.
2. It is invisible one subsidiary at a time: the largest of its 14 subsidiaries ranks only **#24** among counterparties.
3. Of the USD 345.0m rise since April, **25% is FX** (USD 86.2m) and the rest is new drawdowns (USD 258.8m). Measured on April balances instead, FX is 19%. Four subsidiaries account for 94% of the new drawdowns.
4. The re-loaded BKK TRADE_FIN extract for 2026-09-30 overstates total exposure by **USD 366.9m** unless duplicates are removed.
5. **The fiscal-year trap:** at the end of calendar H1 (30 Jun 2026) no group is over 90%; at the end of FY2026 H1 (30 Sep 2026): **Orchid Group**.

### Totals at 30 Sep 2026

| Measure | Value |
|---|---|
| Total exposure | USD 27,239.8m (JPY 3,833.8bn) |
| Overstated if the re-run extract isn't de-duplicated | USD 366.9m |
| Overstated if duplicate counterparties fan out in joins | USD 456.2m |
| Held back by quarantine | USD 219.2m |
| Silently lost if only ISO dates are parsed | USD 4,789.2m |

### Top 5 groups by exposure

| Rank | 30 Jun 2026 (calendar H1) | 30 Sep 2026 (FY2026 H1) |
|---|---|---|
| 1 | Pacific Crown Holdings: USD 1,274.3m, 53.1% | Orchid Group: USD 1,410.0m, 94.0% |
| 2 | Orchid Group: USD 1,185.0m, 79.0% | Pacific Crown Holdings: USD 1,304.2m, 54.3% |
| 3 | Harmony Partners: USD 857.1m, 39.0% | Harmony Partners: USD 806.6m, 36.7% |
| 4 | Zenith Partners: USD 621.9m, 34.5% | Lucky Cloud Corporation: USD 630.4m, 28.7% |
| 5 | Lion Gate Corporation: USD 510.5m, 31.9% | Garuda Capital: USD 561.8m, 33.0% |

### Orchid Group by month

| Month end | Exposure | Utilisation |
|---|---|---|
| 2025-04-30 | USD 930.0m | 62.0% |
| 2025-05-31 | USD 942.0m | 62.8% |
| 2025-06-30 | USD 954.0m | 63.6% |
| 2025-07-31 | USD 966.0m | 64.4% |
| 2025-08-31 | USD 978.0m | 65.2% |
| 2025-09-30 | USD 990.0m | 66.0% |
| 2025-10-31 | USD 1,002.0m | 66.8% |
| 2025-11-30 | USD 1,014.0m | 67.6% |
| 2025-12-31 | USD 1,026.0m | 68.4% |
| 2026-01-31 | USD 1,035.0m | 69.0% |
| 2026-02-28 | USD 1,042.5m | 69.5% |
| 2026-03-31 | USD 1,050.0m | 70.0% |
| 2026-04-30 | USD 1,065.0m | 71.0% |
| 2026-05-31 | USD 1,110.0m | 74.0% |
| 2026-06-30 | USD 1,185.0m | 79.0% |
| 2026-07-31 | USD 1,260.0m | 84.0% |
| 2026-08-31 | USD 1,335.0m | 89.0% |
| 2026-09-30 | USD 1,410.0m | 94.0% |

### Orchid subsidiaries at 30 Sep 2026

| Subsidiary | Country | Exposure | New drawdowns since April | Rank among all counterparties |
|---|---|---|---|---|
| Orchid Land (Thailand) Co., Ltd. *(growth driver)* | TH | USD 163.5m | USD 67.4m | 24 |
| PT Orchid Energi Indonesia *(growth driver)* | ID | USD 156.9m | USD 64.7m | 26 |
| Orchid Land Vietnam JSC *(growth driver)* | VN | USD 142.1m | USD 63.9m | 31 |
| Orchid Logistics (Thailand) Co., Ltd. | TH | USD 118.9m | USD 3.3m | 40 |
| PT Orchid Properti Indonesia *(growth driver)* | ID | USD 118.9m | USD 47.1m | 39 |
| Orchid Industries (Thailand) Co., Ltd. | TH | USD 106.6m | USD 2.8m | 47 |
| Orchid Holdings Pte. Ltd. | SG | USD 105.8m | USD 0.5m | 48 |
| Orchid Logistics Pte. Ltd. | SG | USD 97.5m | USD 5.8m | 56 |
| Orchid Industries India Private Limited | IN | USD 85.9m | USD -0.0m | 65 |
| Orchid Energy Vietnam JSC | VN | USD 74.3m | USD 1.9m | 77 |
| Orchid Infrastructure India Private Limited | IN | USD 74.3m | USD -0.5m | 76 |
| Orchid Consumer (Thailand) Co., Ltd. | TH | USD 59.5m | USD -0.1m | 97 |
| PT Orchid Logistik Indonesia | ID | USD 59.5m | USD 1.8m | 96 |
| Orchid Capital Pte. Ltd. | SG | USD 46.3m | USD 0.2m | 123 |

### Planted data-quality problems

- **Duplicate counterparty rows:** 45 exact copies in `counterparties.csv`.
- **Currency codes needing cleanup:** `AUD ` ×2, `HKD ` ×11, `IDR ` ×5, `INR ` ×6, `JPY ` ×2, `KRW ` ×2, `MYR ` ×9, `PHP ` ×1, `RMB` ×2, `S$` ×8, `THB ` ×6, `TWD ` ×3, `US$` ×39, `USD ` ×25, `Usd` ×37, `VND ` ×8, `aud` ×7, `hkd` ×7, `idr` ×2, `inr` ×4, `jpy` ×3, `krw` ×2, `myr` ×4, `php` ×3, `sgd` ×9, `thb` ×3, `twd` ×1, `usd` ×29, `vnd` ×7. Designer joins ignore case and surrounding spaces by default, so only `US$`, `S$` and `RMB` show up in the join's unmatched output.
- **Quarantine:** MATURITY_BEFORE_START ×9, NON_POSITIVE_COMMITMENT ×12, UNKNOWN_COUNTERPARTY ×15.
- **Re-run extract:** 42 duplicate balance rows (BKK TRADE_FIN extract for 2026-09-30), identical except for a later `extract_ts`. Deduplicate on `facility_id` + `as_of_date`, keeping the latest.
- **Dates:** 13,851 balance rows and 1,441 facility rows (trade-finance system) use DD/MM/YYYY.
- **FX dated on the last business day:** an exact-date join loses 2025-05-31, 2025-08-31, 2025-11-30, 2026-01-31, 2026-02-28, 2026-05-31. Join on currency and month instead.

### Arrears creep: SGN (Ho Chi Minh City) trade finance, % of exposure more than 30 days past due

2026-03: 1.1% → 2026-04: 2.5% → 2026-05: 4.0% → 2026-06: 5.5% → 2026-07: 6.7% → 2026-08: 9.3% → 2026-09: 9.6%
(whole book at 30 Sep 2026: 0.4%)


## 2.11 Quiz

15 minutes on phones, as a Slido quiz: enter the 12 questions below, about 20 seconds each, then prizes. The answers come from `answer_key.md`, which `data/validate_data.py` checks against the data. If the data is regenerated with a different seed, re-check questions 1–6.

After each question, say the one-line **teaching point**: that's what people remember.

| # | Question | Options (✅ = correct) | Teaching point |
|---|---|---|---|
| 1 | Which counterparty group passed 90% of its limit? | A. **Orchid Group** ✅ · B. Pacific Crown Holdings · C. Harmony Partners · D. No group did | Only visible once subsidiaries are rolled up to their parent group. |
| 2 | At the end of FY2026 H1, how much of its limit was Orchid Group using? | A. 71% · B. 79% · C. 89% · D. **94%** ✅ | 71% in April, 79% in June, 94% in September: it crossed 90% last month. |
| 3 | When does FY2026 H1 end? | A. 30 Jun 2026 · B. **30 Sep 2026** ✅ · C. 31 Dec 2026 · D. 31 Mar 2027 | Without the rule, Genie read "Q1 FY2026" as January–March and called Orchid "not near its limit" at 70%. One instruction fixes it. |
| 4 | Where does Orchid's largest subsidiary rank among all borrowers? | A. #1 · B. #5 · C. **#24** ✅ · D. #100 | Concentration risk hides at legal-entity level. |
| 5 | Roughly how much of Orchid's rise since April is FX? | A. ~5% · B. **~25%** ✅ · C. ~50% · D. ~75% | Three-quarters is new borrowing, mostly by four subsidiaries. That's a credit conversation, not just a currency one. |
| 6 | By how much would the re-sent Bangkok extract have overstated exposure? | A. Nothing: the spreadsheet was right · B. USD 37m · C. **USD 367m** ✅ · D. USD 3.7bn | One `Unique` step, keeping the latest `extract_ts`, prevented it. |
| 7 | In Lakeflow Designer, which operator splits rows into *Passed* and *Failed*? | A. Filter · B. Unique · C. **Guardrails** ✅ · D. Combine | Failed rows keep a reason, which is your data-quality evidence. |
| 8 | What sits underneath every Lakeflow Designer operator? | A. Nothing: it's a black box · B. An Excel macro · C. A screenshot · D. **Code you can view, version in Git and schedule** ✅ | No-code without shadow IT. |
| 9 | What's the new name for Databricks One? | A. **Genie One** ✅ · B. Lakehouse One · C. Databricks Home · D. AI/BI Hub | And Genie spaces are now Genie Agents. |
| 10 | A user without `SELECT` on a table asks a Genie Agent about it. What happens? | A. **Genie returns an empty response** ✅ · B. Genie uses the author's access · C. Genie shows a sample · D. Genie emails an admin | Data access is always evaluated as the person asking; row filters and masks apply too. |
| 11 | By default, what decides whether Genie Code can run an action? | A. Nothing: it runs everything · B. A workspace admin, manually · C. It never runs code · D. **An AI classifier that approves actions within your request** ✅ | You can switch to approving every action yourself, or say "don't run any code". |
| 12 | Which branch's trade-finance arrears crept from about 1% to about 10% since April? | A. SIN · B. BKK · C. **SGN** ✅ · D. HKG | The second finding: ask Genie *"which booking branch has the highest share of trade finance in arrears?"* |

**Optional round: "Genie or human?"** During the dry run, save two SQL queries that answer the same question, one written by Genie and one by a facilitator. Show both and ask which is Genie's. It's usually hard to tell, which makes the point that you should check the SQL rather than trust the author.

**Prizes:**
- Quiz top three
- *Best Stump the Genie* (facilitators pick)
- *First to finish Lab 1* (the "First to finish" query in `setup/04_progress_board`)
- *Best dashboard* (a Slido vote of 2–3 shortlisted dashboards)


## 2.12 Polls and survey

Set these up **the day before the workshop**: polls and Q&A in Slido, and the survey in Slido or Microsoft Forms, whichever SMBC allows. The quiz runs in Slido too: enter the 12 questions from Quiz (Part 2) as a Slido quiz.

### During the day

| When | Type | Question | Options |
|---|---|---|---|
| 0:00, while people sign in | Poll, results shown live | What do you use most today? | Excel · SQL · Python · Power BI · ADF or Synapse · Something else |
| All day | Q&A ("parking lot") | Questions that are off the current topic | Answer them in the recap email |
| 2:55, before Genie Code | Open text | What's one question you wish you could ask your data? | Free text. The answers seed the 30-day Genie Agent challenge |
| 3:10, during the quiz | Vote | Best dashboard | The 2–3 dashboards shortlisted during the second break (use screenshots) |

### Feedback survey (3:25; it's also the raffle ticket)

1. Overall, how useful was today? *(1–5)*
2. Which part was most useful? *(Lakeflow Designer and Jobs · AI/BI dashboards · Genie Agents and Genie One · Genie Code · Unity Catalog and governance)*
3. How was the pace of Lab 1? *(Too slow · About right · Too fast)*
4. How was the pace of Lab 2? *(Too slow · About right · Too fast)*
5. Did anything block you during the labs? *(free text)*
6. How likely are you to use something from today in your own work in the next month? *(1–5)*
7. What would you like a follow-up session on? *(free text)*
8. Would your team like to join a 30-day Genie Agent challenge? *(Yes · Maybe · No)*, and your team's name *(optional)*
9. Your email, for the swag raffle *(optional)*

Say on the survey how emails will be used (the raffle draw and the recap email only). Draw the winners from respondents who left an email, and announce them at the close, or in the recap email if the survey stays open.


## 2.13 After the workshop

- **Before resetting anything,** export the progress board as a PDF: it's the attendance and completion record.
- **Within 24 hours,** send the recap email (below) and share the survey results with the organisers.
- **Keep the workspace open** for 1–2 weeks for practice, if the platform allows. Then run `08_reset_or_teardown` → `teardown`.
- **Use cases:**
  - cluster the answers to *"What's one question you wish you could ask your data?"* into 3–5 candidate Genie Agent pilots;
  - review them with Richard's team within two weeks.
- **Measure:** attendance and lab completion (from the progress board), satisfaction, use cases submitted, Genie Agents created in SMBC's workspace within 30 days, and training enrolments.

**Recap email template:**

> **Subject: Thank you for joining the Databricks Data & AI Workshop**
>
> Hi all, thank you for spending the time with us. As promised:
>
> - **Slides and lab workbook:** \<links\>
> - **Recording:** \<link, if recorded\>
> - **Keep practising:** the workshop workspace stays open until \<date\>. Your pipeline, dashboard and Genie Agent are still there.
> - **Keep learning:** free training at https://www.databricks.com/learn/training, and Databricks Free Edition at https://www.databricks.com/learn/free-edition
>
> **What you found:** Orchid Group crossed 90% of its group limit at the end of FY2026 H1, which is invisible one subsidiary at a time. About a quarter of the rise was FX and the rest was new borrowing. And a re-sent extract would have overstated exposure by USD 366.9m without de-duplication. All of it is synthetic, but the patterns are real.
>
> **Next step:** if your team would like to join the 30-day Genie Agent challenge, reply with one business question set you'd like to try.
>
> If you haven't filled in the feedback survey yet, it's here: \<link\>. Thank you again.

# Part 3. Attendee guide

> This part is the attendee workbook: it contains no answers, so it can be shared with attendees as it is. Its section numbers match the printed lab workbook.

> **All workshop data is synthetic.** The labs use a made-up SMBC APAC corporate lending book: every borrower, group, limit and balance is fictional. No SMBC data, systems or customer information is used at any point.

## Before you start

**1. Sign in.** Open `<workspace URL>` in Microsoft Edge or Google Chrome and sign in with your SMBC account. The workshop's **Labs** folder has one notebook per session, from *00 Start here* to *04 Kit and help*; clone one (**File → Clone**) to run its cells.

**2. Check in.** Open **SQL Editor**, choose the workshop's SQL warehouse (your facilitator will name it), paste this block and click **Run**. It checks you in and creates your schema for Lab 1. Change `DA` to `DE` if you're a data engineer.

```sql
-- Check in and create your Lab 1 schema. Change 'DA' to 'DE' if you're a data engineer.
BEGIN
  DECLARE my_schema STRING DEFAULT regexp_replace(lower(split_part(current_user(), '@', 1)), '[^a-z0-9_]', '_');
  INSERT INTO smbc_workshop.ops.checkin SELECT current_user(), 'DA', current_timestamp();
  CREATE SCHEMA IF NOT EXISTS IDENTIFIER('smbc_workshop.' || my_schema);
  SELECT 'smbc_workshop.' || my_schema AS your_schema;
END
```

**3. Your schema.** The check-in shows its name. Your Lab 1 tables go in `smbc_workshop.<your schema>`: the part of your email address before the @, in lower case, with any other characters replaced by `_`. For example, `jane.tan@…` becomes `jane_tan`.

**4. Getting help.** Turn your card to red, or raise a hand, and a helper will come to you.

**5. Short on time?** The reference tables in `smbc_workshop.gold` hold the Lab 1 result, so you can carry on with Lab 2 and the Genie Code segment whatever happens in Lab 1.

---

## 1. The scenario and the data

The labs use a synthetic **SMBC APAC** corporate lending book with about USD 27bn of drawn exposure across 12 booking branches in Asia Pacific. Every borrower, group and figure is made up. Borrowers belong to counterparty groups, such as a conglomerate and its subsidiaries in several countries, and each group has an approved credit limit set by the risk team. As at SMBC, the fiscal year runs from April to March.

### Source files (`/Volumes/smbc_workshop/raw/landing/`)

| Folder | Format | Rows | What it is |
|---|---|---|---|
| `counterparties/` | CSV | 2,370 | Customer master: borrower, parent group, country, sector, internal rating. Names in English, plus local script where available (日本語, 中文, ไทย, 한국어, Tiếng Việt). |
| `facilities/` | JSON Lines | 6,047 | Credit facilities: product, currency, committed amount, start and maturity dates, booking branch, collateral. |
| `monthly_balances/` | CSV | 74,799 | Month-end drawn balance and days past due per facility, April 2025 to September 2026. |
| `fx_rates/` | CSV | 252 | Month-end FX rates to USD and JPY for 14 currencies. |
| `group_limits/` | Excel | 420 | The risk team's spreadsheet of approved limits per counterparty group. |
| `sector_emission_factors/` | CSV | 16 | Illustrative emission factors by sector, for an optional ESG stretch question. |

### Notes from the source-system owners

These are the kind of handover notes a data team gets, and Lab 1 deals with each of them:

- *"The customer master extract sometimes contains the same row twice."*
- *"Currency codes on facilities are typed by hand, so expect `usd`, `US$`, `S$` and `RMB`."*
- *"The trade-finance system writes dates as DD/MM/YYYY; the core loan system uses YYYY-MM-DD."*
- *"Bangkok re-sent its September trade-finance extract. Keep the latest copy of each row (see `extract_ts`)."*
- *"FX rates are captured on the last business day of each month, not always the calendar month end."*
- *"A few facilities were booked before the customer record was created in the master."*

### Reference tables (`bronze`, `silver` and `gold`)

The reference solution to Lab 1, in the medallion layout. Anyone can use the gold tables to carry on with Lab 2 and the Genie Code segment.

| Table | Grain | Use |
|---|---|---|
| `gold.group_exposure` | Counterparty group × month | Exposure, limit and `utilisation_pct` per group |
| `gold.facility_exposure` | Facility × month | Exposure with borrower, country, sector, branch, product, currency and days past due |
| `silver.*`, including `silver.quarantine_facilities` | Cleaned inputs, and the rows held back with a reason | For comparing with your own Lab 1 output |
| `bronze.*` | The extracts as delivered, as tables | Where the cleaning starts |

---

## 2. Lab 1: Build the trusted exposure table

**Goal:** turn the raw extracts into `gold_group_exposure`, a table the Credit Committee can trust, with bad rows quarantined, duplicates removed, and every step visible as code and as lineage.
**Time:** 40 minutes, made up of a 25-minute core path and 15 minutes of stretch exercises.
**Tools:** Lakeflow Designer, Genie Code, Lakeflow Jobs, Unity Catalog.

> **Short on time?** Nothing in Lab 2 depends on finishing Lab 1: the gold reference tables have the same result. Work in pairs, ideally one analyst and one engineer, with the engineer driving.

### Core path

**0. Find your schema (1 min).** Your check-in created it and showed its name: the part of your email address before the @, for example `jane_tan`. Find it in **Catalog Explorer** → `smbc_workshop`. Not there? Run the check-in block (A.1) again.

**1. Start a visual data prep (1 min).** Click **+ New → Visual data prep**. Rename the tab to `Monday exposure report`. In the compute picker at the top right, choose **Serverless**.

**2. Bring in the sources (4 min).** Add a **Source** operator → **Browse existing** → `smbc_workshop` → `raw` → `landing` → select the **`counterparties`** folder. Designer reads every file in a folder into one table. Do the same for `facilities`, `monthly_balances` and `fx_rates`. For the limits, drag `group_limits.xlsx` onto the canvas (download it from the landing volume first), or browse to the `group_limits` folder. Click each Source and look at the preview: can you see two date formats in `monthly_balances`?

**3. De-duplicate the customer master (1 min).** After `counterparties`, add **Unique** with **Unique by: All columns**. Row count: 2,370 → 2,325.

**4. Clean the facilities with Genie Code (4 min).** Select the `facilities` Source and type this into the Genie Code prompt on the canvas:
> *Add a Prepare step that trims and upper-cases `currency`, maps `US$` to `USD`, `S$` to `SGD` and `RMB` to `CNY`, and parses `start_date` and `maturity_date` whether they're written YYYY-MM-DD or DD/MM/YYYY.*

Open the operator it adds and read its actions. Then open **Table of contents** in the left panel, select the operator, and expand **Generated code**. Every visual step is real code you can review and version.

**5. Quarantine bad rows with Guardrails (4 min).** Add **Guardrails** after the Prepare step, with these checks:
- **Value range:** `committed_amount` greater than 0
- **Expression:** `maturity_date >= start_date`
- **Not null:** `start_date`, `maturity_date`

Set **When a check fails** to **Warn and continue with passed rows**. Connect **Failed** to an **Output** that writes the table `quarantine_facilities` to your schema. You should see 21 failed rows. Each one has a reason, and that's your data-quality evidence.

**6. Fix the balances and FX dates (3 min).**
- On `monthly_balances`, add a **Prepare** step with two **Formula** actions. Describe them in plain English: *"`as_of_date` as a date, whether written YYYY-MM-DD or DD/MM/YYYY"* and *"`month` = first day of the month of `as_of_date`"*.
- Then add **Unique** → **Selected columns** `facility_id`, `as_of_date` → **Order by** `extract_ts` descending. Rows: 74,799 → 74,757.
- On `fx_rates`, add a Formula: *"`rate_month` = first day of the month of `rate_date`"*.

**7. Join and convert with Genie Code (4 min).** Prompt:
> *Join the de-duplicated balances to the facilities that passed Guardrails and to the de-duplicated counterparties. Then join fx_rates on currency = currency_code and month = rate_month, and add exposure_usd = drawn_amount × usd_rate and exposure_jpy = drawn_amount × jpy_rate.*

Check the Join outputs:
- **Left unmatched** on the facilities-to-counterparties join shows the facilities whose customer isn't in the master yet (send them to a second quarantine Output if you like).
- **Left unmatched** on the FX join should be empty. If it shows `US$`, `S$` or `RMB`, step 4 missed a mapping.

**8. Roll up to the group and compare with limits (3 min).**
- Add **Aggregate**: group by `as_of_date`, `parent_group_id`; **SUM** of `exposure_usd` and `exposure_jpy`.
- Add **Join** with the limits on `parent_group_id` = `group_id`.
- Add a **Prepare** Formula: *"`utilisation_pct` = 100 × exposure_usd ÷ group_limit_usd"*.

**9. Write and schedule (2 min).** Add an **Output**: **Table** `gold_group_exposure` in your schema, **Write mode: Overwrite**, then **Run**. Click **Schedule** to run it daily at 07:00 Singapore time.

✅ **Checkpoint:** your row on the progress board turns green. To check your result against the reference, run both queries (notebook *01* in the Labs folder works out your schema for you); the two totals should be identical:

```sql
SELECT round(sum(exposure_usd) / 1e6, 1) AS mine_usd_m
FROM smbc_workshop.<your_schema>.gold_group_exposure WHERE as_of_date = '2026-09-30';

SELECT round(sum(exposure_usd) / 1e6, 1) AS reference_usd_m
FROM smbc_workshop.gold.group_exposure WHERE as_of_date = '2026-09-30';
```

### Stretch (pick any)

- **Version and diff:** open the version history (right pane) to see a visual diff of your changes. Then commit the visual data prep to a Git folder.
- **Engineer's path:** rebuild the facility cleaning in the **Lakeflow Pipelines Editor** with Genie Code in agent mode, using expectations (`CONSTRAINT valid_commitment EXPECT (committed_amount > 0) ON VIOLATION DROP ROW`). Compare the data-quality metrics with your Guardrails output.
- **Alerting:** add a task that checks *"any group above 90% utilisation?"* and sends a notification when it's true.
- **Document it:** in Catalog Explorer, accept or edit the AI-suggested description for `gold_group_exposure`. Better metadata means better Genie answers in Lab 2.

---

## 3. Lab 2: Credit Committee in 30 seconds

**Goal:** give the Credit Committee a dashboard for the questions they always ask, and a Genie Agent for the ones they haven't asked yet. Teach the agent the bank's rules, and test that it's right.
**Time:** 40 minutes, made up of a 25-minute core path and 15 minutes of stretch exercises.
**Tools:** AI/BI dashboards, Genie Agents, Genie One, Unity Catalog.

> Use the **gold** reference tables (`smbc_workshop.gold.group_exposure` and `smbc_workshop.gold.facility_exposure`) so everyone's answers match. If you finished Lab 1, your own tables give the same numbers.

### Core path

**1. Build the dashboard (10 min).**
- Click **+ New → Dashboard**. On the **Data** tab, add both gold tables.
- On the canvas, ask the AI assistant: *"Bar chart of the top 10 counterparty groups by exposure_usd at the latest as_of_date, coloured by utilisation_pct."*
- Add these widgets:
  - a **counter** for total exposure at the latest month end;
  - a **counter** for groups above 80% utilisation;
  - a **line chart** of total exposure by month;
  - a **bar chart** of exposure by country.
- Add filters for `as_of_date` and `booking_branch`, then **Publish**.
- Open `<workspace URL>/one`: this is Genie One, what a business user sees.

**2. Create a Genie Agent (5 min).**
- Click **Genie Agents → New**, select the two gold tables (`group_exposure` and `facility_exposure`), and click **Create**.
- Genie Code reads the tables and suggests descriptions and example queries. Review them, and accept the ones that are right.
- In **Configure → Settings**, set the title to `Credit Risk – <your name>` and the default warehouse to the SQL warehouse you checked in with.
- Add the starter instructions (A.3), the two example SQL queries (A.5) and the common questions (A.6).

**3. Ask, and check the SQL (5 min).** Try *"Which counterparty groups are closest to their limits?"* and *"Show exposure in yen by booking branch at the latest month end."* Open the generated SQL for each answer. Trust, but verify.

**4. The fiscal-year test (4 min).** Before adding the fiscal-year instruction, ask:
- *"What was Orchid Group's utilisation at the end of Q1 FY2026?"*
- *"Show Orchid Group's utilisation for each month of FY2025."*

Open the SQL and check which dates Genie used. Then add the fiscal-year instruction (A.4) and ask both again.

✅ **Checkpoint:** ask *"Which groups were above 90% of their limit at the end of FY2026 H1?"*, then submit the name of the group:

```sql
INSERT INTO smbc_workshop.ops.lab_answers SELECT current_user(), 'lab2', '<group name>', current_timestamp();
```

### Stretch (pick any)

- **Stump the Genie:** find a question it gets wrong, fix it with an instruction or an example query, and ask again. Share your best stump-and-fix with a facilitator: there's a prize.
  - *Starter example (tested):* ask *"Which booking branch has the highest share of trade finance in arrears?"* and open the SQL. In one test run Genie counted facilities; in another it weighted by exposure and asked which one we meant. Add the instruction *"Shares of arrears are measured by exposure (exposure_usd), not by number of facilities"*, and the answer becomes consistent.
- **Benchmarks:** add the benchmark questions (A.7) with their expected SQL and run an evaluation. Benchmarks are how a team shows a Genie Agent is accurate before sharing it.
- **Agent mode:** ask *"Why has the most utilised group's limit usage risen since April 2026?"* and watch it plan, run several queries and write a report.
- **In Japanese:** 「2026年度上期末時点で、与信限度額の90%を超えている取引先グループはどこですか？」 Answers may sometimes come back in English.
- **Share it:** attach your Genie Agent to your dashboard, or schedule a Monday 08:00 PDF subscription of the dashboard.
- **Semantic layer:** use the agent's ⋮ menu → **Export to metric view** to turn the definitions you taught it into a governed metric view.

---

## 4. AI-assisted development with Genie Code

**15 minutes**, mostly a live demo; participants can follow along in notebook *03* in the Labs folder, which has the prompts (A.8) and the legacy procedure (A.9).

1. **Explore:** profile `gold.group_exposure` and ask what is unusual about the latest month compared with April.
2. **Generate:** split one group's exposure change since April into an **FX effect** and a **new-drawdowns effect**, by subsidiary, and chart it. This answers the "why" behind the Credit Committee's question.
3. **Explain and convert:** paste a legacy Synapse T-SQL procedure (A.9). Genie Code explains what it does, points out logic risks, and rewrites it as Databricks SQL against the workshop tables.
4. **Iterate safely:**
   - Show the action-approval setting: by default an AI classifier approves actions within your request and blocks actions beyond it, or you can approve each one yourself.
   - Ask for an explanation with *"don't run any code"*.
   - Show that Genie Code can only reach data your Unity Catalog permissions allow.
   - Roll back a change with revision history.

---

## 5. Resources

| Resource | Link |
|---|---|
| Free self-paced training and learning paths for data analysts and data engineers | https://www.databricks.com/learn/training |
| Certifications (Data Analyst Associate, Data Engineer Associate) | https://www.databricks.com/learn/certification |
| Databricks Free Edition, for practice outside work | https://www.databricks.com/learn/free-edition |
| Free virtual workshops (4 Nov *Hands-on with Genie*, 12 Nov *AI-Powered Data Engineering with Lakeflow*, 18 Nov *Build, Orchestrate and Improve Agents*; Americas time slots, recordings available) | https://www.databricks.com/learn/training/workshop |
| Lakeflow Designer documentation | https://learn.microsoft.com/azure/databricks/designer/what-is-lakeflow-designer |
| Genie Agents documentation | https://learn.microsoft.com/azure/databricks/genie-agents/ |
| Genie One documentation | https://learn.microsoft.com/azure/databricks/genie-one/ |
| Genie Code documentation | https://learn.microsoft.com/azure/databricks/genie-code/ |

---

## Appendix A: Copy-paste kit

### A.1 Check-in and checkpoint queries

```sql
-- Check in and create your Lab 1 schema. Change 'DA' to 'DE' if you're a data engineer.
BEGIN
  DECLARE my_schema STRING DEFAULT regexp_replace(lower(split_part(current_user(), '@', 1)), '[^a-z0-9_]', '_');
  INSERT INTO smbc_workshop.ops.checkin SELECT current_user(), 'DA', current_timestamp();
  CREATE SCHEMA IF NOT EXISTS IDENTIFIER('smbc_workshop.' || my_schema);
  SELECT 'smbc_workshop.' || my_schema AS your_schema;
END

-- Lab 2 checkpoint
INSERT INTO smbc_workshop.ops.lab_answers SELECT current_user(), 'lab2', '<group name>', current_timestamp();
```

### A.2 Genie Code prompts for Lab 1 (Designer)

```text
Add a Prepare step that trims and upper-cases currency, maps US$ to USD, S$ to SGD and RMB to CNY, and parses
start_date and maturity_date whether they're written YYYY-MM-DD or DD/MM/YYYY.
```

```text
Join the de-duplicated balances to the facilities that passed Guardrails and to the de-duplicated counterparties.
Then join fx_rates on currency = currency_code and month = rate_month, and add exposure_usd = drawn_amount × usd_rate
and exposure_jpy = drawn_amount × jpy_rate.
```

### A.3 Genie Agent starter instructions

```text
This agent answers questions about SMBC APAC's corporate lending exposure. All data is synthetic.

- Exposure means drawn balance. Use exposure_usd unless the user asks for yen; then use exposure_jpy.
- Utilisation means a counterparty group's exposure divided by its approved group limit (utilisation_pct in
  group_exposure). Above 90% is "near its limit"; above 100% is "in breach".
- Balances are month-end snapshots. For "current" or "latest", use the most recent as_of_date. Never add balances
  across months; compare month ends instead.
- A counterparty group's exposure includes all of its subsidiaries in every country (parent_group_id).
- Booking branch codes: SIN Singapore, HKG Hong Kong, BKK Bangkok, SGN Ho Chi Minh City, JKT Jakarta, BOM Mumbai,
  SYD Sydney, SEL Seoul, SHA Shanghai, KUL Kuala Lumpur, MNL Manila, TPE Taipei.
- Arrears means days_past_due greater than 30.
- Show amounts in USD millions with one decimal place unless asked otherwise.
```

### A.4 The fiscal-year instruction (add in Lab 2, step 4)

```text
The fiscal year runs from 1 April to 31 March and is named after the calendar year it starts in:
FY2026 = 1 April 2026 to 31 March 2027. H1 = April to September; H2 = October to March.
Q1 = April–June, Q2 = July–September, Q3 = October–December, Q4 = January–March.
"End of FY2026 H1" means as_of_date = 2026-09-30. "FY2026 to date" means as_of_date from 2026-04-30 onwards.
```

### A.5 Example SQL queries

**"Top 10 counterparty groups by exposure at the latest month end"**
```sql
SELECT group_name, round(exposure_usd / 1e6, 1) AS exposure_usd_m, utilisation_pct
FROM smbc_workshop.gold.group_exposure
WHERE as_of_date = (SELECT max(as_of_date) FROM smbc_workshop.gold.group_exposure)
ORDER BY exposure_usd DESC
LIMIT 10;
```

**"Exposure by country and sector at a given month end"** (parameterised)
```sql
SELECT country_code, sector, round(sum(exposure_usd) / 1e6, 1) AS exposure_usd_m
FROM smbc_workshop.gold.facility_exposure
WHERE as_of_date = :as_of_date
GROUP BY country_code, sector
ORDER BY exposure_usd_m DESC;
```

### A.6 Common questions

```text
Which counterparty groups are closest to their limits?
How has total exposure changed month by month since April 2025?
What is our exposure to Vietnam by sector at the latest month end?
Show exposure in yen by booking branch at the latest month end.
Which booking branch has the highest share of trade finance in arrears?
```

### A.7 Benchmark questions (stretch)

| Question | Expected SQL |
|---|---|
| Total exposure in USD at 30 Sep 2026 | `SELECT sum(exposure_usd) FROM smbc_workshop.gold.facility_exposure WHERE as_of_date = '2026-09-30'` |
| Which groups were above 90% of their limit at the end of FY2026 H1? | `SELECT group_name, utilisation_pct FROM smbc_workshop.gold.group_exposure WHERE as_of_date = '2026-09-30' AND utilisation_pct > 90` |
| Top 5 groups by exposure at the end of June 2026 | `SELECT group_name, exposure_usd FROM smbc_workshop.gold.group_exposure WHERE as_of_date = '2026-06-30' ORDER BY exposure_usd DESC LIMIT 5` |
| Utilisation by month in FY2026 for the most utilised group | `SELECT as_of_date, utilisation_pct FROM smbc_workshop.gold.group_exposure WHERE parent_group_id = (SELECT parent_group_id FROM smbc_workshop.gold.group_exposure WHERE as_of_date = '2026-09-30' ORDER BY utilisation_pct DESC LIMIT 1) AND as_of_date >= '2026-04-30' ORDER BY as_of_date` |
| Share of SGN trade-finance exposure in arrears at 30 Sep 2026 | `SELECT 100 * sum(CASE WHEN days_past_due > 30 THEN exposure_usd ELSE 0 END) / sum(exposure_usd) FROM smbc_workshop.gold.facility_exposure WHERE as_of_date = '2026-09-30' AND booking_branch = 'SGN' AND source_system = 'TRADE_FIN'` |

### A.8 Genie Code prompts (AI-assisted development segment)

```text
Profile smbc_workshop.gold.group_exposure and tell me what is unusual about the latest month
compared with April 2026.
```

```text
For the group with the highest utilisation at 30 Sep 2026, split the change in USD exposure between 30 Apr 2026
and 30 Sep 2026 into an FX effect and a new-drawdowns (volume) effect, by subsidiary, using
smbc_workshop.gold.facility_exposure. Use: volume = (Sep balance − Apr balance) × Apr rate;
FX = Sep balance × (Sep rate − Apr rate). Chart it.
```

```text
Explain what this procedure does and point out any risks in its logic. Then rewrite it as Databricks SQL against
the smbc_workshop.gold tables. Just explain first, don't run any code.
<paste A.9>
```

### A.9 Legacy Synapse procedure (synthetic example)

```sql
-- Legacy month-end group exposure report (synthetic example for the workshop)
CREATE PROCEDURE rpt.usp_GroupExposure_Monthly @AsOfDate DATE
AS
BEGIN
    SET NOCOUNT ON;

    IF OBJECT_ID('tempdb..#bal') IS NOT NULL DROP TABLE #bal;

    SELECT b.facility_id,
           b.drawn_amount,
           ISNULL(f.currency, 'USD') AS ccy,
           cp.parent_group_id
    INTO #bal
    FROM stg.monthly_balances b
    INNER JOIN stg.facilities f ON f.facility_id = b.facility_id
    INNER JOIN stg.counterparties cp ON cp.counterparty_id = f.counterparty_id
    WHERE b.as_of_date = @AsOfDate
      AND f.committed_amount > 0;

    SELECT TOP 20
           g.group_name,
           SUM(b.drawn_amount * fx.usd_rate) AS exposure_usd,
           CAST(100.0 * SUM(b.drawn_amount * fx.usd_rate) / NULLIF(g.group_limit_usd, 0) AS DECIMAL(9, 2))
               AS utilisation_pct,
           CASE WHEN SUM(b.drawn_amount * fx.usd_rate) > 0.90 * g.group_limit_usd THEN 'RED'
                WHEN SUM(b.drawn_amount * fx.usd_rate) > 0.75 * g.group_limit_usd THEN 'AMBER'
                ELSE 'GREEN' END AS rag_status
    FROM #bal b
    CROSS APPLY (SELECT TOP 1 r.usd_rate
                 FROM ref.fx_rates r
                 WHERE r.currency_code = b.ccy AND r.rate_date <= @AsOfDate
                 ORDER BY r.rate_date DESC) fx
    INNER JOIN ref.group_limits g ON g.group_id = b.parent_group_id
    GROUP BY g.group_name, g.group_limit_usd
    ORDER BY exposure_usd DESC;
END
```

---

## Appendix B: Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| **Genie Agents** is in the sidebar but agents won't open | Partner-powered AI features are off | Ask a facilitator |
| Genie Code prompts in Designer or agent mode are unavailable | Partner-powered AI features off, or cross-Geo processing enforced | Ask a facilitator |
| The check-in fails with a permission error, or you can't see the `landing` volume | No access to `smbc_workshop` yet | Ask a facilitator |
| Output fails with a permission error | Writing outside your own schema | Set **Output location** to `smbc_workshop.<your_schema>` |
| Some months disappear after the FX join | Joining on the exact date: FX is dated on the last business day | Join on currency and month (Lab 1, step 6) |
| Your total is higher than the checkpoint | Duplicates not removed (customer master or the re-sent Bangkok extract) | Lab 1, steps 3 and 6 |
| Your total is much lower than the checkpoint | Only one date format parsed, or currency codes not mapped | Lab 1, steps 4 and 6; check the join's **Left unmatched** output |
| Dragging the `.xlsx` onto the canvas fails | Excel file support not enabled, or downloads blocked | Use **Source → Browse existing →** `group_limits` folder instead |
| Genie picks the wrong dates for "Q1 FY2026", "FY2025" or "FY2026 H1" | It assumed a calendar year (it does this inconsistently) | Add the fiscal-year instruction (A.4) |
| Genie's arrears "share" is much higher than the dashboard's | It counted facilities instead of weighting by exposure | Add an instruction that shares are by exposure (see Stump the Genie) |
| A question in Japanese gets an English answer | Possible: the agent framework wraps prompts in English. In testing, the Japanese question in Lab 2 was answered correctly, in Japanese. | Add Japanese metadata or instructions if needed |
| A dashboard subscription email doesn't arrive | Mail gateway filtering | Ask a facilitator |

# Part 4. Workspace setup and requirements

> For SMBC's SAG team and workspace administrators. Section numbers match the workshop guide.

## 3. Workspace requirements: what must be enabled

> **For the SAG team and workspace administrators.** Each item explains why the workshop needs it, where the setting lives, and its default. Please confirm **at least two days before the workshop** so the smoke tests in 3.8 can run on an SMBC laptop before the day. Setting names and paths are from the Azure Databricks documentation as of October 2026.

**Already confirmed:** the workshop uses a new, dedicated workspace with **serverless compute enabled**, and **Genie has no question-rate limit** to plan around. The **SAG team owns the cross-Geo processing setting** (item 5).

**No groups are needed.** The setup shares everything with the workspace's built-in `users` group (everyone in the workspace) and recognises facilitators by email. Attendees need access to the `smbc_workshop` catalog (3.6) and to a SQL warehouse (3.4).

### 3.1 Checklist

| # | Requirement | Why the workshop needs it | Where it's set | Who | Default | Status |
|---|---|---|---|---|---|---|
| 1 | Unity Catalog metastore attached to the workspace | Everything: Designer, Genie Agents, lineage | Account console | Account admin | New workspaces are usually enabled automatically | ☐ |
| 2 | Serverless compute | Designer, notebooks, Jobs, Genie Code | Already enabled | Workspace admin | | ✅ |
| 3 | A pro or serverless **SQL warehouse** that attendees can use | Dashboards, Genie Agents, SQL editor | Any existing warehouse, for example the Serverless Starter Warehouse (3.4) | Workspace admin | | ☐ |
| 4 | **Partner-powered AI features** on, for the account *and* the workspace | Genie Agents, chat in Genie One, Genie Code's agentic features (including Designer's natural-language prompts), AI-assisted dashboard charts | 3.2 and 3.3 | Account admin, workspace admin | On (off for workspaces with the compliance security profile) | ☐ |
| 5 | **Cross-Geo processing** allowed | In the Asia Pacific Geo: Genie Agents (chat and agent mode), chat in Genie One, Genie Code's agentic features | 3.2 | Account admin (**SAG team**) | Allowed for workspaces outside the US and EU without the compliance security profile | ☐ |
| 6 | Excel file support | Dragging the limits spreadsheet onto the Designer canvas | Smoke test 5; if it fails, check the workspace **Previews** page | Workspace admin | | ☐ |
| 7 | Attendees can sign in, with **Workspace access** and **Databricks SQL access**; no groups needed | Signing in and building | 3.5 | Workspace admin | On for workspace users | ☐ |
| 8 | One test user with **Consumer access** only | Showing the business-user view in Genie One | 3.5 | Workspace admin | | ☐ |
| 9 | The `smbc_workshop` catalog, and attendee access to it | The labs | The setup notebook (section 4), then the grants in 3.6 | Catalog owner or metastore admin | | ☐ |
| 10 | Access from SMBC laptops on the venue network | Everything | 3.7 | SMBC network team | | ☐ |
| 11 | *(Optional)* Delivery of dashboard subscription emails to SMBC addresses | A Lab 2 stretch exercise | SMBC mail gateway | SMBC messaging team | | ☐ |

### 3.2 Account-level settings (account admin)

**Partner-powered AI features: on.** Genie Agents, chat in Genie One, Genie Code's agentic capabilities and AI-assisted dashboard charts are only available with this setting on. When it is off, Genie Code still works without its agentic capabilities, using a Databricks-hosted model.
1. In the [account console](https://accounts.azuredatabricks.net), click **Settings**.
2. Open the **Feature enablement** tab.
3. Set **Enable partner-powered AI features** to **On**. Use **Enforce** only if workspaces must not override it.

Enabling or disabling this setting is recorded as an account event in the audit logs.

**Cross-Geo processing: allowed** *(owner: SAG team)*. Some AI features are "Designated Services" that use Azure Geographies to manage data residency. In the **Asia Pacific Geo**, which includes Southeast Asia (Singapore), the features this workshop uses for Genie need cross-Geo processing (see 3.9).
1. In the account console sidebar, click **Workspaces** and open the workshop workspace.
2. Open the **Security and compliance** tab.
3. Make sure **Enforce data processing within workspace Geography for Designated Services** is **disabled**. Some pages call it *Enforce data processing within workspace Geography for AI features*.

The documentation says: *"your data is not stored outside of your workspace's Geo regardless of this setting."* Cross-Geo processing is enabled by default for workspaces outside the US and EU that don't use the compliance security profile, so this is usually a check rather than a change. Preview features also follow this setting.

**Account-level Genie One: optional.** The workshop uses the workspace-level Genie One (`<workspace URL>/one`), so account-level Genie One isn't required. If you review it: Databricks-generated metadata for account-level Genie One (asset identifiers, usage signals, audit events) might be processed in the US. An account admin can turn it off under **Settings → Feature enablement → Genie** without affecting workspace-level Genie One.

**Compliance security profile.** If the workspace uses the compliance security profile, partner-powered AI features are off by default and need an explicit decision.

### 3.3 Workspace-level settings (workspace admin)

- **Partner-powered AI features: on.** Go to your username → **Settings** → **Workspace admin** → **Advanced** → **Partner-powered AI features**. It inherits the account setting unless the account enforces it.
- **Previews:** none are required. Optionally turn on **Genie Agents Flash Mode** (Beta), a faster agent-mode option. Outside the US and EU it also needs cross-Geo processing.
- **Genie One homepage (optional, recommended),** so the business-user view feels finished when it's shown. This is set in the UI only, after `06_deploy_dashboards_and_agents` has run:
  1. Go to your username → **Settings** → **Appearance**, and next to **Genie One home page** click **Edit**.
  2. Paste the welcome message below into **Markdown text**. Optionally set a brand colour and upload a logo.
  3. Turn on **Pinned content enabled**, click **Edit pinned assets**, and pin the reference dashboard and the reference Genie Agent. Click **Save**.

Welcome message for the Genie One homepage:

```markdown
## Welcome to the SMBC Data & AI Workshop
Start with the **Credit Committee: APAC exposure** dashboard, or ask the **Credit Risk** Genie Agent a question in plain English.

*All data in this workspace is synthetic: the borrowers, groups and figures are made up.*
```

### 3.4 Compute

| Item | Recommendation |
|---|---|
| SQL warehouse | Any pro or serverless SQL warehouse that attendees can use (**CAN USE**), for example the workspace's **Serverless Starter Warehouse**. The setup uses the one you name, or picks the first one you can use, and prints its name: give that name to attendees. For about 40–60 people, a Small or Medium serverless warehouse with up to 4 clusters is comfortable; if you manage it, set a longer auto-stop on the day. Genie Agents need pro or serverless; serverless is recommended. |
| Serverless compute for notebooks, Jobs and Designer | Already on. Check that a test attendee can pick **Serverless** in Designer's compute picker; Designer needs CAN USE on at least one compute resource. |

### 3.5 Identity and entitlements

| Who | Entitlements | Notes |
|---|---|---|
| Attendees (any workspace users: no group is needed) | **Workspace access** and **Databricks SQL access** (on for workspace users by default) | Databricks SQL access is required to create Genie Agents and dashboards; workspace access is required for Designer and notebooks. |
| Facilitators | Workspace admin (recommended) | Run the setup notebooks and the governance demo. List the other facilitators' emails in the setup's `facilitator_emails` setting: they get full access to the catalog, see every branch in the governance demo, and can edit the reference dashboards and Genie Agents. |
| Genie One demo user (one account) | **Consumer access** only | Shows what a business user sees: dashboards and Genie Agents, no notebooks or compute. |

Sign-in is through SSO (Microsoft Entra ID). **No groups need to be created.** The setup shares the dashboards, Genie Agents and Labs folder with the workspace's built-in `users` group, which is everyone in the workspace, and recognises facilitators by email. To share with an existing group instead, set `share_with` in `00_master_setup`.

### 3.6 Unity Catalog objects

The setup notebook creates these objects. Creating a catalog needs the `CREATE CATALOG` privilege, and on metastores without root storage a managed location: set it in the setup, or create `smbc_workshop` yourself in Catalog Explorer, which can use Default Storage. If the catalog already exists, whoever runs the setup needs `ALL PRIVILEGES` and `MANAGE` on it.

| Object | Contents | What attendees need |
|---|---|---|
| Catalog `smbc_workshop` | Everything below, tagged `synthetic_data = true` and `workshop_date` (any tag a governed tag policy rejects is skipped) | `USE CATALOG`, and `CREATE SCHEMA` for their own schema |
| Volume `smbc_workshop.raw.landing` | Raw source extracts and the limits spreadsheet | `READ VOLUME` |
| Volume `smbc_workshop.raw.facilitator` | Answer key | Nothing |
| Schemas `smbc_workshop.bronze`, `silver` and `gold` | The reference tables (the Lab 1 solution): the extracts as tables, cleaned tables, and the gold tables Lab 2 uses | `USE SCHEMA`, `SELECT` |
| Schema `smbc_workshop.ops` | Check-in and lab-answer tables | `USE SCHEMA`, `MODIFY` |
| One schema per attendee, e.g. `smbc_workshop.jane_tan` | Each person's Lab 1 output; their check-in block creates it | They own it |

**Giving attendees access.** The setup grants attendees nothing. Once it has run, the catalog owner or a metastore admin runs these three statements. `account users` is everyone in the account; use an existing group instead if you prefer.

```sql
GRANT USE CATALOG, USE SCHEMA, SELECT, CREATE SCHEMA ON CATALOG smbc_workshop TO `account users`;
GRANT READ VOLUME ON VOLUME smbc_workshop.raw.landing TO `account users`;
GRANT MODIFY ON SCHEMA smbc_workshop.ops TO `account users`;
```

Granting `READ VOLUME` on the landing volume only keeps the answer key private. Attendees need no privileges on the governance demo's functions, because row filters and column masks run with their owner's rights. `07_check_requirements` reports whether attendees have everything they need.

### 3.7 Network and devices

- SMBC laptops on the venue network can open the workspace URL and sign in with SSO. If the workspace uses **IP access lists** or **Private Link**, allow the venue's egress addresses.
- Proxies and SSL inspection allow the workspace URL and `*.azuredatabricks.net`, including websockets.
- Use a current version of Microsoft Edge or Google Chrome.
- The quiz and the polls run on phones (Slido), so nothing needs installing on laptops.

### 3.8 Smoke tests

Run these as a **test attendee** (not an admin), **on an SMBC laptop, on the SMBC network**, after the setup notebooks have run and `07_check_requirements` passes.

| # | Test | Expected result | Proves |
|---|---|---|---|
| 1 | Sign in through SSO; open the SQL editor on the workshop's SQL warehouse; run the check-in block (A.1) | It shows your schema, e.g. `smbc_workshop.jane_tan` | Access, entitlements, warehouse, catalog access |
| 2 | **+ New → Visual data prep**; add a Source from `smbc_workshop.raw.landing/facilities` | Rows preview | Designer, serverless, volume grant |
| 3 | In Designer, type a Genie Code prompt: *"Trim and upper-case the currency column"* | A Prepare operator appears on the canvas | Partner-powered AI, cross-Geo (Genie Code agentic) |
| 4 | Add an **Output** to your own schema and **Run**; click **Schedule** | Table written; a job created | Schema grants, Jobs |
| 5 | Drag `group_limits.xlsx` (downloaded from the landing volume) onto the canvas | A Source operator for the spreadsheet | Excel file support |
| 6 | **+ New → Dashboard**; add `smbc_workshop.gold.group_exposure`; ask the AI assistant for a bar chart; **Publish** | Chart created; dashboard published | AI/BI, AI-assisted charts |
| 7 | **Genie Agents → New** on the two gold tables (`group_exposure`, `facility_exposure`); ask *"Top 5 groups by exposure at the latest month end"*, then try **Agent mode** | Answer with SQL; agent-mode report | Genie Agents (chat and agent mode) |
| 8 | Open `<workspace URL>/one` and use chat | Genie One loads; chat answers | Genie One chat |
| 9 | In a notebook, ask Genie Code to *"profile smbc_workshop.gold.group_exposure"* | It plans, runs code, summarises | Genie Code agent mode |
| 10 | In Catalog Explorer, open a table → AI-suggested description; open the **Lineage** tab | Suggestion shown; lineage graph | AI-generated comments, lineage |
| 11 | Sign in as the **Consumer access** user | Lands in Genie One; sees shared dashboard and Genie Agent | Consumer experience |

### 3.9 What processes data where

From the [Designated Services](https://learn.microsoft.com/en-us/azure/databricks/resources/designated-services) page (updated 14 October 2026) and the [Partner-powered AI features](https://learn.microsoft.com/en-us/azure/databricks/databricks-ai/partner-powered) page:

| Feature used in the workshop | Model provider | Asia Pacific Geo (e.g. Singapore) | Japan Geo |
|---|---|---|---|
| Genie Agents: chat mode | Azure OpenAI service | Needs cross-Geo processing | In-Geo |
| Genie Agents: agent mode | Anthropic on Databricks | Needs cross-Geo processing | In-Geo |
| Chat in Genie One | Anthropic on Databricks | Needs cross-Geo processing | In-Geo |
| Genie Code: agentic capabilities (also used by Designer) | Azure OpenAI service and Anthropic on Databricks | Needs cross-Geo processing | In-Geo |
| Genie Code: chat and cell actions | Azure OpenAI service | In-Geo | In-Geo |
| AI/BI dashboards | Azure OpenAI service | In-Geo | In-Geo |
| AI-generated comments | Azure OpenAI service (Databricks-hosted if partner features are off) | In-Geo | In-Geo |

Points the documentation makes that risk and technology reviewers usually ask about:

- **Storage stays in the Geo.** *"Your data is not stored outside of your workspace's Geo regardless of this setting."*
- **Anthropic on Databricks** *"uses endpoints hosted by Databricks within the Databricks security perimeter."*
- **Genie Agents query data as the person asking.** Generated queries are read-only, data access is evaluated with each user's own Unity Catalog permissions, and row filters and column masks are enforced per user. A question about data a user can't access returns an empty response.
- **What Genie Code sends to the model:** the prompt plus relevant context, such as table and column names, descriptions, the code being worked on, data samples and cell outputs, all within the user's Unity Catalog permissions. By default an AI classifier approves actions that carry out the request and blocks actions beyond it; users can instead approve every action themselves.
- **Cost:** Genie One and Genie Agents usage by users is free until 31 January 2027 (service principals are billed). Genie Code has been pay-as-you-go since 8 July 2026, with a free monthly allowance per user. Account admins can set budgets and cost controls for Genie.

---

## 4. Setting up the workspace

The scripts are in this repository. Import it into the workspace as a **Git folder** so the notebooks can find the data generator and the deployment tools. Everything runs inside the workspace on serverless compute, so no laptop or CLI is needed.

**One notebook does it all.** Open `setup/00_master_setup`. Every setting is optional:
- a SQL warehouse to use (blank: the first pro or serverless warehouse you can use, serverless and running ones first);
- the other facilitators' emails (you're always included);
- a managed location, only if creating a catalog asks for one;
- who to share the dashboards, Genie Agents and Labs folder with (default `users`: everyone in the workspace).

Then attach it to **Serverless** and click **Run all**. Before it creates anything, it checks that Unity Catalog is attached and that you can run queries on the SQL warehouse. Then it runs steps 2–6 and 9 below in order, and finishes with links to everything it created, the requirement checks, and the name of the warehouse to give attendees. In testing it took about 5 minutes, and it's safe to re-run. It needs someone who can create the `smbc_workshop` catalog, or who already has `ALL PRIVILEGES` and `MANAGE` on it; no groups are needed. Steps 7, 8 and 10 are done by hand.

You can also run the notebooks one at a time, in this order; for example, to repeat a single step.

| Step | Notebook | Who | Time |
|---|---|---|---|
| 1 | *(Optional, local)* `python data/generate_data.py --out data/output`, then `python data/validate_data.py --data data/output` (needs pandas) | Facilitator | 1 min |
| 2 | `setup/01_setup_workspace`: creates the catalog, schemas, volumes and ops tables, generates the data into the landing volume, and gives the facilitators `ALL PRIVILEGES` and `MANAGE` on the catalog | Facilitator who can create the catalog | 3 min |
| 3 | `setup/02_build_bronze_silver_gold` (SQL): builds the reference tables in the `bronze`, `silver` and `gold` schemas | Facilitator | 2 min |
| 4 | `setup/03_validate_bronze_silver_gold`: compares those tables with the answer key; every row must say PASS | Facilitator | 1 min |
| 5 | `setup/05_governance_demo`: row-filter and column-mask demo table | Facilitator | 2 min |
| 6 | `setup/06_deploy_dashboards_and_agents`: picks the SQL warehouse (3.4); tests and publishes the **reference dashboard** and the **progress board**; creates the **reference** and **secured demo** Genie Agents; copies the attendee notebooks in `labs/` into a **Labs** folder; and shares all of them with everyone in the workspace. It also creates the job **SMBC Workshop: daily data refresh**, which regenerates the data and rebuilds and validates the reference tables every day at 06:00 Singapore time | Facilitator | 5 min |
| 7 | Give attendees access to `smbc_workshop`: the three grants in 3.6 | Catalog owner or metastore admin | 1 min |
| 8 | Set up the Genie One homepage (3.3) | Workspace admin | 5 min |
| 9 | `setup/07_check_requirements`: automated checks of the requirements in section 3, including attendee access and a live question to the reference Genie Agent. Every row should say PASS; the attendee-access check warns until step 7 is done, so run it again afterwards. | Facilitator | 2 min |
| 10 | Run the smoke tests (3.8) | Facilitator with an SMBC volunteer | 30 min |

Between a dry run and the workshop, `setup/08_reset_or_teardown` empties the progress board and drops attendee schemas; after the workshop it tears everything down. It only lists what it would change until you set `dry_run` to `no`.

The tools behind step 6 (`setup/tools/dashboards.py`, `genie_agents.py` and `data_job.py`) also run from a laptop through the Databricks CLI. That's useful for rehearsing the Lab 2 fiscal-year test with the `starter` agent, which has no fiscal-year instruction.

The generator is deterministic: the same seed always produces identical files, so every answer in the facilitator's answer key holds. Re-running `00_master_setup` is safe, and so is the daily data job: each morning it writes the same files and tables, an hour before the 07:00 schedule attendees give their Lab 1 pipeline. If a run fails, whoever ran step 6 gets an email. Late registrations need nothing from the setup: once they can sign in and have access to the catalog, their check-in creates their schema.

---

## 5. Participant pre-work

Send **two days before the workshop**:

> **Subject: Before the Databricks workshop: 2-minute login check**
>
> Hi all, we're looking forward to seeing you at the workshop. To make sure the time goes on the hands-on labs rather than logins, please take two minutes before then to:
>
> 1. Open **`<workspace URL>`** in Microsoft Edge or Google Chrome on the laptop you'll bring, and sign in with your SMBC account.
> 2. Open **SQL Editor**, choose the **`<warehouse name>`** SQL warehouse, paste the check-in block from the end of this email and click **Run**. It checks you in and creates your schema for the labs. (Change `DA` to `DE` if you're a data engineer.)
> 3. If anything doesn't work, reply to this email. We'll also have a help desk open 30 minutes before the start.
>
> Please bring your laptop and charger, and your phone for the quiz. No preparation or software installation is needed. All workshop data is synthetic.
>
> Check-in block:
>
>     BEGIN
>       DECLARE my_schema STRING DEFAULT regexp_replace(lower(split_part(current_user(), '@', 1)), '[^a-z0-9_]', '_');
>       INSERT INTO smbc_workshop.ops.checkin SELECT current_user(), 'DA', current_timestamp();
>       CREATE SCHEMA IF NOT EXISTS IDENTIFIER('smbc_workshop.' || my_schema);
>       SELECT 'smbc_workshop.' || my_schema AS your_schema;
>     END

---

# Part 5. Presenter script

> Slide-by-slide speaker notes from the workshop slides: timing, what to say, what helpers should watch for, and fallbacks.

## Welcome and check-in · 0:00

### Slide 1: From days to seconds, with guardrails

*Before 0:00, on screen as people arrive*

- Doors open 30 minutes early, with a help desk for sign-in problems.
- The theme for the day: from days to seconds, with guardrails.
- Say it early and often: everything today uses a synthetic SMBC APAC lending book. The borrowers, groups and figures are made up, and no SMBC data, systems or customer information is used at any point.

### Slide 2: Get set up

*0:00 · 10 min*

- Most people should already be signed in from the pre-work email; this slot only confirms everyone is in.
- Fill in the warehouse name that 00_master_setup printed at the end.
- The check-in block writes one row to smbc_workshop.ops.checkin and creates the attendee's Lab 1 schema; the progress board shows both live. Put the board on the second screen.
- A permission error means the person doesn't have access to smbc_workshop yet (guide 3.6): a facilitator fixes it.
- Run the Slido poll while people sign in: Excel, SQL, Python, Power BI, ADF or Synapse, something else. It shows the room's mix of tools.
- Red card up: a helper comes over. Pair anyone who is still blocked with a neighbour so they don't miss Lab 1.

### Slide 3: Today's agenda

*0:02 · 1 min*

- Two short intros, each followed by a 40-minute hands-on lab, then a Genie Code segment you can follow along with, and a quiz on phones.
- Each lab has a 25-minute core path and 15 minutes of stretch exercises, so nobody waits and nobody gets left behind.
- The reference tables in bronze, silver and gold mean nobody gets stuck: if Lab 1 runs long, Lab 2 still works.
- Times are relative to the start time.

### Slide 4: The Monday exposure report

*0:04 · 2 min*

- One storyline runs through the day: the Monday exposure report.
- Lab 1 automates it with Lakeflow, Lab 2 makes it self-service with an AI/BI dashboard and a Genie Agent, and the Genie Code segment investigates what you found.
- By the end, everyone has built a pipeline, a dashboard and a Genie Agent themselves.

### Slide 5: The data: a synthetic SMBC APAC lending book

*0:06 · 2 min*

- Every borrower, group and figure is made up: this isn't SMBC's real book.
- Borrowers belong to counterparty groups, such as a conglomerate with subsidiaries in several countries. Each group has an approved credit limit, set by the risk team and kept in a spreadsheet.
- The files sit in a Unity Catalog volume, smbc_workshop.raw.landing, as the source systems delivered them. There's also a small sector_emission_factors file for an optional ESG question.
- The fiscal year runs April to March. Remember that for Lab 2.

### Slide 6: Your inbox this morning

*0:08 · 2 min*

- These are the kind of handover notes a data team really gets, and Lab 1 deals with each of them.
- Ask the room: which one would hurt the Credit Committee most? Don't answer yet; we reveal it after Lab 1.

## Data engineering with Lakeflow · 0:25

### Slide 7: Data engineering with Lakeflow

*0:25 · 20 min*

- At most 8 minutes of slides; spend the rest live in the workspace.
- Slides: the date hook, Lakeflow at a glance, and the trust message. Then the live demo, which is the first few steps of Lab 1.

### Slide 8: Quick question

*0:26 · 1 min*

- Show of hands: who reads this as 3 April? Who reads 4 March?
- Both are in today's data: the trade-finance system writes DD/MM/YYYY, the core loan system writes YYYY-MM-DD.
- In this data, parsing only the ISO format silently drops USD 4,789.2m of exposure at 30 September 2026. Lab 1 handles both formats.

### Slide 9: Lakeflow at a glance

*0:28 · 2 min*

- Lab 1 uses Designer and Jobs in the core path, and Pipelines in the engineer's stretch exercise.
- Position it next to what people run today. Nobody has to replace everything at once.

### Slide 10: No-code without shadow IT

*0:30 · 2 min*

- The trust message: no-code without shadow IT.
- In Designer, open Table of contents, select an operator and expand Generated code: every visual step is real code you can review and version.
- Version history (right pane) shows a visual diff of changes, and the visual data prep can be committed to a Git folder.
- The Schedule button turns it into a Lakeflow Job, and Unity Catalog governs every table it reads and writes.

### Slide 11: Live demo: what you'll see

*0:32 · about 12 min live*

Click path:

1. \+ New → Visual data prep. Rename it "Monday exposure report" and pick Serverless in the compute picker.
2. Drag group_limits.xlsx (downloaded from the landing volume beforehand) onto the canvas: Designer turns it into a Source operator. Show the preview.
3. Add Source → Browse existing → smbc_workshop → raw → landing → facilities.
4. Select it and type the prompt on the slide (also in the workbook, A.2). Open the Prepare operator it adds and read its actions aloud.
5. Table of contents → select the operator → expand Generated code.

Fallbacks:

- Excel drag fails: Source → Browse existing → the group_limits folder.
- Genie Code prompts unavailable: partner-powered AI features or cross-Geo processing are off (guide Appendix B). Add a Prepare operator by hand and show the dry-run screenshots.
- The AI output differs from the rehearsal: use it. That's why a person reviews every step.

## Lab 1 · 0:45

### Slide 12: Lab 1: Build the trusted exposure table

*0:45 · 40 min*

- Goal: turn the raw extracts into gold_group_exposure, a table the Credit Committee can trust, with bad rows quarantined, duplicates removed, and every step visible as code and as lineage.
- Nothing in Lab 2 depends on finishing Lab 1: the gold reference tables have the same result.
- The full steps are in the lab workbook PDF and in the Labs folder in the workspace: notebook 01 is Lab 1.
- Helpers: watch for red cards, and for anyone who hasn't added a Source after five minutes.

### Slide 13: Lab 1 at a glance

*Leave on screen during the lab*

Core path, about 25 minutes: 0 find your schema (1 min) · 1 start a visual data prep (1) · 2 bring in the sources (4) · 3 de-duplicate the customer master (1) · 4 clean the facilities with Genie Code (4) · 5 quarantine bad rows with Guardrails (4) · 6 fix the balances and FX dates (3) · 7 join and convert (4) · 8 roll up to the group and compare with limits (3) · 9 write and schedule (2).

Helpers, watch for:

- Can't see the landing volume: a missing READ VOLUME grant. Tell a facilitator.
- Output fails with a permission error: writing outside your own schema. Set the output location to smbc_workshop.\<your_schema\>.
- Months disappear after the FX join: joined on the exact date, but FX is dated on the last business day. Join on currency and month.
- The .xlsx won't drag in: use Source → Browse existing → the group_limits folder.
- Genie Code prompts unavailable: partner-powered AI features or cross-Geo processing. Tell a facilitator.

### Slide 14: Lab 1 · Steps 0–2: start and bring in the sources

*0:46 · 6 min*

- Designer reads every file in a folder into one table.
- The Excel file has to be downloaded from the landing volume before it can be dragged in. Browsing to the group_limits folder is the fallback.
- The two date formats are the 03/04/2026 problem from the intro.

### Slide 15: Lab 1 · Steps 3–4: de-duplicate, then clean with Genie Code

*0:52 · 5 min*

- 45 exact duplicate rows in the customer master. If they stay, every join fans out and exposure is overstated.
- The prompt is in the workbook (A.2), ready to copy.
- Point out that the generated actions are readable and editable: it isn't a black box.
- If the prompt doesn't respond: partner-powered AI features or cross-Geo processing are off. Add the Prepare actions by hand.

### Slide 16: Lab 1 · Step 5: quarantine bad rows with Guardrails

*0:57 · 4 min*

- 12 facilities have a commitment of zero or less, and 9 mature before they start.
- The Failed output keeps a reason per row. That's the evidence an auditor asks for.
- Helpers: if someone sees far more than 21, the dates weren't parsed in step 4 (unparsed dates fail the not-null check).

### Slide 17: Lab 1 · Step 6: fix the balances and FX dates

*1:01 · 3 min*

- The 42 rows removed by Unique are Bangkok's re-sent trade-finance extract for 30 September 2026. Keep the latest extract_ts.
- rate_month matters because FX is dated on the last business day of the month. A join on the exact date silently loses six months.

### Slide 18: Lab 1 · Step 7: join and convert with Genie Code

*1:04 · 4 min*

- The second prompt, also in the workbook (A.2).
- Joins in Designer ignore case and surrounding spaces by default, so only US$, S$ and RMB show up as unmatched if the mapping was missed.
- The 15 facilities with no customer record can go to a second quarantine Output.

### Slide 19: Lab 1 · Steps 8–9: roll up, compare with limits, schedule

*1:08 · 5 min*

- A counterparty group's exposure includes all of its subsidiaries in every country. That's why we aggregate by parent_group_id.
- Schedule turns the visual data prep into a Lakeflow Job.
- When the Output exists, the participant's row turns green on the progress board.

### Slide 20: Lab 1 checkpoint

*From about 1:10*

- Run both queries in the SQL editor. Notebook 01 in the Labs folder has a version that works out your schema from your login.
- Total higher than the checkpoint: duplicates not removed, either in the customer master or from the re-sent Bangkok extract.
- Total much lower: only one date format parsed, or currency codes not mapped. Check the join's Left unmatched output.
- 1:15: anyone not past step 5 switches to the gold reference tables.

### Slide 21: Lab 1 stretch: pick any

*For anyone who finishes the core path early*

- Engineer's path: Genie Code in agent mode, with expectations, for example CONSTRAINT valid_commitment EXPECT (committed_amount > 0) ON VIOLATION DROP ROW. Compare the data-quality metrics with the Guardrails output.
- Document it: better metadata means better Genie answers in Lab 2.

### Slide 22: Lab 1 debrief

*1:22 · 3 min*

- Open Catalog Explorer → gold_group_exposure → Lineage and trace it back through every step to the raw files. That's lineage evidence nobody had to draw by hand.
- Then the reveal: Bangkok's re-sent extract for 30 September 2026 duplicated 42 balance rows. Without one Unique step, the Credit Committee pack would have overstated exposure by USD 366.9m.
- Every held-back row has a reason attached. That's your data-quality evidence.

### Slide 23: 15-minute break

*1:25 · 15 min*

- Fill in the clock time before the day: back at 1:40, relative to the start.
- Put the progress board on screen during the break.

## Self-service analytics · 1:40

### Slide 24: Self-service analytics

*1:40 · 20 min*

- At most 8 minutes of slides, the rest live.

### Slide 25: Three tools, one message

*1:41 · 2 min*

- Dashboards answer the questions the Credit Committee always asks. A Genie Agent answers the follow-ups nobody built a chart for. Genie One is the simple front door for business users.
- Product names changed in 2026, and the workshop uses the current names: that's what people see in the product and the documentation.

### Slide 26: Curation is the job

*1:43 · 2 min*

- A Genie Agent is only as good as what it has been taught. Curation is the job, not an afterthought.
- Lab 2 shows what happens without a fiscal-year instruction.

### Slide 27: Trust, but verify

*1:45 · 2 min*

- A question about data you can't access returns an empty response.
- We show the permissions live in the governance moment at the end of Lab 2.
- Keep the BI point general: coexistence, not replacement.

### Slide 28: Live demo: what you'll see

*1:47 · about 12 min live*

Click path:

1. Open the published reference dashboard, "Credit Committee: APAC exposure (reference)". Walk through the counters, the top-10 chart and the trend.
2. Open \<workspace URL\>/one, signed in as the Consumer-access demo user: Genie One shows dashboards and Genie Agents, with no notebooks or compute.
3. Open the "Credit Risk (reference)" agent and ask "Show exposure in yen by booking branch at the latest month end", then the Japanese question on the slide: exposure in yen by booking branch (計上店) at the end of FY2026 Q2.
4. Open the SQL behind the answer.

Notes:

- These questions don't give away the Lab 2 answer. The dashboard's top-10 chart does show it, so don't dwell on the top bar.
- Tested on 15 October: Genie read the end of FY2026 Q2 as 30 September 2026, used exposure_jpy by booking branch, and answered in Japanese in about 20 seconds. Answers can sometimes come back in English.
- Talk through the dashboard while Genie works.

Fallback: if the Consumer-access user or Genie One chat fails, use the agent from Genie Agents in your own session.

## Lab 2 · 2:00

### Slide 29: Lab 2: Credit Committee in 30 seconds

*2:00 · 40 min*

- Goal: a dashboard for the questions the Credit Committee always asks, and a Genie Agent for the ones they haven't asked yet. Teach the agent the bank's rules, and test that it's right.
- The tables: smbc_workshop.gold.group_exposure and smbc_workshop.gold.facility_exposure.

### Slide 30: Lab 2 at a glance

*Leave on screen during the lab*

Timings: 2:10 dashboards published; 2:15 agents created; 2:24 fiscal-year test done; 2:25 answers submitted.

Helpers, watch for:

- Genie Agents won't open: partner-powered AI features are off. Tell a facilitator.
- Genie picks the wrong dates for "Q1 FY2026", "FY2025" or "FY2026 H1": expected until the fiscal-year instruction (A.4) is added.
- A dashboard subscription email doesn't arrive: mail filtering. Use a PDF download instead.
- The load on Genie is staggered naturally: everyone starts with the dashboard.

### Slide 31: Lab 2 · Step 1: build the dashboard

*2:00 · 10 min*

- The AI assistant drafts the chart; people adjust it. That's the pattern for the whole lab.
- Shortlist 2–3 good dashboards for the Best dashboard vote during the second break.

### Slide 32: Lab 2 · Step 2: create a Genie Agent

*2:10 · 5 min*

- The starter instructions define exposure, utilisation, month-end balances, groups, branch codes and arrears.
- Holding back A.4 is deliberate: step 4 shows what happens without it.

### Slide 33: Lab 2 · Step 3: ask, and check the SQL

*2:15 · 5 min*

- Check which table it used, which as_of_date it filtered on, and whether yen came from exposure_jpy.
- In testing, the first question put the most utilised group at the top, at 94%.

### Slide 34: Lab 2 · Step 4: the fiscal-year test

*2:20 · 4 min*

- Don't give the answer away here; we compare results in the debrief.
- The instruction (A.4): the fiscal year runs from 1 April to 31 March and is named after the calendar year it starts in. FY2026 = 1 April 2026 to 31 March 2027.

### Slide 35: Lab 2 checkpoint

*From about 2:25*

- Replace \<group name\> with the group the agent found, then run the line in the SQL editor.
- If an answer looks wrong, check the as_of_date in the SQL: FY2026 H1 ends on 30 September 2026.

### Slide 36: Lab 2 stretch: pick any

*For anyone who finishes the core path early*

- Stump the Genie, a tested starter: "Which booking branch has the highest share of trade finance in arrears?" In one test run Genie counted facilities; in another it weighted by exposure and asked which one we meant. The instruction "Shares of arrears are measured by exposure (exposure_usd), not by number of facilities" makes the answer consistent. Facilitators pick the best stump-and-fix.
- Agent mode: watch it plan, run several queries and write a report.
- In Japanese: answers may sometimes come back in English.

### Slide 37: Lab 2 debrief: what we saw in testing

*2:38 · 2 min*

- From testing on 15 October. Yet Genie guessed "end of FY2026 H1" correctly as 30 September, which is why the checkpoint question worked even before the instruction.
- That's why curation and benchmarks matter before anyone shares an agent with a credit committee.
- The finding: at the end of calendar H1 (30 June) no group was above 90%; at the end of FY2026 H1, Orchid Group was at 94%. It's invisible one subsidiary at a time.

### Slide 38: Governance moment: same question, two answers

*2:35 · 3 min*

- The demo agent "Credit Risk (secured demo)" sits on a copy of the facility table with a row filter (Singapore branch only, unless you're on the facilitator list) and a mask on borrower names.
- A facilitator and a volunteer ask the same question on screen.
- In testing, the facilitator saw all 12 branches; the attendee saw SIN only, with names masked.

### Slide 39: 15-minute break

*2:40 · 15 min*

- Fill in the clock time before the day: back at 2:55, relative to the start.
- Progress board on screen: read out how many people found the group.

## Genie Code · 2:55

### Slide 40: AI-assisted development with Genie Code

*2:55 · 15 min*

- Mostly a live demo; participants can follow along in their own notebook.
- Many people already use Genie Code, so skip the autocomplete basics: lead with agent mode, the legacy-SQL conversion and the approval settings.

### Slide 41: Genie Code · 1. Explore

*2:56 · 3 min*

- Agent mode: it plans, writes and runs code, fixes its own errors and summarises.
- Fallback: rehearse these exact prompts in the dry run and keep screenshots. If the output varies on the day, say so: that's why the human stays in the loop.

### Slide 42: Genie Code · 2. Generate

*2:59 · 4 min*

- The formulas are in the prompt so the answer is reproducible.
- Let it run; talk through the plan it shows while it works.

### Slide 43: Genie Code · 3. Explain and convert

*3:03 · 3 min*

- The procedure uses a temp table, ISNULL and CROSS APPLY, typical of what teams migrate from Synapse.
- "Don't run any code" gets an explanation only: a safety control people can use any time.
- For hundreds of stored procedures, Lakebridge (Databricks' migration toolkit) is the at-scale route.

### Slide 44: You stay in control

*3:06 · 3 min*

- Show the action-approval setting.
- Try a table you don't have access to: Genie Code can't reach it.
- Roll back a change with the notebook's revision history.

### Slide 45: Why did Orchid's utilisation rise?

*3:09 · 1 min*

- The "why" half of the CDAO's question.
- Measured on April balances instead, FX is 19%, so say which method you used.

## Quiz and close · 3:10

### Slide 46: Quiz: join on your phone

*3:10 · 15 min*

- The questions and answers are in facilitator/quiz.md. After each question, say its one-line teaching point: that's what people remember.
- First to finish Lab 1 comes from the progress board's "First to finish" table.
- If Slido is blocked on the SMBC network: phones on mobile data, or read the questions out and take answers by show of hands.

### Slide 47: What you found today

*3:25 · 2 min*

- Back to the CDAO's question. Which group? Orchid Group, visible only once its subsidiaries are rolled up to the group. Why? Three-quarters new drawdowns, mostly by four subsidiaries, and a quarter FX.
- A second signal to follow up: trade-finance arrears in Ho Chi Minh City crept from 1.1% to 9.6% of exposure, against 0.4% across the whole book.

### Slide 48: Keep learning

*3:27 · 3 min*

- The free virtual workshops run in Americas time slots, so point people to the recordings.
- Add a QR code to databricks.com/learn/training when you generate the deck.

### Slide 49: Proposed next step: a 30-day Genie Agent challenge

*3:30 · 2 min*

- A proposal: agree the wording with SMBC before the day.

### Slide 50: Thank you

*3:33*

- Add the survey QR code when you generate the deck.
- Prize-giving: quiz top three, Best Stump the Genie, First to finish Lab 1, Best dashboard.
- Thank the SMBC organisers and the helpers.
