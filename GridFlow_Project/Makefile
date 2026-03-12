# ─── Makefile ─── Energy Pipeline ─────────────────────────────────────────────
.PHONY: help setup ingest-opsd ingest-nrel dbt-run dbt-test dbt-docs clean

PYTHON     ?= python3
DBT_DIR    := energy_dbt
DBT_TARGET ?= dev

help:           ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	  | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'

# ── Environment ────────────────────────────────────────────────────────────────
setup:          ## Create venv and install all dependencies
	$(PYTHON) -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt
	cp energy_dbt/profiles.yml ~/.dbt/profiles.yml
	cd $(DBT_DIR) && ../.venv/bin/dbt deps
	@echo "✓  Setup complete. Activate with: source .venv/bin/activate"

# ── Ingestion ──────────────────────────────────────────────────────────────────
ingest-opsd-load:       ## Ingest OPSD load time series → BigQuery
	$(PYTHON) scripts/ingest_data.py --source opsd --dataset load

ingest-opsd-plants:     ## Ingest OPSD renewable plant registry → BigQuery
	$(PYTHON) scripts/ingest_data.py --source opsd --dataset renewable

ingest-nrel-solar:      ## Ingest NREL solar resource data → BigQuery
	$(PYTHON) scripts/ingest_data.py --source nrel --dataset solar

ingest-dry-run:         ## Preview OPSD load without uploading
	$(PYTHON) scripts/ingest_data.py --source opsd --dataset load --dry-run

ingest-all: ingest-opsd-load ingest-opsd-plants ingest-nrel-solar  ## Run all ingestion jobs

# ── dbt ────────────────────────────────────────────────────────────────────────
dbt-seed:       ## Load seed files (country_codes.csv) into BigQuery
	cd $(DBT_DIR) && dbt seed --target $(DBT_TARGET)

dbt-run:        ## Run all dbt models
	cd $(DBT_DIR) && dbt run --target $(DBT_TARGET)

dbt-run-staging:    ## Run only staging models
	cd $(DBT_DIR) && dbt run --select staging --target $(DBT_TARGET)

dbt-run-marts:      ## Run only mart models
	cd $(DBT_DIR) && dbt run --select marts --target $(DBT_TARGET)

dbt-test:       ## Run all dbt tests
	cd $(DBT_DIR) && dbt test --target $(DBT_TARGET)

dbt-test-staging:   ## Run tests on staging models only
	cd $(DBT_DIR) && dbt test --select staging --target $(DBT_TARGET)

dbt-docs:       ## Generate and serve dbt documentation
	cd $(DBT_DIR) && dbt docs generate --target $(DBT_TARGET)
	cd $(DBT_DIR) && dbt docs serve --port 8080

dbt-compile:    ## Compile dbt without running
	cd $(DBT_DIR) && dbt compile --target $(DBT_TARGET)

dbt-debug:      ## Verify dbt connection to BigQuery
	cd $(DBT_DIR) && dbt debug --target $(DBT_TARGET)

dbt-full: dbt-seed dbt-run dbt-test     ## Seed → run → test (full pipeline)

# ── SQL schema ─────────────────────────────────────────────────────────────────
apply-schema:   ## Apply BigQuery schema DDL (requires bq CLI)
	bq query --use_legacy_sql=false < sql/bigquery_schema.sql

# ── Housekeeping ───────────────────────────────────────────────────────────────
clean:          ## Remove temporary files
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -name "*.pyc" -delete
	rm -rf $(DBT_DIR)/target $(DBT_DIR)/dbt_packages .venv data/
