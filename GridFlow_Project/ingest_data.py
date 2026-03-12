"""
Data Ingestion Agent — Energy Pipeline
Fetches data from NREL or OPSD and uploads to BigQuery staging tables.

Usage:
    python scripts/ingest_data.py --source opsd --dataset load
    python scripts/ingest_data.py --source nrel --dataset solar
    python scripts/ingest_data.py --source local --file data/my_file.csv --table raw_energy
"""

import os
import sys
import argparse
import logging
import hashlib
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

import requests
import pandas as pd
from google.cloud import bigquery
from google.api_core.exceptions import GoogleAPIError

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Configuration (override via env-vars or CLI) ──────────────────────────────
GCP_PROJECT   = os.getenv("GCP_PROJECT",   "your-gcp-project-id")
BQ_DATASET    = os.getenv("BQ_DATASET",    "energy_staging")
BQ_LOCATION   = os.getenv("BQ_LOCATION",   "US")
DATA_DIR      = Path(os.getenv("DATA_DIR", "data"))

# ── Source URLs ───────────────────────────────────────────────────────────────
SOURCES = {
    "opsd": {
        # Open Power System Data — time-series package (CC-BY 4.0)
        "load": {
            "url": (
                "https://data.open-power-system-data.org/time_series/latest/"
                "time_series_60min_singleindex.csv"
            ),
            "table": "raw_opsd_load",
            "description": "OPSD 60-min electricity load time series",
        },
        "renewable": {
            "url": (
                "https://data.open-power-system-data.org/renewable_power_plants/latest/"
                "renewable_power_plants_EU.csv"
            ),
            "table": "raw_opsd_renewable_plants",
            "description": "OPSD EU renewable power plant registry",
        },
        "weather": {
            "url": (
                "https://data.open-power-system-data.org/weather_data/latest/"
                "weather_data.csv"
            ),
            "table": "raw_opsd_weather",
            "description": "OPSD hourly weather data",
        },
    },
    "nrel": {
        # NREL provides data via API; a sample static export is used here.
        "solar": {
            "url": (
                "https://developer.nrel.gov/api/solar/solar_resource/v1.csv"
                "?api_key=DEMO_KEY&lat=40.7128&lon=-74.0060&wrad=1"
            ),
            "table": "raw_nrel_solar_resource",
            "description": "NREL solar resource data (demo key)",
        },
        "wind": {
            "url": (
                "https://raw.githubusercontent.com/NREL/OpenStudio-ERI/develop/"
                "weather/USA_CO_Denver.Intl.AP.725650_TMY3.epw"
            ),
            "table": "raw_nrel_wind_resource",
            "description": "NREL wind/weather EPW sample",
            "format": "epw",   # custom parser needed
        },
    },
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _md5(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def download_file(url: str, dest: Path, retries: int = 3) -> Path:
    """Download *url* to *dest* with retry logic; skip if already present."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        log.info("Cache hit — skipping download: %s", dest)
        return dest

    log.info("Downloading → %s", url)
    for attempt in range(1, retries + 1):
        try:
            with requests.get(url, stream=True, timeout=120) as resp:
                resp.raise_for_status()
                with open(dest, "wb") as fh:
                    for chunk in resp.iter_content(chunk_size=1 << 20):
                        fh.write(chunk)
            log.info("Saved %s (%.1f MB)", dest, dest.stat().st_size / 1e6)
            return dest
        except requests.RequestException as exc:
            log.warning("Attempt %d/%d failed: %s", attempt, retries, exc)
            if attempt < retries:
                time.sleep(5 * attempt)
    raise RuntimeError(f"Failed to download {url} after {retries} attempts")


def read_csv_resilient(path: Path) -> pd.DataFrame:
    """Read a CSV, trying common encodings and separators."""
    for enc in ("utf-8", "latin-1", "cp1252"):
        for sep in (",", ";", "\t"):
            try:
                df = pd.read_csv(path, sep=sep, encoding=enc, low_memory=False)
                if df.shape[1] > 1:
                    log.info("Parsed CSV: %d rows × %d cols  (enc=%s sep=%r)",
                             len(df), df.shape[1], enc, sep)
                    return df
            except Exception:
                continue
    raise ValueError(f"Cannot parse {path} as CSV")


def normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Snake-case columns, drop fully-empty columns, add ingestion metadata."""
    df.columns = (
        df.columns.str.strip()
                  .str.lower()
                  .str.replace(r"[^0-9a-z]+", "_", regex=True)
                  .str.strip("_")
    )
    df = df.dropna(axis=1, how="all")
    df["_ingested_at"] = datetime.now(timezone.utc).isoformat()
    df["_source_file"] = ""          # filled by caller
    return df


def upload_to_bigquery(
    df: pd.DataFrame,
    project: str,
    dataset: str,
    table: str,
    location: str = "US",
    write_disposition: str = "WRITE_TRUNCATE",
) -> None:
    """Upload *df* to BigQuery using the Storage Write API (fast path)."""
    client = bigquery.Client(project=project)
    table_ref = f"{project}.{dataset}.{table}"

    job_config = bigquery.LoadJobConfig(
        write_disposition=write_disposition,
        autodetect=True,               # schema auto-detected; override via schema.sql
        create_disposition="CREATE_IF_NEEDED",
        source_format=bigquery.SourceFormat.PARQUET,
    )

    # Convert to Parquet in-memory for efficiency
    import io
    buf = io.BytesIO()
    df.to_parquet(buf, index=False, engine="pyarrow")
    buf.seek(0)

    job = client.load_table_from_file(buf, table_ref, job_config=job_config,
                                      location=location)
    log.info("BigQuery load job started: %s", job.job_id)
    job.result()   # wait for completion
    tbl = client.get_table(table_ref)
    log.info("✓ %s  →  %d rows, %d cols", table_ref,
             tbl.num_rows, len(tbl.schema))


def create_dataset_if_missing(project: str, dataset: str, location: str) -> None:
    client = bigquery.Client(project=project)
    ds_ref = bigquery.Dataset(f"{project}.{dataset}")
    ds_ref.location = location
    try:
        client.get_dataset(ds_ref)
        log.info("Dataset %s already exists", dataset)
    except Exception:
        client.create_dataset(ds_ref, exists_ok=True)
        log.info("Created dataset %s", dataset)


# ── Source-specific loaders ───────────────────────────────────────────────────

def load_opsd(dataset_key: str) -> pd.DataFrame:
    cfg  = SOURCES["opsd"][dataset_key]
    dest = DATA_DIR / "opsd" / f"{dataset_key}.csv"
    path = download_file(cfg["url"], dest)
    df   = read_csv_resilient(path)
    df   = normalise_columns(df)
    df["_source_file"] = str(path)
    return df, cfg["table"]


def load_nrel(dataset_key: str) -> tuple[pd.DataFrame, str]:
    cfg  = SOURCES["nrel"][dataset_key]
    dest = DATA_DIR / "nrel" / f"{dataset_key}.csv"
    path = download_file(cfg["url"], dest)

    if cfg.get("format") == "epw":
        df = _parse_epw(path)
    else:
        df = read_csv_resilient(path)

    df = normalise_columns(df)
    df["_source_file"] = str(path)
    return df, cfg["table"]


def _parse_epw(path: Path) -> pd.DataFrame:
    """Minimal EPW parser — extracts hourly weather records."""
    rows = []
    with open(path, encoding="latin-1") as fh:
        for i, line in enumerate(fh):
            if i < 8:           # skip header sections
                continue
            parts = line.strip().split(",")
            if len(parts) >= 35:
                rows.append({
                    "year": parts[0], "month": parts[1], "day": parts[2],
                    "hour": parts[3], "minute": parts[4],
                    "dry_bulb_c": parts[6], "dew_point_c": parts[7],
                    "rel_humidity_pct": parts[8],
                    "atm_pressure_pa": parts[9],
                    "ghi_wm2": parts[13], "dni_wm2": parts[14],
                    "dhi_wm2": parts[15], "wind_dir_deg": parts[20],
                    "wind_speed_ms": parts[21],
                })
    return pd.DataFrame(rows)


def load_local(file_path: str, table_name: str) -> tuple[pd.DataFrame, str]:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Local file not found: {path}")
    if path.suffix.lower() == ".parquet":
        df = pd.read_parquet(path)
    else:
        df = read_csv_resilient(path)
    df = normalise_columns(df)
    df["_source_file"] = str(path)
    return df, table_name


# ── Dry-run / preview ─────────────────────────────────────────────────────────

def preview(df: pd.DataFrame, table: str) -> None:
    print(f"\n{'─'*60}")
    print(f"  Table  : {table}")
    print(f"  Shape  : {df.shape[0]:,} rows × {df.shape[1]} cols")
    print(f"  Cols   : {list(df.columns)[:10]} {'...' if df.shape[1] > 10 else ''}")
    print(f"  Sample :")
    print(df.head(3).to_string(index=False))
    print(f"{'─'*60}\n")


# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Energy Data Ingestion Agent — NREL / OPSD → BigQuery"
    )
    p.add_argument("--source",   choices=["opsd", "nrel", "local"], required=True)
    p.add_argument("--dataset",  help="Sub-dataset key  (e.g. load, solar, renewable)")
    p.add_argument("--file",     help="Path to local CSV/Parquet (--source local)")
    p.add_argument("--table",    help="BigQuery table name override")
    p.add_argument("--project",  default=GCP_PROJECT)
    p.add_argument("--bq-dataset", dest="bq_dataset", default=BQ_DATASET)
    p.add_argument("--location", default=BQ_LOCATION)
    p.add_argument("--write-mode",
                   choices=["WRITE_TRUNCATE", "WRITE_APPEND", "WRITE_EMPTY"],
                   default="WRITE_TRUNCATE")
    p.add_argument("--dry-run",  action="store_true",
                   help="Preview data without uploading to BigQuery")
    p.add_argument("--data-dir", default=str(DATA_DIR))
    return p.parse_args()


def main() -> None:
    args = parse_args()
    global DATA_DIR
    DATA_DIR = Path(args.data_dir)

    # ── Load data ──────────────────────────────────────────────────────────
    log.info("=== Energy Ingestion Agent  [source=%s] ===", args.source)
    t0 = time.time()

    if args.source == "opsd":
        if not args.dataset or args.dataset not in SOURCES["opsd"]:
            valid = list(SOURCES["opsd"].keys())
            log.error("--dataset must be one of %s for source=opsd", valid)
            sys.exit(1)
        df, table = load_opsd(args.dataset)

    elif args.source == "nrel":
        if not args.dataset or args.dataset not in SOURCES["nrel"]:
            valid = list(SOURCES["nrel"].keys())
            log.error("--dataset must be one of %s for source=nrel", valid)
            sys.exit(1)
        df, table = load_nrel(args.dataset)

    elif args.source == "local":
        if not args.file:
            log.error("--file is required when --source=local")
            sys.exit(1)
        if not args.table:
            log.error("--table is required when --source=local")
            sys.exit(1)
        df, table = load_local(args.file, args.table)

    # CLI table name override
    if args.table:
        table = args.table

    preview(df, table)

    if args.dry_run:
        log.info("Dry-run mode — skipping BigQuery upload.")
        return

    # ── Upload ─────────────────────────────────────────────────────────────
    create_dataset_if_missing(args.project, args.bq_dataset, args.location)
    upload_to_bigquery(
        df,
        project=args.project,
        dataset=args.bq_dataset,
        table=table,
        location=args.location,
        write_disposition=args.write_mode,
    )

    elapsed = time.time() - t0
    log.info("Done in %.1f s", elapsed)


if __name__ == "__main__":
    main()
