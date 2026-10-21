# Databricks notebook source
# MAGIC %md
# MAGIC # Start here
# MAGIC
# MAGIC *SMBC Data & AI Workshop*
# MAGIC
# MAGIC > **All workshop data is synthetic.** The labs use a made-up SMBC APAC corporate lending book: every borrower, group, limit and balance is fictional. No SMBC data, systems or customer information is used at any point.
# MAGIC
# MAGIC This is a read-only copy. To run its cells, use **File → Clone** to copy it to your own folder, or paste the SQL into the SQL editor.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Before you start
# MAGIC
# MAGIC **1. Sign in.** Open `<workspace URL>` in Microsoft Edge or Google Chrome and sign in with your SMBC account. The workshop's **Labs** folder has one notebook per session, from *00 Start here* to *04 Kit and help*; clone one (**File → Clone**) to run its cells.
# MAGIC
# MAGIC **2. Check in.** Open **SQL Editor**, choose the workshop's SQL warehouse (your facilitator will name it), paste this block and click **Run**. It checks you in and creates your schema for Lab 1. Change `DA` to `DE` if you're a data engineer.
# MAGIC
# MAGIC ```sql
# MAGIC -- Check in and create your Lab 1 schema. Change 'DA' to 'DE' if you're a data engineer.
# MAGIC BEGIN
# MAGIC   DECLARE my_schema STRING DEFAULT regexp_replace(lower(split_part(current_user(), '@', 1)), '[^a-z0-9_]', '_');
# MAGIC   INSERT INTO smbc_workshop.ops.checkin SELECT current_user(), 'DA', current_timestamp();
# MAGIC   CREATE SCHEMA IF NOT EXISTS IDENTIFIER('smbc_workshop.' || my_schema);
# MAGIC   SELECT 'smbc_workshop.' || my_schema AS your_schema;
# MAGIC END
# MAGIC ```
# MAGIC
# MAGIC **3. Your schema.** The check-in shows its name. Your Lab 1 tables go in `smbc_workshop.<your schema>`: the part of your email address before the @, in lower case, with any other characters replaced by `_`. For example, `jane.tan@…` becomes `jane_tan`.
# MAGIC
# MAGIC **4. Getting help.** Turn your card to red, or raise a hand, and a helper will come to you.
# MAGIC
# MAGIC **5. Short on time?** The reference tables in `smbc_workshop.gold` hold the Lab 1 result, so you can carry on with Lab 2 and the Genie Code segment whatever happens in Lab 1.

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Check in and create your Lab 1 schema. Change 'DA' to 'DE' if you're a data engineer.
# MAGIC BEGIN
# MAGIC   DECLARE my_schema STRING DEFAULT regexp_replace(lower(split_part(current_user(), '@', 1)), '[^a-z0-9_]', '_');
# MAGIC   INSERT INTO smbc_workshop.ops.checkin SELECT current_user(), 'DA', current_timestamp();
# MAGIC   CREATE SCHEMA IF NOT EXISTS IDENTIFIER('smbc_workshop.' || my_schema);
# MAGIC   SELECT 'smbc_workshop.' || my_schema AS your_schema;
# MAGIC END

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. The scenario and the data
# MAGIC
# MAGIC The labs use a synthetic **SMBC APAC** corporate lending book with about USD 27bn of drawn exposure across 12 booking branches in Asia Pacific. Every borrower, group and figure is made up. Borrowers belong to counterparty groups, such as a conglomerate and its subsidiaries in several countries, and each group has an approved credit limit set by the risk team. As at SMBC, the fiscal year runs from April to March.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Source files (`/Volumes/smbc_workshop/raw/landing/`)
# MAGIC
# MAGIC | Folder | Format | Rows | What it is |
# MAGIC |---|---|---|---|
# MAGIC | `counterparties/` | CSV | 2,370 | Customer master: borrower, parent group, country, sector, internal rating. Names in English, plus local script where available (日本語, 中文, ไทย, 한국어, Tiếng Việt). |
# MAGIC | `facilities/` | JSON Lines | 6,047 | Credit facilities: product, currency, committed amount, start and maturity dates, booking branch, collateral. |
# MAGIC | `monthly_balances/` | CSV | 74,799 | Month-end drawn balance and days past due per facility, April 2025 to September 2026. |
# MAGIC | `fx_rates/` | CSV | 252 | Month-end FX rates to USD and JPY for 14 currencies. |
# MAGIC | `group_limits/` | Excel | 420 | The risk team's spreadsheet of approved limits per counterparty group. |
# MAGIC | `sector_emission_factors/` | CSV | 16 | Illustrative emission factors by sector, for an optional ESG stretch question. |

# COMMAND ----------

# MAGIC %md
# MAGIC ### Notes from the source-system owners
# MAGIC
# MAGIC These are the kind of handover notes a data team gets, and Lab 1 deals with each of them:
# MAGIC
# MAGIC - *"The customer master extract sometimes contains the same row twice."*
# MAGIC - *"Currency codes on facilities are typed by hand, so expect `usd`, `US$`, `S$` and `RMB`."*
# MAGIC - *"The trade-finance system writes dates as DD/MM/YYYY; the core loan system uses YYYY-MM-DD."*
# MAGIC - *"Bangkok re-sent its September trade-finance extract. Keep the latest copy of each row (see `extract_ts`)."*
# MAGIC - *"FX rates are captured on the last business day of each month, not always the calendar month end."*
# MAGIC - *"A few facilities were booked before the customer record was created in the master."*

# COMMAND ----------

# MAGIC %md
# MAGIC ### Reference tables (`bronze`, `silver` and `gold`)
# MAGIC
# MAGIC The reference solution to Lab 1, in the medallion layout. Anyone can use the gold tables to carry on with Lab 2 and the Genie Code segment.
# MAGIC
# MAGIC | Table | Grain | Use |
# MAGIC |---|---|---|
# MAGIC | `gold.group_exposure` | Counterparty group × month | Exposure, limit and `utilisation_pct` per group |
# MAGIC | `gold.facility_exposure` | Facility × month | Exposure with borrower, country, sector, branch, product, currency and days past due |
# MAGIC | `silver.*`, including `silver.quarantine_facilities` | Cleaned inputs, and the rows held back with a reason | For comparing with your own Lab 1 output |
# MAGIC | `bronze.*` | The extracts as delivered, as tables | Where the cleaning starts |
