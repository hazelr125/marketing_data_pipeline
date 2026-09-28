# Marketing Data Pipeline

A small, end-to-end Python data pipeline that generates synthetic marketing data, loads it into a SQLite warehouse, applies analytical transformations, and runs automated data-quality checks.

The project is designed to demonstrate common data engineering concerns such as:

- Synthetic source-data generation
- Raw/staging-layer ingestion
- Schema drift and inconsistent casing
- Duplicate records and missing values
- Referential integrity validation
- SQL-based transformation and KPI calculation
- Idempotent pipeline execution

## Pipeline overview

```text
Synthetic data generation
        |
        v
CSV files: CRM, email, web analytics
        |
        v
SQLite raw/staging tables
        |
        v
Data quality checks + SQL transformations
        |
        v
campaign_performance table
```

## Project files

| File | Description |
| --- | --- |
| [`data_generator.py`](data_generator.py) | Creates synthetic CRM, email-export, and web-analytics CSV files with intentional data-quality issues. |
| [`ingestion.py`](ingestion.py) | Creates SQLite raw tables and bulk-loads the generated CSV files. |
| [`transformation.py`](transformation.py) | Cleans, aggregates, and joins the raw tables into the `campaign_performance` table. |
| [`dq_checks.py`](dq_checks.py) | Runs automated checks for duplicates, null rates, referential integrity, value ranges, and stale dates. |

## Generated data

Running the generator creates:

- `crm_customers.csv` — customer records, including duplicate customer IDs
- `email_export.csv` — email sends with null metrics, inconsistent campaign casing, and stale dates
- `web_analytics.csv` — web sessions with inconsistent campaign casing and a renamed campaign column (`utm_cmpgn_name_v2`)

The generated data intentionally contains issues so the ingestion, transformation, and data-quality logic can be exercised.

## Requirements

- Python 3.9 or newer
- `pandas`
- `numpy`
- SQLite, included with Python through the standard-library `sqlite3` module

Install the Python dependencies with:

```bash
python -m pip install pandas numpy
```

For an isolated environment:

```bash
python -m venv .venv
source .venv/bin/activate       # macOS/Linux
# .venv\\Scripts\\activate    # Windows PowerShell
python -m pip install pandas numpy
```

## Usage

Run the scripts from the repository root in this order.

### 1. Generate source data

```bash
python data_generator.py
```

This creates the three CSV input files in the current directory.

### 2. Ingest the CSV files

```bash
python ingestion.py
```

This creates `marketing_warehouse.db` and loads the CSV data into these raw tables:

- `raw_crm_customers`
- `raw_email_export`
- `raw_web_analytics`

The ingestion step recreates the raw tables on each run, making it safe to rerun from a clean raw layer.

### 3. Build campaign performance metrics

```bash
python transformation.py
```

This creates the `campaign_performance` table and calculates:

- Total email sends
- Total opens
- Total clicks
- Total web sessions
- Open rate
- Click-through rate

Campaign names are normalized to uppercase before aggregation, and missing metric values are treated as zero for aggregate calculations.

### 4. Run data-quality checks

```bash
python dq_checks.py
```

The validation suite checks:

- Duplicate IDs in raw and curated tables
- Null-rate thresholds
- Referential integrity between email sends and CRM customers
- Numeric and rate ranges
- Stale email send dates

Because the source data intentionally contains quality problems, some checks are expected to fail. These failures are useful for demonstrating how the validator reports issues.

## Outputs

After a complete run, the repository directory will contain generated artifacts similar to:

```text
crm_customers.csv
email_export.csv
web_analytics.csv
marketing_warehouse.db
```

These files are runtime outputs and can be deleted and regenerated at any time.

## Data model

### Raw layer

The raw layer stores source data with permissive types so that imperfect source records can be ingested before validation and transformation.

### Curated layer

The `campaign_performance` table provides one row per normalized campaign and includes aggregated engagement metrics and calculated rates.

## Notes

- The pipeline uses randomly generated data, so exact row-level results vary between runs.
- The scripts use relative file paths; run them from the repository root.
- The SQLite database is recreated or overwritten as part of the ingestion and transformation workflow.
- This is an educational/demo project and is not intended as a production-ready orchestration framework.

## License

No license has been specified for this repository yet.
