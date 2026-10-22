# Databricks notebook source
# MAGIC %md
# MAGIC # Copy-paste kit, troubleshooting and resources
# MAGIC
# MAGIC *SMBC Data & AI Workshop*
# MAGIC
# MAGIC > **All workshop data is synthetic.** The labs use a made-up SMBC APAC corporate lending book: every borrower, group, limit and balance is fictional. No SMBC data, systems or customer information is used at any point.
# MAGIC
# MAGIC This is a read-only copy. To run its cells, use **File → Clone** to copy it to your own folder, or paste the SQL into the SQL editor.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Appendix A: Copy-paste kit

# COMMAND ----------

# MAGIC %md
# MAGIC ### A.1 Check-in and checkpoint queries
# MAGIC
# MAGIC ```sql
# MAGIC -- Check in and create your Lab 1 schema. Change 'DA' to 'DE' if you're a data engineer.
# MAGIC BEGIN
# MAGIC   DECLARE my_schema STRING DEFAULT regexp_replace(lower(split_part(current_user(), '@', 1)), '[^a-z0-9_]', '_');
# MAGIC   INSERT INTO smbc_workshop.ops.checkin SELECT current_user(), 'DA', current_timestamp();
# MAGIC   CREATE SCHEMA IF NOT EXISTS IDENTIFIER('smbc_workshop.' || my_schema);
# MAGIC   SELECT 'smbc_workshop.' || my_schema AS your_schema;
# MAGIC END
# MAGIC
# MAGIC -- Lab 2 checkpoint
# MAGIC INSERT INTO smbc_workshop.ops.lab_answers SELECT current_user(), 'lab2', '<group name>', current_timestamp();
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ### A.2 Genie Code prompts for Lab 1 (Designer)
# MAGIC
# MAGIC ```text
# MAGIC Add a Prepare step that trims and upper-cases currency, maps US$ to USD, S$ to SGD and RMB to CNY, and parses
# MAGIC start_date and maturity_date whether they're written YYYY-MM-DD or DD/MM/YYYY.
# MAGIC ```
# MAGIC
# MAGIC ```text
# MAGIC Join the de-duplicated balances to the facilities that passed Guardrails and to the de-duplicated counterparties.
# MAGIC Then join fx_rates on currency = currency_code and month = rate_month, and add exposure_usd = drawn_amount × usd_rate
# MAGIC and exposure_jpy = drawn_amount × jpy_rate.
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ### A.3 Genie Agent starter instructions
# MAGIC
# MAGIC ```text
# MAGIC This agent answers questions about SMBC APAC's corporate lending exposure. All data is synthetic.
# MAGIC
# MAGIC - Exposure means drawn balance. Use exposure_usd unless the user asks for yen; then use exposure_jpy.
# MAGIC - Utilisation means a counterparty group's exposure divided by its approved group limit (utilisation_pct in
# MAGIC   group_exposure). Above 90% is "near its limit"; above 100% is "in breach".
# MAGIC - Balances are month-end snapshots. For "current" or "latest", use the most recent as_of_date. Never add balances
# MAGIC   across months; compare month ends instead.
# MAGIC - A counterparty group's exposure includes all of its subsidiaries in every country (parent_group_id).
# MAGIC - Booking branch codes: SIN Singapore, HKG Hong Kong, BKK Bangkok, SGN Ho Chi Minh City, JKT Jakarta, BOM Mumbai,
# MAGIC   SYD Sydney, SEL Seoul, SHA Shanghai, KUL Kuala Lumpur, MNL Manila, TPE Taipei.
# MAGIC - Arrears means days_past_due greater than 30.
# MAGIC - Show amounts in USD millions with one decimal place unless asked otherwise.
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ### A.4 The fiscal-year instruction (add in Lab 2, step 4)
# MAGIC
# MAGIC ```text
# MAGIC The fiscal year runs from 1 April to 31 March and is named after the calendar year it starts in:
# MAGIC FY2026 = 1 April 2026 to 31 March 2027. H1 = April to September; H2 = October to March.
# MAGIC Q1 = April–June, Q2 = July–September, Q3 = October–December, Q4 = January–March.
# MAGIC "End of FY2026 H1" means as_of_date = 2026-09-30. "FY2026 to date" means as_of_date from 2026-04-30 onwards.
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ### A.5 Example SQL queries
# MAGIC
# MAGIC **"Top 10 counterparty groups by exposure at the latest month end"**
# MAGIC ```sql
# MAGIC SELECT group_name, round(exposure_usd / 1e6, 1) AS exposure_usd_m, utilisation_pct
# MAGIC FROM smbc_workshop.gold.group_exposure
# MAGIC WHERE as_of_date = (SELECT max(as_of_date) FROM smbc_workshop.gold.group_exposure)
# MAGIC ORDER BY exposure_usd DESC
# MAGIC LIMIT 10;
# MAGIC ```
# MAGIC
# MAGIC **"Exposure by country and sector at a given month end"** (parameterised)
# MAGIC ```sql
# MAGIC SELECT country_code, sector, round(sum(exposure_usd) / 1e6, 1) AS exposure_usd_m
# MAGIC FROM smbc_workshop.gold.facility_exposure
# MAGIC WHERE as_of_date = :as_of_date
# MAGIC GROUP BY country_code, sector
# MAGIC ORDER BY exposure_usd_m DESC;
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ### A.6 Common questions
# MAGIC
# MAGIC ```text
# MAGIC Which counterparty groups are closest to their limits?
# MAGIC How has total exposure changed month by month since April 2025?
# MAGIC What is our exposure to Vietnam by sector at the latest month end?
# MAGIC Show exposure in yen by booking branch at the latest month end.
# MAGIC Which booking branch has the highest share of trade finance in arrears?
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ### A.7 Benchmark questions (stretch)
# MAGIC
# MAGIC | Question | Expected SQL |
# MAGIC |---|---|
# MAGIC | Total exposure in USD at 30 Sep 2026 | `SELECT sum(exposure_usd) FROM smbc_workshop.gold.facility_exposure WHERE as_of_date = '2026-09-30'` |
# MAGIC | Which groups were above 90% of their limit at the end of FY2026 H1? | `SELECT group_name, utilisation_pct FROM smbc_workshop.gold.group_exposure WHERE as_of_date = '2026-09-30' AND utilisation_pct > 90` |
# MAGIC | Top 5 groups by exposure at the end of June 2026 | `SELECT group_name, exposure_usd FROM smbc_workshop.gold.group_exposure WHERE as_of_date = '2026-06-30' ORDER BY exposure_usd DESC LIMIT 5` |
# MAGIC | Utilisation by month in FY2026 for the most utilised group | `SELECT as_of_date, utilisation_pct FROM smbc_workshop.gold.group_exposure WHERE parent_group_id = (SELECT parent_group_id FROM smbc_workshop.gold.group_exposure WHERE as_of_date = '2026-09-30' ORDER BY utilisation_pct DESC LIMIT 1) AND as_of_date >= '2026-04-30' ORDER BY as_of_date` |
# MAGIC | Share of SGN trade-finance exposure in arrears at 30 Sep 2026 | `SELECT 100 * sum(CASE WHEN days_past_due > 30 THEN exposure_usd ELSE 0 END) / sum(exposure_usd) FROM smbc_workshop.gold.facility_exposure WHERE as_of_date = '2026-09-30' AND booking_branch = 'SGN' AND source_system = 'TRADE_FIN'` |

