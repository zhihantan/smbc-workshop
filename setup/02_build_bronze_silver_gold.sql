-- Databricks notebook source
-- MAGIC %md
-- MAGIC # 02 · Build the bronze, silver and gold reference tables
-- MAGIC
-- MAGIC The reference solution for Lab 1, written as plain SQL in the medallion layout. It turns the raw extracts in
-- MAGIC `/Volumes/smbc_workshop/raw/landing/` into the tables Lab 2 and the Genie Code segment use, so anyone whose
-- MAGIC Lab 1 isn't finished can carry on from `smbc_workshop.gold`:
-- MAGIC
-- MAGIC | Schema | Tables |
-- MAGIC |---|---|
-- MAGIC | `bronze` | `counterparties`, `facilities`, `balances`: the extracts exactly as delivered |
-- MAGIC | `silver` | `counterparties`, `facilities`, `balances`, `fx_rates`, `group_limits`: cleaned, typed and de-duplicated; plus `facilities_all` and `silver.quarantine_facilities`, the rows held back with a reason |
-- MAGIC | `gold` | `facility_exposure` and `group_exposure`: what Lab 2 and Genie use |
-- MAGIC
-- MAGIC Run after `01_setup_workspace`, which creates the schemas, on serverless compute or a serverless SQL warehouse.
-- MAGIC It uses the catalog `smbc_workshop`; if yours is named differently, find-and-replace it in this file.
-- MAGIC
-- MAGIC The cleaning rules are the ones participants apply in Lab 1, and the same ones
-- MAGIC `data/validate_data.py` checks against the answer key:
-- MAGIC
-- MAGIC 1. Counterparties: drop exact duplicate rows.
-- MAGIC 2. Facilities: trim and upper-case currency codes, map `US$`→`USD`, `S$`→`SGD`, `RMB`→`CNY`; parse dates
-- MAGIC    written as `YYYY-MM-DD` or `DD/MM/YYYY`; quarantine rows with an unknown counterparty, a commitment of
-- MAGIC    zero or less, a maturity before the start date, an unknown currency, or an unreadable date.
-- MAGIC 3. Balances: parse both date formats; keep one row per `facility_id` + `as_of_date` (the latest `extract_ts`).
-- MAGIC 4. FX: rates are dated on the last business day of each month, so join on currency **and month**.
-- MAGIC 5. Exposure = drawn balance × that month's rate, in USD and JPY; utilisation = group exposure ÷ group limit.

-- COMMAND ----------

USE CATALOG smbc_workshop;

-- COMMAND ----------

-- MAGIC %md ## Bronze: the extracts exactly as delivered (everything read as text, so nothing is silently coerced)

-- COMMAND ----------

CREATE OR REPLACE TABLE bronze.counterparties
COMMENT 'Raw customer-master extract, as delivered. SYNTHETIC DATA for the SMBC Data & AI Workshop.' AS
SELECT counterparty_id, counterparty_name, counterparty_name_local, parent_group_id, country_code, sector,
       internal_rating, relationship_manager, onboarded_on, last_updated_at
