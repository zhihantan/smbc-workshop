# Run of show (facilitators and organisers)

**Thursday 22 October 2026 · 3 hours 35 minutes · start time TBC.** Times are relative to the start, as in the guide's agenda. Fill in the names and the start time when they're confirmed. Nothing here is confidential to Databricks, so SMBC's organisers can use it too.

## 1. Roles

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

## 2. Countdown

| When | Task | Status |
|---|---|---|
| 15 Oct | Dataset generated and validated. Checkpoint tables, dashboards and Genie Agents built and tested in the Databricks test workspace ([test report](test_report_2026-10-15.md)) | ✅ |
| Fri 16 Oct | Send guide §3 to the SAG team and workspace admins. Confirm the start time, headcount and DA/DE split, venue Wi-Fi, whether Slido is allowed, and whether recording is allowed | ☐ |
| Mon 19 Oct | Internal dry run (section 6) | ☐ |
| Tue 20 Oct | In SMBC's workspace, run `setup/00_master_setup` (guide §4). It should finish with "none failed" and name the SQL warehouse to give attendees. Then grant attendees access to `smbc_workshop` (guide §3.6), run `07_check_requirements` again, and set up the Genie One homepage (guide §3.3) | ☐ |
| Tue 20 Oct | Smoke tests (guide §3.8) on an SMBC laptop, on the SMBC network, with 2–3 SMBC volunteers | ☐ |
| Tue 20 Oct | Send the pre-work email (guide §5), with the workspace URL and warehouse name filled in. Agree the executive briefing with Richard and Peter (section 7) | ☐ |
| Wed 21 Oct | Freeze the content. Set up the quiz ([quiz.md](quiz.md)), the polls and the survey ([polls_and_survey.md](polls_and_survey.md)) in Slido, and test them on a phone | ☐ |
| Wed 21 Oct | Print a cheat sheet per person plus spares (`handouts/dist/Cheat_Sheet.pdf`, rebuilt with the real workspace URL), and red/green cards. Record the fallback videos (section 5) | ☐ |
| Wed 21 Oct | Late registrations: check they can sign in and have access to `smbc_workshop`; their check-in creates their schema. Then run `08_reset_or_teardown` → `reset_progress` so the board starts at zero | ☐ |
| Day, −90 min | Arrive. Test the projector, clicker and Wi-Fi. Open the presenter tabs (section 3). Start the workshop's SQL warehouse (the one `00_master_setup` named) and, if you manage it, lengthen its auto-stop for the day | ☐ |
| Day, −30 min | Doors open; check-in desk opens | ☐ |

## 3. Presenter laptop: tabs to open before the start

1. The slides, generated from `slides/Workshop_Slides.md`, in presenter view.
2. The **progress board** (published view). It's on the projector during labs and breaks.
3. The **reference dashboard** (published view).
4. The two Genie Agents: **Credit Risk (reference)** and **Credit Risk (secured demo)**.
5. Lakeflow Designer: a new visual data prep for the demo, with `group_limits.xlsx` downloaded to the desktop.
6. A notebook with the Genie Code prompts (guide A.8) and the legacy procedure (A.9) ready to paste.
7. Genie One (`<workspace URL>/one`), signed in as the Consumer-access demo user, in a separate browser profile.
8. Slido, signed in, with the polls and the quiz ready.

## 4. Timeline