# COMMAND ----------

# MAGIC %md
# MAGIC ### A.8 Genie Code prompts (AI-assisted development segment)
# MAGIC
# MAGIC ```text
# MAGIC Profile smbc_workshop.gold.group_exposure and tell me what is unusual about the latest month
# MAGIC compared with April 2026.
# MAGIC ```
# MAGIC
# MAGIC ```text
# MAGIC For the group with the highest utilisation at 30 Sep 2026, split the change in USD exposure between 30 Apr 2026
# MAGIC and 30 Sep 2026 into an FX effect and a new-drawdowns (volume) effect, by subsidiary, using
# MAGIC smbc_workshop.gold.facility_exposure. Use: volume = (Sep balance − Apr balance) × Apr rate;
# MAGIC FX = Sep balance × (Sep rate − Apr rate). Chart it.
# MAGIC ```
# MAGIC
# MAGIC ```text
# MAGIC Explain what this procedure does and point out any risks in its logic. Then rewrite it as Databricks SQL against
# MAGIC the smbc_workshop.gold tables. Just explain first, don't run any code.
# MAGIC <paste A.9>
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ### A.9 Legacy Synapse procedure (synthetic example)
# MAGIC
# MAGIC ```sql
# MAGIC -- Legacy month-end group exposure report (synthetic example for the workshop)
# MAGIC CREATE PROCEDURE rpt.usp_GroupExposure_Monthly @AsOfDate DATE
# MAGIC AS
# MAGIC BEGIN
# MAGIC     SET NOCOUNT ON;
# MAGIC
# MAGIC     IF OBJECT_ID('tempdb..#bal') IS NOT NULL DROP TABLE #bal;
# MAGIC
# MAGIC     SELECT b.facility_id,
# MAGIC            b.drawn_amount,
# MAGIC            ISNULL(f.currency, 'USD') AS ccy,
# MAGIC            cp.parent_group_id
# MAGIC     INTO #bal
# MAGIC     FROM stg.monthly_balances b
# MAGIC     INNER JOIN stg.facilities f ON f.facility_id = b.facility_id
# MAGIC     INNER JOIN stg.counterparties cp ON cp.counterparty_id = f.counterparty_id
# MAGIC     WHERE b.as_of_date = @AsOfDate
# MAGIC       AND f.committed_amount > 0;
# MAGIC
# MAGIC     SELECT TOP 20
# MAGIC            g.group_name,
# MAGIC            SUM(b.drawn_amount * fx.usd_rate) AS exposure_usd,
# MAGIC            CAST(100.0 * SUM(b.drawn_amount * fx.usd_rate) / NULLIF(g.group_limit_usd, 0) AS DECIMAL(9, 2))
# MAGIC                AS utilisation_pct,
# MAGIC            CASE WHEN SUM(b.drawn_amount * fx.usd_rate) > 0.90 * g.group_limit_usd THEN 'RED'
# MAGIC                 WHEN SUM(b.drawn_amount * fx.usd_rate) > 0.75 * g.group_limit_usd THEN 'AMBER'
# MAGIC                 ELSE 'GREEN' END AS rag_status
# MAGIC     FROM #bal b
# MAGIC     CROSS APPLY (SELECT TOP 1 r.usd_rate
# MAGIC                  FROM ref.fx_rates r
# MAGIC                  WHERE r.currency_code = b.ccy AND r.rate_date <= @AsOfDate
# MAGIC                  ORDER BY r.rate_date DESC) fx
# MAGIC     INNER JOIN ref.group_limits g ON g.group_id = b.parent_group_id
# MAGIC     GROUP BY g.group_name, g.group_limit_usd
# MAGIC     ORDER BY exposure_usd DESC;
# MAGIC END
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## Appendix B: Troubleshooting
# MAGIC
# MAGIC | Symptom | Likely cause | Fix |
# MAGIC |---|---|---|
# MAGIC | **Genie Agents** is in the sidebar but agents won't open | Partner-powered AI features are off | Ask a facilitator |
# MAGIC | Genie Code prompts in Designer, or a Genie Agent's Agent mode, are unavailable | Partner-powered AI features off, or cross-Geo processing enforced | Ask a facilitator |
# MAGIC | The check-in fails with a permission error, or you can't see the `landing` volume | No access to `smbc_workshop` yet | Ask a facilitator |
# MAGIC | Output fails with a permission error | Writing outside your own schema | Set **Output location** to `smbc_workshop.<your_schema>` |
# MAGIC | Some months disappear after the FX join | Joining on the exact date: FX is dated on the last business day | Join on currency and month (Lab 1, step 6) |
# MAGIC | Your total is higher than the checkpoint | Duplicates not removed (customer master or the re-sent Bangkok extract) | Lab 1, steps 3 and 6 |
# MAGIC | Your total is much lower than the checkpoint | Only one date format parsed, or currency codes not mapped | Lab 1, steps 4 and 6; check the join's **Left unmatched** output |
# MAGIC | Dragging the `.xlsx` onto the canvas fails | Excel file support not enabled, or downloads blocked | Use **Source → Browse existing →** `group_limits` folder instead |
# MAGIC | Genie picks the wrong dates for "Q1 FY2026", "FY2025" or "FY2026 H1" | It assumed a calendar year (it does this inconsistently) | Add the fiscal-year instruction (A.4) |
# MAGIC | Genie's arrears "share" is much higher than the dashboard's | It counted facilities instead of weighting by exposure | Add an instruction that shares are by exposure (see Stump the Genie) |
# MAGIC | A question in Japanese gets an English answer | Possible: the agent framework wraps prompts in English. In testing, the Japanese question in Lab 2 was answered correctly, in Japanese. | Add Japanese metadata or instructions if needed |
# MAGIC | A dashboard subscription email doesn't arrive | Mail gateway filtering | Ask a facilitator |

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Resources
# MAGIC
# MAGIC | Resource | Link |
# MAGIC |---|---|
# MAGIC | Free self-paced training and learning paths for data analysts and data engineers | https://www.databricks.com/learn/training |
# MAGIC | Certifications (Data Analyst Associate, Data Engineer Associate) | https://www.databricks.com/learn/certification |
# MAGIC | Databricks Free Edition, for practice outside work | https://www.databricks.com/learn/free-edition |
# MAGIC | Free virtual workshops (4 Nov *Hands-on with Genie*, 12 Nov *AI-Powered Data Engineering with Lakeflow*, 18 Nov *Build, Orchestrate and Improve Agents*; Americas time slots, recordings available) | https://www.databricks.com/learn/training/workshop |
# MAGIC | Lakeflow Designer documentation | https://learn.microsoft.com/azure/databricks/designer/what-is-lakeflow-designer |
# MAGIC | Genie Agents documentation | https://learn.microsoft.com/azure/databricks/genie-agents/ |
# MAGIC | Genie One documentation | https://learn.microsoft.com/azure/databricks/genie-one/ |
# MAGIC | Genie Code documentation | https://learn.microsoft.com/azure/databricks/genie-code/ |
