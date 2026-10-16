-- Databricks notebook source
-- MAGIC %md
-- MAGIC # 04 · Facilitator progress board
-- MAGIC
-- MAGIC Queries behind the live board on the projector. `06_deploy_dashboards_and_agents` builds and publishes the
-- MAGIC board (**SMBC Workshop: progress board**) with the same queries (kept in `tools/dashboards.py`), so there's nothing
-- MAGIC to run here; use this notebook to try a query on its own. The board needs nothing from participants beyond the two one-line inserts at the bottom:
-- MAGIC the rest is read live from Unity Catalog's information schema. Present it full screen while the labs run.
-- MAGIC
-- MAGIC Uses catalog `smbc_workshop`; find-and-replace it if yours is named differently.

-- COMMAND ----------

-- MAGIC %md ### Headline counters: checked in, Lab 1 finished, Lab 2 answered correctly

-- COMMAND ----------

WITH participant_schemas AS (
  SELECT schema_name
  FROM smbc_workshop.information_schema.schemata
  WHERE schema_name NOT IN ('information_schema', 'default', 'raw', 'checkpoint', 'ops')
),
lab1 AS (
  SELECT DISTINCT table_schema
  FROM smbc_workshop.information_schema.tables
  WHERE table_schema IN (SELECT schema_name FROM participant_schemas)
    AND lower(table_name) LIKE '%group_exposure%'
)
SELECT
  (SELECT count(DISTINCT user_email) FROM smbc_workshop.ops.checkin) AS checked_in,
  (SELECT count(*) FROM lab1) AS lab1_finished,
  (SELECT count(DISTINCT user_email) FROM smbc_workshop.ops.lab_answers
   WHERE lab = 'lab2' AND lower(answer) LIKE '%orchid%') AS lab2_found_orchid;

-- COMMAND ----------

-- MAGIC %md ### Per-person progress (sort: furthest along first)

-- COMMAND ----------

WITH participant_schemas AS (
  SELECT schema_name
  FROM smbc_workshop.information_schema.schemata
  WHERE schema_name NOT IN ('information_schema', 'default', 'raw', 'checkpoint', 'ops')
),
tables AS (
  SELECT table_schema, lower(table_name) AS table_name, created
  FROM smbc_workshop.information_schema.tables
)
SELECT
  p.schema_name AS participant,
  count(t.table_name) AS tables_written,
  max(CASE WHEN t.table_name LIKE '%quarantine%' THEN 1 ELSE 0 END) AS quarantine_table,
  max(CASE WHEN t.table_name LIKE '%facility_exposure%' THEN 1 ELSE 0 END) AS facility_gold,
  max(CASE WHEN t.table_name LIKE '%group_exposure%' THEN 1 ELSE 0 END) AS group_gold,
  min(t.created) AS first_table_at,
  max(t.created) AS latest_table_at
FROM participant_schemas p
LEFT JOIN tables t ON t.table_schema = p.schema_name
GROUP BY p.schema_name
ORDER BY group_gold DESC, quarantine_table DESC, tables_written DESC, first_table_at;

-- COMMAND ----------

-- MAGIC %md ### First to finish (for the "First green Lab 1" prize)

-- COMMAND ----------

SELECT table_schema AS participant, min(created) AS finished_at
FROM smbc_workshop.information_schema.tables
WHERE lower(table_name) LIKE '%group_exposure%'
  AND table_schema NOT IN ('checkpoint', 'raw', 'ops', 'default', 'information_schema')
GROUP BY table_schema
ORDER BY finished_at
LIMIT 10;

-- COMMAND ----------

-- MAGIC %md ### Lab 2 answers as they come in

-- COMMAND ----------

SELECT user_email, answer, submitted_at, lower(answer) LIKE '%orchid%' AS correct
FROM smbc_workshop.ops.lab_answers
WHERE lab = 'lab2'
ORDER BY submitted_at;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### The two lines participants run (copy into the lab guide / cheat sheet)
-- MAGIC
-- MAGIC **Check-in** (arrival): replace `DA` with `DE` if you're a data engineer.
-- MAGIC ```sql
-- MAGIC INSERT INTO smbc_workshop.ops.checkin SELECT current_user(), 'DA', current_timestamp();
-- MAGIC ```
-- MAGIC **Lab 2 checkpoint**: put the name of the group you found in the quotes.
-- MAGIC ```sql
-- MAGIC INSERT INTO smbc_workshop.ops.lab_answers SELECT current_user(), 'lab2', '<group name>', current_timestamp();
-- MAGIC ```