| Time | Segment | On the projector | What happens | Move on when |
|---|---|---|---|---|
| −0:30 | Doors open | Welcome slide | Check-in desk solves sign-in problems | |
| 0:00 | **Welcome and check-in** (10) | Welcome slide, then the progress board | Host welcomes; everyone runs the check-in line; the poll runs (*"What do you use most today?"*). Anyone not checked in by 0:05 gets a helper. | 0:10, or 90% checked in |
| 0:10 | **Executive briefing** (15) | Briefing slides | Richard 5 min, Peter 5 min, fireside 5 min (section 7). Richard asks *the CDAO's question*. | 0:25, hard stop |
| 0:25 | **Lakeflow** (20) | At most 8 min of slides, then live Designer | The demo: drag `group_limits.xlsx` onto the canvas → one Genie Code prompt → preview → open the generated code | 0:45 |
| 0:45 | **Lab 1** (40) | *Lab 1 at a glance*, then the progress board | Pairs, engineer driving. **0:55:** most pairs have their sources in (step 2). **1:10:** the core path should be done; call "stretch or catch up". **1:15:** anyone not past step 5 switches to the checkpoint tables. **1:22:** facilitator close (lineage, and the USD 366.9m reveal). | 1:25 |
| 1:25 | Break (15) | Progress board, "back at" slide | Helpers sort out anyone stuck | 1:40 |
| 1:40 | **Self-service analytics** (20) | Slides, then live | The demo: reference dashboard → Genie One as the Consumer-access user → a question in English, then in Japanese → open the SQL | 2:00 |
| 2:00 | **Lab 2** (40) | *Lab 2 at a glance*, then the progress board | **2:10:** dashboards published. **2:15:** Genie Agents created. **2:24:** the fiscal-year test done. **2:25:** answers submitted (the board shows them). **2:25–2:35:** stretch; Stump the Genie entries go to a facilitator. **2:35:** governance moment, facilitator and a volunteer (3 min). **2:38:** the fiscal-year debrief slide. | 2:40 |
| 2:40 | Break (15) | Progress board | Shortlist 2–3 dashboards for the *Best dashboard* vote; pick *Best Stump the Genie* | 2:55 |
| 2:55 | **Genie Code** (15) | Live notebook | Explore → generate (the FX split) → explain and convert the legacy procedure → the safety beat | 3:10 |
| 3:10 | **Quiz** (15) | Slido quiz | 12 questions; after each one, say its teaching point ([quiz.md](quiz.md)). Richard awards: quiz top three, *Best Stump the Genie*, *First to finish Lab 1* (the progress board's "First to finish" table), *Best dashboard* (Slido vote). | 3:25 |
| 3:25 | **Next steps** (10) | Closing slides | What you found today; resources; the 30-day Genie Agent challenge; the feedback survey, which is the raffle ticket | 3:35 |

If the organisers swap the last two slots (guide §2), the prizes close the session and the raffle draw comes straight after the survey.

## 5. If something goes wrong

| If | Then |
|---|---|
| SSO or the proxy blocks a few laptops | Pair them with a neighbour; the check-in desk escalates to SMBC IT |
| Nobody can reach the workspace | Present from the Databricks test workspace; people follow on the projector in pairs; play the recordings |
| Designer's Genie Code prompts don't respond | Build the step by hand from the actions in Lab 1, step 4, and check cross-Geo processing (guide §3.2) |
| Genie Agents error or are slow | Lab 2 carries on with the dashboard, Genie in pairs; check cross-Geo processing and partner-powered AI (`07_check_requirements` tests both) |
| Queries queue on the warehouse | Raise its maximum clusters in SQL Warehouses, or ask its owner to |
| Lab 1 overruns | At 1:15 move everyone to the checkpoint tables; Lab 2 doesn't depend on Lab 1 |
| AI output differs from the rehearsal | Say so: it's why you check the SQL. Show the recording if the difference matters |
| Slido is blocked on the SMBC network | Phones on mobile data; or read the questions from `quiz.md` and take answers by show of hands |

**Recordings to make on Wed 21 Oct**, in SMBC's workspace if possible, otherwise in the test workspace:
1. The Designer demo (Excel → prompt → preview → generated code).
2. Lab 1's core path end to end (speed it up).
3. Genie One as a business user, including the Japanese question.
4. The Genie Code prompts (A.8) and the legacy-SQL conversion (A.9).
5. A Genie Agents agent-mode answer.

## 6. Dry run: Monday 19 October, in the Databricks test workspace

**Goal:** time the labs with first-time users, and test what the 15 Oct tests couldn't reach through the APIs (the test report's "Not tested" list).

**Set up** (`fe-vm-zh-serverless-ws`; no groups are needed):
1. Add 3–5 colleagues to the workspace, including at least one who hasn't used Designer.
2. Run `08_reset_or_teardown` → `drop_attendee_schemas`, with `dry_run` = `no`.
3. Run `00_master_setup` with `folder` = `/Workspace/Users/zhihan.tan@databricks.com/smbc_workshop` and **Generate the synthetic data** = `no`. Leave the warehouse blank to let it pick one, or name one.
4. Give the colleagues access to `smbc_workshop` with the three grants in guide §3.6, then run `07_check_requirements` again: every row should pass.

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

## 7. Executive briefing: notes for Richard and Peter

Agree these by Tuesday 20 October. Fifteen minutes in three parts.

- **Richard (5 min):** why self-service *with guardrails* matters for the APAC Data Hub. Then he asks the room **the CDAO's question**: *"Which client groups are closest to their limits, and why?"* The room answers it by the end of the day.
- **Peter (5 min):** Databricks' commitment to SMBC: enablement and follow-up, such as the proposed 30-day Genie Agent challenge. *(Peter to provide content.)*
- **Fireside (5 min), two prepared questions:**
  - *"What does good look like by FY-end, March 2027?"*
  - *"Where should AI help, and where must a human stay in the loop?"* This sets up the governance thread for the day.
- Ask Richard to come back at **3:10** to award the prizes.
- Expect questions about where the AI features process data. Answer from guide §3.9; don't improvise.

## 8. Helper briefing (print one per helper)

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

**Catching up:** anyone can carry on from `smbc_workshop.checkpoint`.

**Escalation:** helper → lab lead → SMBC IT (sign-in and network).

**Don't** show participants the answer key, or tell them the planted findings before the reveals.

## 9. After the workshop

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
> Hi all, thank you for spending the afternoon with us on Thursday. As promised:
>
> - **Slides and lab workbook:** <links>
> - **Recording:** <link, if recorded>
> - **Keep practising:** the workshop workspace stays open until <date>. Your pipeline, dashboard and Genie Agent are still there.
> - **Keep learning:** free training at https://www.databricks.com/learn/training, and Databricks Free Edition at https://www.databricks.com/learn/free-edition
>
> **What you found:** Orchid Group crossed 90% of its group limit at the end of FY2026 H1, which is invisible one subsidiary at a time. About a quarter of the rise was FX and the rest was new borrowing. And a re-sent extract would have overstated exposure by USD 366.9m without de-duplication. All of it is synthetic, but the patterns are real.
>
> **Next step:** if your team would like to join the 30-day Genie Agent challenge, reply with one business question set you'd like to try.
>
> If you haven't filled in the feedback survey yet, it's here: <link>. Thank you again.
