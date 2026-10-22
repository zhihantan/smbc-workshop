# SMBC Data & AI Workshop: Workshop Guide

**SMBC Asia Pacific · Data Analysts and Data Engineers**

*Version 0.1, draft of 15 October 2026. Prepared by the Databricks account team (Siu-Li Choa, Zhi Han Tan) with SMBC (contacts TBC).*

> **All workshop data is synthetic.** The labs use a made-up SMBC APAC corporate lending book: every borrower, group, limit and balance is fictional. No SMBC data, systems or customer information is used at any point.

---

## Contents

1. [At a glance](#1-at-a-glance)
2. [Agenda](#2-agenda)
3. [Workspace requirements: what must be enabled](#3-workspace-requirements-what-must-be-enabled) (for the SAG team and workspace admins)
4. [Setting up the workspace](#4-setting-up-the-workspace)
5. [Participant pre-work](#5-participant-pre-work)
6. [The scenario and the data](#6-the-scenario-and-the-data)
7. [Lab 1: Build the trusted exposure table](#7-lab-1-build-the-trusted-exposure-table)
8. [Lab 2: Credit Committee in 30 seconds](#8-lab-2-credit-committee-in-30-seconds)
9. [AI-assisted development with Genie Code](#9-ai-assisted-development-with-genie-code)
10. [Quiz](#10-quiz)
11. [Next steps and resources](#11-next-steps-and-resources)
- [Appendix A: Copy-paste kit](#appendix-a-copy-paste-kit)
- [Appendix B: Troubleshooting](#appendix-b-troubleshooting)

---

## 1. At a glance

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

**One storyline runs through the day.** It's 8am on Monday at the APAC hub. The Credit Committee wants the top counterparty-group exposures across all booking branches, in USD and JPY, by 10am. Today that means four system extracts, a spreadsheet of limits, and days of reconciliation. In Lab 1 participants automate it, in Lab 2 they make it self-service, and in the Genie Code segment they investigate what they found. Section 6 tells the full story, as participants read it.

---

## 2. Agenda

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

## 3. Workspace requirements: what must be enabled

> **For the SAG team and workspace administrators.** Each item explains why the workshop needs it, where the setting lives, and its default. Please confirm **at least two days before the workshop** so the smoke tests in [3.8](#38-smoke-tests) can run on an SMBC laptop before the day. Setting names and paths are from the Azure Databricks documentation as of October 2026.

**Already confirmed:** the workshop uses a new, dedicated workspace with **serverless compute enabled**, and **Genie has no question-rate limit** to plan around. The **SAG team owns the cross-Geo processing setting** (item 5).

**No groups are needed.** The setup shares everything with the workspace's built-in `users` group (everyone in the workspace) and recognises facilitators by email. Attendees need access to the `smbc_workshop` catalog ([3.6](#36-unity-catalog-objects)) and to a SQL warehouse ([3.4](#34-compute)).

### 3.1 Checklist

| # | Requirement | Why the workshop needs it | Where it's set | Who | Default | Status |
|---|---|---|---|---|---|---|
| 1 | Unity Catalog metastore attached to the workspace | Everything: Designer, Genie Agents, lineage | Account console | Account admin | New workspaces are usually enabled automatically | ☐ |
| 2 | Serverless compute | Designer, notebooks, Jobs, Genie Code | Already enabled | Workspace admin | | ✅ |
| 3 | A pro or serverless **SQL warehouse** that attendees can use | Dashboards, Genie Agents, SQL editor | Any existing warehouse, for example the Serverless Starter Warehouse ([3.4](#34-compute)) | Workspace admin | | ☐ |
| 4 | **Partner-powered AI features** on, for the account *and* the workspace | Genie Agents, chat in Genie One, Genie Code's agentic features (including Designer's natural-language prompts), AI-assisted dashboard charts | [3.2](#32-account-level-settings-account-admin) and [3.3](#33-workspace-level-settings-workspace-admin) | Account admin, workspace admin | On (off for workspaces with the compliance security profile) | ☐ |
| 5 | **Cross-Geo processing** allowed | In the Asia Pacific Geo: Genie Agents (chat and agent mode), chat in Genie One, Genie Code's agentic features | [3.2](#32-account-level-settings-account-admin) | Account admin (**SAG team**) | Allowed for workspaces outside the US and EU without the compliance security profile | ☐ |
| 6 | Excel file support | Dragging the limits spreadsheet onto the Designer canvas | Smoke test 5; if it fails, check the workspace **Previews** page | Workspace admin | | ☐ |
| 7 | Attendees can sign in, with **Workspace access** and **Databricks SQL access**; no groups needed | Signing in and building | [3.5](#35-identity-and-entitlements) | Workspace admin | On for workspace users | ☐ |
| 8 | One test user with **Consumer access** only | Showing the business-user view in Genie One | [3.5](#35-identity-and-entitlements) | Workspace admin | | ☐ |
| 9 | The `smbc_workshop` catalog, and attendee access to it | The labs | The setup notebook ([section 4](#4-setting-up-the-workspace)), then the grants in [3.6](#36-unity-catalog-objects) | Catalog owner or metastore admin | | ☐ |
| 10 | Access from SMBC laptops on the venue network | Everything | [3.7](#37-network-and-devices) | SMBC network team | | ☐ |
| 11 | *(Optional)* Delivery of dashboard subscription emails to SMBC addresses | A Lab 2 stretch exercise | SMBC mail gateway | SMBC messaging team | | ☐ |

### 3.2 Account-level settings (account admin)

**Partner-powered AI features: on.** Genie Agents, chat in Genie One, Genie Code's agentic capabilities and AI-assisted dashboard charts are only available with this setting on. When it is off, Genie Code still works without its agentic capabilities, using a Databricks-hosted model.
1. In the [account console](https://accounts.azuredatabricks.net), click **Settings**.
2. Open the **Feature enablement** tab.
3. Set **Enable partner-powered AI features** to **On**. Use **Enforce** only if workspaces must not override it.

Enabling or disabling this setting is recorded as an account event in the audit logs.

**Cross-Geo processing: allowed** *(owner: SAG team)*. Some AI features are "Designated Services" that use Azure Geographies to manage data residency. In the **Asia Pacific Geo**, which includes Southeast Asia (Singapore), the features this workshop uses for Genie need cross-Geo processing (see [3.9](#39-what-processes-data-where)).
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
| Catalog `smbc_workshop` | Everything below, tagged `synthetic_data = true` (the tag is skipped if a governed tag policy rejects it) | `USE CATALOG`, and `CREATE SCHEMA` for their own schema |
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
| 6 | `setup/06_deploy_dashboards_and_agents`: picks the SQL warehouse ([3.4](#34-compute)); tests and publishes the **reference dashboard** and the **progress board**; creates the **reference** and **secured demo** Genie Agents; copies the attendee notebooks in `labs/` into a **Labs** folder; and shares all of them with everyone in the workspace. It also creates the job **SMBC Workshop: daily data refresh**, which regenerates the data and rebuilds and validates the reference tables every day at 06:00 Singapore time | Facilitator | 5 min |
| 7 | Give attendees access to `smbc_workshop`: the three grants in [3.6](#36-unity-catalog-objects) | Catalog owner or metastore admin | 1 min |
| 8 | Set up the Genie One homepage ([3.3](#33-workspace-level-settings-workspace-admin)) | Workspace admin | 5 min |
| 9 | `setup/07_check_requirements`: automated checks of the requirements in [section 3](#3-workspace-requirements-what-must-be-enabled), including attendee access and a live question to the reference Genie Agent. Every row should say PASS; the attendee-access check warns until step 7 is done, so run it again afterwards. | Facilitator | 2 min |
| 10 | Run the smoke tests ([3.8](#38-smoke-tests)) | Facilitator with an SMBC volunteer | 30 min |

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

## 6. The scenario and the data

The labs use a synthetic **SMBC APAC** corporate lending book with about USD 27bn of drawn exposure across 12 booking branches in Asia Pacific. Every borrower, group and figure is made up. Borrowers belong to counterparty groups, such as a conglomerate and its subsidiaries in several countries, and each group has an approved credit limit set by the risk team. As at SMBC, the fiscal year runs from April to March.

### The story: the Monday exposure report

It's 8:00 on Monday at the APAC hub. The Credit Committee meets at 10:00 and wants the top counterparty-group exposures across all 12 booking branches, in USD and JPY. Behind it is the question the CDAO asks the room at the start of the day: *"Which client groups are closest to their limits, and why?"*

**Why that's hard today.** A group's exposure is spread across subsidiaries in several countries, booked in different branches and currencies, so no single system adds it up. Answering means four system extracts, the risk team's spreadsheet of limits and days of reconciliation, and the extracts have the problems in the notes below. A group can creep towards its limit without any one report showing it. And the committee asks in the bank's own terms, such as *"the end of FY2026 H1"*, which a tool that assumes a calendar year gets wrong.

**How you solve it, one session at a time:**

| Session | What you build or use | What it solves |
|---|---|---|
| Lab 1: automate it | A **Lakeflow Designer** pipeline from the raw extracts to your own `gold_group_exposure` table, scheduled daily with **Lakeflow Jobs** | One trusted figure per group and month: duplicates removed; currencies, dates and FX rates fixed; bad rows held back with a reason; every step visible as code and as lineage |
| Lab 2: make it self-service | An **AI/BI dashboard** for the Credit Committee and a **Genie Agent**, shared through **Genie One** | The questions the committee always asks, on one page: total exposure, the largest groups and how close each is to its limit, the trend, and a watchlist. New questions answered in plain English or Japanese, using the April-to-March fiscal year you teach the agent, with the SQL behind every answer |
| Genie Code: find out why | **Genie Code** in a notebook | What changed since April; how much of a group's rise is currency movement rather than new lending; and a legacy SQL procedure rewritten for Databricks, with you in control of what runs |
| All day: governance | **Unity Catalog**, under everything you build | Lineage, data-quality checks and permissions that follow the data: a Genie Agent shows each person only the branches and borrower names they're allowed to see |

By the end of the day you can answer the CDAO's question yourself, with numbers you can trace back to the source files. The quiz checks what you found.

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

## 7. Lab 1: Build the trusted exposure table

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

### Facilitator close (3 min)

- Open **Catalog Explorer → `gold_group_exposure` → Lineage** and trace it back through every step to the raw files. That's lineage evidence nobody had to draw by hand.
- Then reveal what the duplicate extract would have done to the Credit Committee pack.

---

## 8. Lab 2: Credit Committee in 30 seconds

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

> **What we saw when testing (15 Oct).** Without the instruction, Genie treated Q1 FY2026 as January–March 2026 and answered *"70.0%, not near its limit"*, and it treated FY2025 as January–December 2025. Yet it guessed *"end of FY2026 H1"* correctly as 30 September. After adding the instruction, Q1 FY2026 ends on 30 June (79.0%), and FY2025 runs from April 2025 to March 2026. **The lesson: without explicit rules the AI guesses, and it doesn't guess the same way every time.** That's why curation and benchmarks matter before anyone shares an agent with a credit committee.

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

### Governance moment (facilitator, 3 min)

A demo Genie Agent sits on a copy of the facility table that has a **row filter** (Singapore branch only, unless you're a facilitator) and a **column mask** on borrower names. A facilitator and a volunteer ask the same question and get different, correct answers: the Genie Agent inherits Unity Catalog permissions rather than bypassing them.

---

## 9. AI-assisted development with Genie Code

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

## 10. Quiz

- **Format:** about 12 questions of 20 seconds each, on phones with Slido (confirm that SMBC allows it). There's a mix of questions about what people discovered in the labs, product questions, and one "Genie or human?" round. The facilitator pack has the questions and answers.
- **Prizes:** quiz top three, plus *Best Stump the Genie*, *First to finish Lab 1* (from the progress board) and *Best dashboard* (peer vote).
- **Close:** a short feedback survey, which doubles as the swag raffle ticket.

---

## 11. Next steps and resources

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

**Proposed follow-up with SMBC:** a 30-day Genie Agent challenge. Each team nominates one real business question set, and the Databricks team holds weekly 30-minute office hours, leading into a pilot in SMBC's own workspace.

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
| **Genie Agents** is in the sidebar but agents won't open | Partner-powered AI features are off | [3.2](#32-account-level-settings-account-admin), [3.3](#33-workspace-level-settings-workspace-admin) |
| Genie Code prompts in Designer or agent mode are unavailable | Partner-powered AI features off, or cross-Geo processing enforced | [3.2](#32-account-level-settings-account-admin) |
| The check-in fails with a permission error, or you can't see the `landing` volume | No access to `smbc_workshop` yet | Grant it ([3.6](#36-unity-catalog-objects)) |
| Output fails with a permission error | Writing outside your own schema | Set **Output location** to `smbc_workshop.<your_schema>` |
| Some months disappear after the FX join | Joining on the exact date: FX is dated on the last business day | Join on currency and month (Lab 1, step 6) |
| Your total is higher than the checkpoint | Duplicates not removed (customer master or the re-sent Bangkok extract) | Lab 1, steps 3 and 6 |
| Your total is much lower than the checkpoint | Only one date format parsed, or currency codes not mapped | Lab 1, steps 4 and 6; check the join's **Left unmatched** output |
| Dragging the `.xlsx` onto the canvas fails | Excel file support not enabled, or downloads blocked | Use **Source → Browse existing →** `group_limits` folder instead |
| Genie picks the wrong dates for "Q1 FY2026", "FY2025" or "FY2026 H1" | It assumed a calendar year (it does this inconsistently) | Add the fiscal-year instruction (A.4) |
| Genie's arrears "share" is much higher than the dashboard's | It counted facilities instead of weighting by exposure | Add an instruction that shares are by exposure (see Stump the Genie) |
| A question in Japanese gets an English answer | Possible: the agent framework wraps prompts in English. In testing, the Japanese question in Lab 2 was answered correctly, in Japanese. | Add Japanese metadata or instructions if needed |
| A dashboard subscription email doesn't arrive | Mail gateway filtering | Check with the SMBC messaging team; use a PDF download for the demo |
