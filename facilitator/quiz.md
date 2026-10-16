# Quiz (facilitators only)

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
