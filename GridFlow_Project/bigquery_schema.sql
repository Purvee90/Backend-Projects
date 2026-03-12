-- =============================================================================
-- BigQuery Schema Definition — Energy Pipeline
-- Project  : <your-gcp-project-id>
-- Datasets : energy_staging  (raw ingest)
--            energy_dbt      (dbt-managed transforms)
-- =============================================================================

-- ─────────────────────────────────────────────────────────────────────────────
-- 0.  DATASETS
-- ─────────────────────────────────────────────────────────────────────────────

CREATE SCHEMA IF NOT EXISTS `<your-gcp-project-id>.energy_staging`
  OPTIONS (
    description = 'Raw ingested energy data — managed by ingest_data.py',
    location    = 'US'
  );

CREATE SCHEMA IF NOT EXISTS `<your-gcp-project-id>.energy_dbt`
  OPTIONS (
    description = 'Transformed energy data — managed by dbt',
    location    = 'US'
  );


-- ─────────────────────────────────────────────────────────────────────────────
-- 1.  STAGING TABLES  (energy_staging dataset)
-- ─────────────────────────────────────────────────────────────────────────────

-- 1a. OPSD 60-minute load time series
CREATE OR REPLACE TABLE `<your-gcp-project-id>.energy_staging.raw_opsd_load`
(
  utc_timestamp          TIMESTAMP    OPTIONS(description='UTC timestamp of observation'),
  cet_cest_timestamp     STRING       OPTIONS(description='CET/CEST local timestamp'),

  -- DE (Germany)
  de_load_actual_entsoe_transparency  FLOAT64  OPTIONS(description='DE actual load MW – ENTSO-E'),
  de_load_forecast_entsoe_transparency FLOAT64 OPTIONS(description='DE day-ahead forecast MW'),

  -- AT (Austria)
  at_load_actual_entsoe_transparency  FLOAT64,
  at_load_forecast_entsoe_transparency FLOAT64,

  -- GB (Great Britain)
  gb_gbn_load_actual_entsoe_transparency  FLOAT64,
  gb_gbn_load_forecast_entsoe_transparency FLOAT64,

  -- Metadata
  _ingested_at    TIMESTAMP  OPTIONS(description='Row ingestion timestamp (UTC)'),
  _source_file    STRING     OPTIONS(description='Source file path or URL')
)
PARTITION BY DATE(utc_timestamp)
CLUSTER BY utc_timestamp
OPTIONS (
  description          = 'OPSD hourly electricity load – raw staging',
  require_partition_filter = FALSE
);


-- 1b. OPSD renewable power plants registry
CREATE OR REPLACE TABLE `<your-gcp-project-id>.energy_staging.raw_opsd_renewable_plants`
(
  id                   STRING   OPTIONS(description='Unique plant ID'),
  energy_source_level_1 STRING,
  energy_source_level_2 STRING,
  energy_source_level_3 STRING,
  technology           STRING,
  data_source          STRING,
  country              STRING,
  capacity             FLOAT64  OPTIONS(description='Installed capacity in MW'),
  lat                  FLOAT64,
  lon                  FLOAT64,
  municipality         STRING,
  nuts_1_region        STRING,
  commissioning_date   DATE,
  decommissioning_date DATE,
  comment              STRING,

  _ingested_at    TIMESTAMP,
  _source_file    STRING
)
OPTIONS (description = 'OPSD EU renewable power plant registry – raw staging');


-- 1c. OPSD weather data
CREATE OR REPLACE TABLE `<your-gcp-project-id>.energy_staging.raw_opsd_weather`
(
  utc_timestamp     TIMESTAMP,
  lat               FLOAT64,
  lon               FLOAT64,
  radiation_direct_horizontal   FLOAT64  OPTIONS(description='W/m²'),
  radiation_diffuse_horizontal  FLOAT64  OPTIONS(description='W/m²'),
  temperature                   FLOAT64  OPTIONS(description='°C at 2 m'),
  wind_speed                    FLOAT64  OPTIONS(description='m/s at 10 m'),

  _ingested_at    TIMESTAMP,
  _source_file    STRING
)
PARTITION BY DATE(utc_timestamp)
CLUSTER BY lat, lon
OPTIONS (description = 'OPSD hourly weather data – raw staging');


