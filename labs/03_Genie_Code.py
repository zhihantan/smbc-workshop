# Databricks notebook source
# MAGIC %md
# MAGIC # AI-assisted development with Genie Code
# MAGIC
# MAGIC *SMBC Data & AI Workshop*
# MAGIC
# MAGIC > **All workshop data is synthetic.** The labs use a made-up SMBC APAC corporate lending book: every borrower, group, limit and balance is fictional. No SMBC data, systems or customer information is used at any point.
# MAGIC
# MAGIC This is a read-only copy. Use **File → Clone** to copy it to your own folder, attach it to **Serverless**, then open **Genie Code** and use the prompts below.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. AI-assisted development with Genie Code
# MAGIC
# MAGIC **15 minutes**, mostly a live demo; participants can follow along in notebook *03* in the Labs folder, which has the prompts (A.8) and the legacy procedure (A.9).
# MAGIC
# MAGIC 1. **Explore:** profile `gold.group_exposure` and ask what is unusual about the latest month compared with April.
# MAGIC 2. **Generate:** split one group's exposure change since April into an **FX effect** and a **new-drawdowns effect**, by subsidiary, and chart it. This answers the "why" behind the Credit Committee's question.
# MAGIC 3. **Explain and convert:** paste a legacy Synapse T-SQL procedure (A.9). Genie Code explains what it does, points out logic risks, and rewrites it as Databricks SQL against the workshop tables.
# MAGIC 4. **Iterate safely:**
# MAGIC    - Show the action-approval setting: by default an AI classifier approves actions within your request and blocks actions beyond it, or you can approve each one yourself.
# MAGIC    - Ask for an explanation with *"don't run any code"*.
# MAGIC    - Show that Genie Code can only reach data your Unity Catalog permissions allow.
# MAGIC    - Roll back a change with revision history.

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