FROM read_files(
  '/Volumes/smbc_workshop/raw/landing/counterparties/',
  format => 'csv', header => true,
  schema => 'counterparty_id STRING, counterparty_name STRING, counterparty_name_local STRING,
             parent_group_id STRING, country_code STRING, sector STRING, internal_rating STRING,
             relationship_manager STRING, onboarded_on STRING, last_updated_at STRING');

CREATE OR REPLACE TABLE bronze.facilities
COMMENT 'Raw facility extract (JSON Lines), as delivered. SYNTHETIC DATA for the SMBC Data & AI Workshop.' AS
SELECT facility_id, counterparty_id, product_type, currency, committed_amount, start_date, maturity_date,
       booking_branch, secured, collateral, source_system
FROM read_files(
  '/Volumes/smbc_workshop/raw/landing/facilities/',
  format => 'json',
  schema => 'facility_id STRING, counterparty_id STRING, product_type STRING, currency STRING,
             committed_amount DOUBLE, start_date STRING, maturity_date STRING, booking_branch STRING,
             secured BOOLEAN, collateral STRUCT<type: STRING, value_usd: DOUBLE>, source_system STRING');

CREATE OR REPLACE TABLE bronze.balances
COMMENT 'Raw month-end balance extracts, as delivered. SYNTHETIC DATA for the SMBC Data & AI Workshop.' AS
SELECT as_of_date, facility_id, drawn_amount, days_past_due, source_system, extract_ts
FROM read_files(
  '/Volumes/smbc_workshop/raw/landing/monthly_balances/',
  format => 'csv', header => true,
  schema => 'as_of_date STRING, facility_id STRING, drawn_amount STRING, days_past_due STRING,
             source_system STRING, extract_ts STRING');

-- COMMAND ----------

-- MAGIC %md ## Silver: cleaned, typed, de-duplicated

-- COMMAND ----------

CREATE OR REPLACE TABLE silver.counterparties
COMMENT 'Customer master, one row per counterparty (exact duplicate rows removed). SYNTHETIC DATA.' AS
SELECT DISTINCT
  counterparty_id,
  counterparty_name,
  counterparty_name_local,
  parent_group_id,
  country_code,
  sector,
  CAST(internal_rating AS INT) AS internal_rating,
  relationship_manager,
  CAST(onboarded_on AS DATE) AS onboarded_on,
  CAST(last_updated_at AS TIMESTAMP) AS last_updated_at
FROM bronze.counterparties;

CREATE OR REPLACE TABLE silver.fx_rates
COMMENT 'Month-end FX rates. rate_date is the last business day of the month; join on rate_month. SYNTHETIC DATA.' AS
SELECT
  CAST(rate_date AS DATE) AS rate_date,
  trunc(CAST(rate_date AS DATE), 'MM') AS rate_month,
  currency_code,
  usd_rate,
  jpy_rate
FROM read_files(
  '/Volumes/smbc_workshop/raw/landing/fx_rates/',
  format => 'csv', header => true,
  schema => 'rate_date STRING, currency_code STRING, usd_rate DOUBLE, jpy_rate DOUBLE');

-- The risk team's limits spreadsheet. The CSV copy in the facilitator volume holds the same rows as
-- landing/group_limits/group_limits.xlsx. To read the Excel file directly instead, use:
--   read_files('/Volumes/smbc_workshop/raw/landing/group_limits/', format => 'excel', headerRows => 1,
--              schemaEvolutionMode => 'none')
CREATE OR REPLACE TABLE silver.group_limits
COMMENT 'Approved credit limit per counterparty group (from the risk team spreadsheet). SYNTHETIC DATA.' AS
SELECT
  group_id,
  group_name,
  home_country,
  primary_sector,
  CAST(group_limit_usd AS DECIMAL(20, 2)) AS group_limit_usd,
  CAST(limit_approved_on AS DATE) AS limit_approved_on,
  credit_officer
FROM read_files(
  '/Volumes/smbc_workshop/raw/facilitator/group_limits.csv',
  format => 'csv', header => true,
  schema => 'group_id STRING, group_name STRING, home_country STRING, primary_sector STRING,
             group_limit_usd DOUBLE, limit_approved_on STRING, credit_officer STRING');

CREATE OR REPLACE TABLE silver.facilities_all
COMMENT 'Facilities with standardised currency codes and parsed dates, plus the reason a row is quarantined (if any). SYNTHETIC DATA.' AS
WITH typed AS (
  SELECT
    facility_id,
    counterparty_id,
    product_type,
    currency AS currency_raw,
    CASE upper(trim(currency))
      WHEN 'US$' THEN 'USD'
      WHEN 'S$' THEN 'SGD'
      WHEN 'RMB' THEN 'CNY'
      ELSE upper(trim(currency))
    END AS currency,
    committed_amount,
    coalesce(to_date(try_to_timestamp(start_date, 'yyyy-MM-dd')),
             to_date(try_to_timestamp(start_date, 'dd/MM/yyyy'))) AS start_date,
    coalesce(to_date(try_to_timestamp(maturity_date, 'yyyy-MM-dd')),
             to_date(try_to_timestamp(maturity_date, 'dd/MM/yyyy'))) AS maturity_date,
    booking_branch,
    secured,
    collateral.type AS collateral_type,
    collateral.value_usd AS collateral_value_usd,
    source_system
  FROM bronze.facilities
)
SELECT
  t.*,
  CASE
    WHEN c.counterparty_id IS NULL THEN 'UNKNOWN_COUNTERPARTY'
    WHEN t.committed_amount <= 0 THEN 'NON_POSITIVE_COMMITMENT'
    WHEN t.maturity_date < t.start_date THEN 'MATURITY_BEFORE_START'
    WHEN x.currency_code IS NULL THEN 'UNKNOWN_CURRENCY'
    WHEN t.start_date IS NULL OR t.maturity_date IS NULL THEN 'BAD_DATE'
  END AS quarantine_reason
FROM typed t
LEFT JOIN (SELECT DISTINCT counterparty_id FROM silver.counterparties) c ON t.counterparty_id = c.counterparty_id
LEFT JOIN (SELECT DISTINCT currency_code FROM silver.fx_rates) x ON t.currency = x.currency_code;

CREATE OR REPLACE TABLE silver.quarantine_facilities
COMMENT 'Facilities held back by the data-quality checks, with the reason. SYNTHETIC DATA.' AS
SELECT * FROM silver.facilities_all WHERE quarantine_reason IS NOT NULL;

CREATE OR REPLACE TABLE silver.facilities
COMMENT 'Facilities that passed every data-quality check. SYNTHETIC DATA.' AS
SELECT * EXCEPT (quarantine_reason) FROM silver.facilities_all WHERE quarantine_reason IS NULL;

CREATE OR REPLACE TABLE silver.balances
COMMENT 'Month-end drawn balances, one row per facility and month (re-loaded extract rows removed, latest extract_ts kept). SYNTHETIC DATA.' AS
SELECT *
FROM (
  SELECT
    facility_id,
    coalesce(to_date(try_to_timestamp(as_of_date, 'yyyy-MM-dd')),
             to_date(try_to_timestamp(as_of_date, 'dd/MM/yyyy'))) AS as_of_date,
    CAST(drawn_amount AS DECIMAL(20, 2)) AS drawn_amount,
    CAST(days_past_due AS INT) AS days_past_due,
    source_system,
    CAST(extract_ts AS TIMESTAMP) AS extract_ts
  FROM bronze.balances
)
QUALIFY row_number() OVER (PARTITION BY facility_id, as_of_date ORDER BY extract_ts DESC) = 1;

-- COMMAND ----------

-- MAGIC %md ## Gold: what Lab 2 and Genie use

-- COMMAND ----------

CREATE OR REPLACE TABLE gold.facility_exposure (
  as_of_date DATE COMMENT 'Month-end reporting date',
  facility_id STRING COMMENT 'Credit facility identifier',
  product_type STRING COMMENT 'Term Loan, Revolving Credit Facility, Working Capital Loan, Project Finance Loan, or Trade Finance',
  booking_branch STRING COMMENT 'Booking branch code: SIN Singapore, HKG Hong Kong, BKK Bangkok, SGN Ho Chi Minh City, JKT Jakarta, BOM Mumbai, SYD Sydney, SEL Seoul, SHA Shanghai, KUL Kuala Lumpur, MNL Manila, TPE Taipei',
  source_system STRING COMMENT 'CORE_LOANS or TRADE_FIN',
  currency STRING COMMENT 'ISO 4217 currency of the facility',
  counterparty_id STRING COMMENT 'Borrowing legal entity',
  counterparty_name STRING COMMENT 'Borrower name in English',
  counterparty_name_local STRING COMMENT 'Borrower name in local script, where available',
  country_code STRING COMMENT 'Borrower country (ISO 3166 alpha-2)',
  sector STRING COMMENT 'Borrower industry sector',
  internal_rating INT COMMENT 'Internal credit rating, 1 (strongest) to 10 (weakest)',
  parent_group_id STRING COMMENT 'Counterparty group the borrower belongs to',
  group_name STRING COMMENT 'Counterparty group name',
  drawn_amount_local DECIMAL(20, 2) COMMENT 'Drawn balance in the facility currency',
  usd_rate DOUBLE COMMENT 'USD per 1 unit of the facility currency at month end',
  jpy_rate DOUBLE COMMENT 'JPY per 1 unit of the facility currency at month end',
  exposure_usd DOUBLE COMMENT 'Drawn balance converted to USD',
  exposure_jpy DOUBLE COMMENT 'Drawn balance converted to JPY',
  days_past_due INT COMMENT 'Days past due at month end; more than 30 counts as in arrears'
)
COMMENT 'Month-end exposure per credit facility with borrower and group attributes. Exposure means drawn balance. SYNTHETIC DATA for the SMBC Data & AI Workshop.';

INSERT OVERWRITE gold.facility_exposure
SELECT
  b.as_of_date,
  f.facility_id,
  f.product_type,
  f.booking_branch,
  f.source_system,
  f.currency,
  c.counterparty_id,
  c.counterparty_name,
  c.counterparty_name_local,
  c.country_code,
  c.sector,
  c.internal_rating,
  g.group_id,
  g.group_name,
  b.drawn_amount,
  x.usd_rate,
  x.jpy_rate,
  b.drawn_amount * x.usd_rate,
  b.drawn_amount * x.jpy_rate,
  b.days_past_due
FROM silver.balances b
JOIN silver.facilities f ON b.facility_id = f.facility_id
JOIN silver.counterparties c ON f.counterparty_id = c.counterparty_id
JOIN silver.group_limits g ON c.parent_group_id = g.group_id
JOIN silver.fx_rates x ON x.currency_code = f.currency AND x.rate_month = trunc(b.as_of_date, 'MM');

CREATE OR REPLACE TABLE gold.group_exposure (
  as_of_date DATE COMMENT 'Month-end reporting date',
  parent_group_id STRING COMMENT 'Counterparty group identifier',
  group_name STRING COMMENT 'Counterparty group name',
  group_limit_usd DECIMAL(20, 2) COMMENT 'Approved credit limit for the whole group, in USD',
  exposure_usd DOUBLE COMMENT 'Total drawn balance across all group members, in USD',
  exposure_jpy DOUBLE COMMENT 'Total drawn balance across all group members, in JPY',
  utilisation_pct DOUBLE COMMENT 'Exposure as a percentage of the group limit',
  counterparties BIGINT COMMENT 'Number of group members with a balance that month',
  facilities BIGINT COMMENT 'Number of facilities with a balance that month'
)
COMMENT 'Month-end exposure and limit utilisation per counterparty group, aggregated across all subsidiaries and countries. SYNTHETIC DATA for the SMBC Data & AI Workshop.';

INSERT OVERWRITE gold.group_exposure
SELECT
  e.as_of_date,
  e.parent_group_id,
  e.group_name,
  g.group_limit_usd,
  SUM(e.exposure_usd),
  SUM(e.exposure_jpy),
  ROUND(100 * SUM(e.exposure_usd) / g.group_limit_usd, 2),
  COUNT(DISTINCT e.counterparty_id),
  COUNT(DISTINCT e.facility_id)
FROM gold.facility_exposure e
JOIN silver.group_limits g ON e.parent_group_id = g.group_id
GROUP BY e.as_of_date, e.parent_group_id, e.group_name, g.group_limit_usd;

-- COMMAND ----------

-- MAGIC %md ## Quick look (the full comparison with the answer key is in `03_validate_bronze_silver_gold`)

-- COMMAND ----------

SELECT as_of_date, group_name, ROUND(exposure_usd / 1e6, 1) AS exposure_usd_m, utilisation_pct
FROM gold.group_exposure
WHERE as_of_date IN ('2026-06-30', '2026-09-30')
QUALIFY row_number() OVER (PARTITION BY as_of_date ORDER BY exposure_usd DESC) <= 5
ORDER BY as_of_date, exposure_usd DESC;