-- 1d. NREL solar resource (API export)
CREATE OR REPLACE TABLE `<your-gcp-project-id>.energy_staging.raw_nrel_solar_resource`
(
  period_start       TIMESTAMP,
  period_end         TIMESTAMP,
  latitude           FLOAT64,
  longitude          FLOAT64,
  elevation_m        FLOAT64,
  ghi_wm2            FLOAT64  OPTIONS(description='Global Horizontal Irradiance W/m²'),
  dni_wm2            FLOAT64  OPTIONS(description='Direct Normal Irradiance W/m²'),
  dhi_wm2            FLOAT64  OPTIONS(description='Diffuse Horizontal Irradiance W/m²'),
  air_temperature_c  FLOAT64,
  wind_speed_ms      FLOAT64,
  surface_pressure_mbar FLOAT64,

  _ingested_at    TIMESTAMP,
  _source_file    STRING
)
PARTITION BY DATE(period_start)
CLUSTER BY latitude, longitude
OPTIONS (description = 'NREL solar resource data – raw staging');


-- 1e. NREL wind / weather (EPW-derived)
CREATE OR REPLACE TABLE `<your-gcp-project-id>.energy_staging.raw_nrel_wind_resource`
(
  year               INT64,
  month              INT64,
  day                INT64,
  hour               INT64,
  minute             INT64,
  dry_bulb_c         FLOAT64,
  dew_point_c        FLOAT64,
  rel_humidity_pct   FLOAT64,
  atm_pressure_pa    FLOAT64,
  ghi_wm2            FLOAT64,
  dni_wm2            FLOAT64,
  dhi_wm2            FLOAT64,
  wind_dir_deg       FLOAT64,
  wind_speed_ms      FLOAT64,

  _ingested_at    TIMESTAMP,
  _source_file    STRING
)
OPTIONS (description = 'NREL EPW weather file – raw staging');


-- ─────────────────────────────────────────────────────────────────────────────
-- 2.  AUDIT / CONTROL TABLE
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS `<your-gcp-project-id>.energy_staging._ingest_audit`
(
  run_id          STRING     NOT NULL  OPTIONS(description='UUID for each run'),
  source          STRING     NOT NULL,
  dataset_key     STRING     NOT NULL,
  bq_table        STRING     NOT NULL,
  rows_loaded     INT64,
  file_md5        STRING,
  status          STRING     OPTIONS(description='SUCCESS | FAILED'),
  error_message   STRING,
  started_at      TIMESTAMP,
  finished_at     TIMESTAMP
)
OPTIONS (description = 'Ingestion run audit log');


-- ─────────────────────────────────────────────────────────────────────────────
-- 3.  USEFUL VIEWS  (convenience layer over raw tables)
-- ─────────────────────────────────────────────────────────────────────────────

-- Latest load snapshot for Germany
CREATE OR REPLACE VIEW `<your-gcp-project-id>.energy_staging.v_de_load_latest` AS
SELECT
  utc_timestamp,
  de_load_actual_entsoe_transparency   AS load_actual_mw,
  de_load_forecast_entsoe_transparency AS load_forecast_mw,
  SAFE_DIVIDE(
    de_load_actual_entsoe_transparency - de_load_forecast_entsoe_transparency,
    de_load_forecast_entsoe_transparency
  ) * 100                              AS forecast_error_pct
FROM `<your-gcp-project-id>.energy_staging.raw_opsd_load`
WHERE de_load_actual_entsoe_transparency IS NOT NULL
ORDER BY utc_timestamp DESC;
