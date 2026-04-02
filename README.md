# Olist E-Commerce Data Pipeline

An end-to-end data pipeline that ingests raw Olist e-commerce data from CSV files into PostgreSQL, transforms it through a dimensional model using dbt, and orchestrates the entire workflow with Apache Airflow — all running in Docker.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Data Pipeline Flow](#data-pipeline-flow)
- [Data Sources](#data-sources)
- [dbt Models](#dbt-models)
  - [Staging Layer](#staging-layer)
  - [Marts Layer](#marts-layer)
- [Data Tests](#data-tests)
- [Airflow DAG](#airflow-dag)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Setup](#setup)
  - [Running the Pipeline](#running-the-pipeline)
- [Challenges & Solutions](#challenges--solutions)
- [Key Design Decisions](#key-design-decisions)

---

## Overview

This project builds a complete data pipeline for the [Olist Brazilian E-Commerce dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce). It demonstrates a modern data stack approach:

1. **Ingest** — A Python script loads 9 CSV files into a PostgreSQL `olist_raw` schema using a truncate-and-reload strategy for idempotent re-runs.
2. **Transform** — dbt models clean, rename, and restructure the raw data into staging views and analytical mart tables following a star schema.
3. **Test** — dbt runs schema tests (unique, not_null, accepted_values, relationships) and custom data quality assertions.
4. **Orchestrate** — Apache Airflow coordinates the three steps in sequence via a single DAG scheduled to run daily.

---

## Architecture

<img width="1236" height="431" alt="Week 5 Mini Pipeline Architecture Diagram-Copy of Page-1 drawio (1)" src="https://github.com/user-attachments/assets/f56b066d-ef6d-4ac4-a35a-01169f54f83f" />

The entire pipeline runs inside **Docker**. Key components:

- **Ingestion Layer** — `ingest_olist.py` reads 9 Kaggle Olist CSV files and loads them into a PostgreSQL **Raw Schema** (`olist_raw`). On first run it creates each table; on subsequent runs it truncates and reloads, preserving table structure.
- **Orchestration Layer (Airflow)** — Apache Airflow orchestrates the end-to-end workflow: ingestion → dbt run → dbt test, running on a `@daily` schedule. All tasks use `BashOperator` for consistency and process isolation.
- **Staging Layer (dbt)** — dbt cleans and standardizes raw tables into views in the `olist_staging` schema.
- **Mart Layer (dbt)** — dbt materializes dimensional and fact tables into the `olist_analytics` schema following a star schema design.
- **Visualization** — The `olist_analytics` schema is ready for downstream BI tools such as Power BI.

---

## Tech Stack

| Tool                        | Purpose                                                                      |
| --------------------------- | ---------------------------------------------------------------------------- |
| **Python 3.10**             | CSV ingestion script (`ingest_olist.py`)                                     |
| **PostgreSQL**              | Data warehouse (raw, staging, analytics schemas)                             |
| **dbt-core 1.5 / 1.7**      | Data transformation & testing (1.5.9 in Airflow, 1.7.6 standalone container) |
| **Apache Airflow 2.8**      | Workflow orchestration                                                       |
| **Docker & Docker Compose** | Containerized infrastructure                                                 |
| **dbt_utils**               | Additional dbt test utilities                                                |

---

## Project Structure

```
olist-ecommerce-data-pipeline/
├── .env.example                    # Example environment variables
├── docker-compose.example.yml      # Example Docker Compose template
├── airflow/
│   ├── Dockerfile                  # Airflow image with dbt + Docker provider
│   ├── requirements.txt            # Python deps for Airflow workers
│   ├── dags/
│   │   └── olist_pipeline_dag_bash.py     # Main DAG (BashOperator, @daily)
│   ├── datasets/                   # 9 Olist CSV source files
│   └── logs/                       # Airflow task logs
├── dbt/
│   ├── dbt_project.yml             # dbt project config
│   ├── profiles.yml.example        # Example dbt connection profile
│   ├── packages.yml                # dbt_utils dependency
│   ├── macros/
│   │   └── get_custom_schema.sql   # Custom schema naming macro
│   ├── models/
│   │   ├── staging/olist/          # 9 staging views + source/model YAML
│   │   ├── intermediate/          # (reserved for future use)
│   │   └── marts/core/            # Dimension & fact tables + model YAML
│   └── tests/                      # Custom singular data tests + schema.yml
├── scripts/
│   ├── Dockerfile                  # Standalone Python app image
│   └── ingest_olist.py             # CSV → PostgreSQL ingestion script
└── postgres/
    └── init.sql                    # DB bootstrap (creates sample table)
```

---

## Data Pipeline Flow

```
CSV Files ──► Python Ingestion ──► olist_raw (9 tables)
                                        │
                                        ▼
                                  dbt staging layer
                                  olist_staging (9 views)
                                        │
                                        ▼
                                  dbt marts layer
                                  olist_analytics (5 tables)
                                        │
                                        ▼
                                  dbt tests (schema + singular)
```

**Step 1 — Ingest:** `ingest_olist.py` reads each CSV, checks if the target table already exists, truncates it if so (preserving schema), or creates it fresh. Connection details are configurable via `DB_HOST` and `DB_PORT` environment variables (`localhost:5433` locally, `postgres:5432` in Docker).

**Step 2 — Transform:** dbt builds 9 staging views that clean and rename columns, cast timestamps, round monetary values, and deduplicate reviews. It then builds 5 mart tables (4 dimensions + 1 fact) following a star schema.

**Step 3 — Test:** dbt runs schema-level tests (unique, not_null, accepted_values, relationships, expression_is_true) and 3 custom singular tests for business rule validation.

---

## Data Sources

The pipeline processes 9 datasets from the [Olist Brazilian E-Commerce public dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce):

| CSV File                                | Raw Table                           | Description                                   |
| --------------------------------------- | ----------------------------------- | --------------------------------------------- |
| `olist_customers_dataset.csv`           | `olist_customers`                   | Customer profiles and locations               |
| `olist_orders_dataset.csv`              | `olist_orders`                      | Order headers with status and timestamps      |
| `olist_order_items_dataset.csv`         | `olist_order_items`                 | Line items per order (product, seller, price) |
| `olist_order_payments_dataset.csv`      | `olist_order_payments`              | Payment methods and installments              |
| `olist_order_reviews_dataset.csv`       | `olist_order_reviews`               | Customer review scores and comments           |
| `olist_products_dataset.csv`            | `olist_products`                    | Product catalog with dimensions               |
| `olist_sellers_dataset.csv`             | `olist_sellers`                     | Seller profiles and locations                 |
| `olist_geolocation_dataset.csv`         | `olist_geolocation`                 | Zip code coordinates                          |
| `product_category_name_translation.csv` | `product_category_name_translation` | Portuguese → English category names           |

---

## dbt Models

All models and columns are fully documented in YAML schema files (`_sources.yml`, `_stg_olist__models.yml`, `_core__models.yml`). Documentation is viewable via `dbt docs serve`.

### Staging Layer

Materialized as **views** in the `olist_staging` schema. These models rename columns, cast data types, and apply light cleaning.

| Model                             | Source Table                        | Key Transformations                                         |
| --------------------------------- | ----------------------------------- | ----------------------------------------------------------- |
| `stg_olist__customers`            | `olist_customers`                   | Rename `customer_zip_code_prefix` → `zip_code_prefix`       |
| `stg_olist__orders`               | `olist_orders`                      | Cast all timestamp strings to `timestamp` type              |
| `stg_olist__order_items`          | `olist_order_items`                 | Round `price` and `freight_value` to 2 decimal places       |
| `stg_olist__payments`             | `olist_order_payments`              | Clean column naming                                         |
| `stg_olist__reviews`              | `olist_order_reviews`               | **Deduplicate** reviews using `row_number()` by `review_id` |
| `stg_olist__products`             | `olist_products`                    | Rename misspelled columns (`lenght` → `length`)             |
| `stg_olist__sellers`              | `olist_sellers`                     | Rename `seller_zip_code_prefix` → `zip_code_prefix`         |
| `stg_olist__geolocation`          | `olist_geolocation`                 | Rename geo-prefixed columns                                 |
| `stg_olist__category_translation` | `product_category_name_translation` | Clean column naming                                         |

### Marts Layer

Materialized as **tables** in the `olist_analytics` schema. Follows a **star schema** design.

#### Dimension Tables

| Model           | Description                                                                                                             |
| --------------- | ----------------------------------------------------------------------------------------------------------------------- |
| `dim_customers` | Customer dimension with location attributes (city, state, zip code)                                                     |
| `dim_products`  | Product dimension with English category translations via join to `stg_olist__category_translation`                      |
| `dim_sellers`   | Seller dimension with location attributes                                                                               |
| `dim_date`      | Date dimension derived from order timestamps with calendar attributes (year, month, quarter, day of week, weekend flag) |

#### Fact Table

| Model        | Grain                  | Description                                                                                                                                                                                                                                                                                                                                                              |
| ------------ | ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `fact_sales` | One row per order item | Joins `stg_olist__order_items` with `stg_olist__orders`; includes surrogate key (`order_id + '-' + order_item_id`), foreign keys to all dimensions (customers, products, sellers, dates), date FKs (`purchased_date`, `delivered_date`, `estimated_delivery_date`) for `dim_date` joins, order timestamps, status, `price`, `freight_value`, and computed `total_amount` |

**Star Schema Diagram:**

The mart layer follows a star schema with `fact_sales` at the center, linked to four dimension tables:

- **`fact_sales`** — Keyed by `sales_key` (one row per order item). Contains foreign keys to all dimensions, order context (`order_item_id`, `order_status`, `purchased_at`, `delivered_to_customer_at`), and measures (`price`, `freight_value`, `total_amount`).
- **`dim_customers`** — Customer location attributes: `customer_city`, `customer_state`.
- **`dim_products`** — Product catalog with `category_name`, English translation, and physical measurements (`weight_g`, `length_cm`, `height_cm`, `width_cm`).
- **`dim_sellers`** — Seller location attributes: `seller_city`, `seller_state`.
- **`dim_date`** — Calendar dimension derived from order timestamps, with `year`, `month`, `quarter`, `day_of_week`, and `is_weekend`.

<img width="1158" height="1162" alt="diagrams - Page 4" src="https://github.com/user-attachments/assets/a6476e5b-5207-45cd-8659-7237c0d8c015" />

### dbt Macros

| Macro                  | Purpose                                                                                                                                                                                      |
| ---------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `generate_schema_name` | Overrides dbt's default schema naming. Returns the custom schema name directly (e.g., `olist_staging`) instead of prepending the target schema (which would produce `public_olist_staging`). |

---

## Data Tests

### Schema Tests (defined in YAML)

| Test Type                       | Applied To                                                                           | Purpose                                     |
| ------------------------------- | ------------------------------------------------------------------------------------ | ------------------------------------------- |
| `unique`                        | Primary keys across all models                                                       | Ensure no duplicate records                 |
| `not_null`                      | Primary/foreign keys, required fields                                                | Ensure completeness                         |
| `accepted_values`               | `order_status`, `payment_type`, `review_score`, `quarter`                            | Validate categorical values                 |
| `relationships`                 | `fact_sales` → `dim_customers`, `dim_products`, `dim_sellers`, `dim_date`            | Ensure referential integrity in star schema |
| `expression_is_true`            | `price >= 0`, `freight_value >= 0`, `total_amount >= 0`, dimensions `> 0`            | Validate numeric ranges                     |
| `unique_combination_of_columns` | `order_items` (order_id + order_item_id), `payments` (order_id + payment_sequential) | Validate composite keys                     |

### Custom Singular Tests

| Test                                            | Description                                                                                                                                                                             |
| ----------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `assert_approved_after_purchased`               | Validates that `approved_at >= purchased_at` for all orders — enforces logical timestamp ordering                                                                                       |
| `assert_total_amount_equals_price_plus_freight` | Validates that `total_amount = price + freight_value` in `fact_sales` — enforces calculation correctness                                                                                |
| `assert_fact_sales_dates_in_dim_date`           | Validates that all date FKs in `fact_sales` (`purchased_date`, `delivered_date`, `estimated_delivery_date`) exist in `dim_date` — enforces referential integrity for the date dimension |

All singular tests are documented in `dbt/tests/schema.yml` with descriptions and severity metadata.

---

## Airflow DAG

A single DAG (`olist_ecommerce_pipeline_bash`) orchestrates the entire pipeline using `BashOperator` for all tasks. This approach was chosen for:

- **Consistency** — All three tasks use the same operator type
- **Process isolation** — Each task runs in a subprocess; a crash won't take down the Airflow worker
- **Simplicity** — No `sys.path` hacks needed to import the ingestion script

| Setting             | Value    | Reason                                                           |
| ------------------- | -------- | ---------------------------------------------------------------- |
| `schedule_interval` | `@daily` | Runs the full pipeline once per day at midnight UTC              |
| `catchup`           | `False`  | Prevents backfilling all runs since `start_date` on first enable |
| `retries`           | `1`      | Retries each task once before marking it as failed               |
| `retry_delay`       | `5 min`  | Wait 5 minutes between retries                                   |

### Task Sequence

```
ingest_raw_data  ──►  dbt_run  ──►  dbt_test
```

| Task              | What It Does                                                                                       |
| ----------------- | -------------------------------------------------------------------------------------------------- |
| `ingest_raw_data` | Runs `python scripts/ingest_olist.py` — loads 9 CSVs into `olist_raw` schema (truncate-and-reload) |
| `dbt_run`         | Runs `dbt run --target prod` — builds 9 staging views + 5 mart tables                              |
| `dbt_test`        | Runs `dbt test --target prod` — executes 71 schema tests + 3 custom singular tests (74 total)      |

Both dbt tasks use `DBT_LOG_PATH=/tmp` and `--target-path /tmp/dbt_target` to avoid write permission errors on the Docker-mounted volume.

---

## Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)
- Git

### Setup

1. **Clone the repository:**

   ```bash
   git clone https://github.com/<your-username>/olist-ecommerce-data-pipeline.git
   cd olist-ecommerce-data-pipeline
   ```

2. **Create your local config files:**

   ```bash
   cp .env.example .env
   cp docker-compose.example.yml docker-compose.yml
   cp dbt/profiles.yml.example dbt/profiles.yml
   ```

   The `.example` files are the safe templates kept in Git. The copied files (`.env`, `docker-compose.yml`, and `dbt/profiles.yml`) are your local working configs and should not be committed.

3. **Start all services:**

   ```bash
   docker compose up -d --build
   ```

   This starts:
   - **PostgreSQL** on port `5433` (mapped from container port `5432`)
   - **Airflow Webserver** on port `8080` (auto-initializes DB and creates an admin user)
   - **Airflow Scheduler**
   - **python-app** container (starter Python image from project template, restarts on failure)
   - **dbt** container (idle, for manual dbt commands)

4. **Access the Airflow UI:**

   Open [http://localhost:8080](http://localhost:8080) and log in:
   - Username: value from `AIRFLOW_ADMIN_USERNAME` in `.env`
   - Password: value from `AIRFLOW_ADMIN_PASSWORD` in `.env`

### Running the Pipeline

**Option A — Via Airflow UI (recommended):**

1. Navigate to the DAGs page.
2. Enable and trigger `olist_ecommerce_pipeline_bash`.
3. Monitor task progress in the Graph or Grid view.

**Option B — Manual dbt commands:**

```bash
# Enter the dbt container
docker exec -it dbt-lab-olist bash

# Run models
dbt run --profiles-dir . --target dev

# Run tests
dbt test --profiles-dir . --target dev

# Generate and serve docs
dbt docs generate --profiles-dir . --target dev
dbt docs serve --port 8081
```

**Option C — Run ingestion standalone:**

```bash
# From the host machine (connects via localhost:5433)
cd scripts
python ingest_olist.py
```

---

## Challenges & Solutions

### 1. dbt `Permission denied` on log file

**Problem:** The `dbt_run` Airflow task failed with `PermissionError: [Errno 13] Permission denied: '/opt/airflow/dbt/logs/dbt.log'`. The `dbt/logs` directory was owned by the host user, not the container's `airflow` user.

**Fix:** Added `DBT_LOG_PATH=/tmp` to the `dbt_run` bash command (it was already present on `dbt_test` but had been missed on `dbt_run`). Also set `--target-path /tmp/dbt_target` for compiled artifacts.

### 2. dbt partial parse corruption

**Problem:** After editing YAML schema files, `dbt docs generate` failed with _"dbt was unable to infer all dependencies for the model unique_stg_olist\_\_sellers_seller_id"_, even though the YAML was valid.

**Fix:** Ran `dbt clean` to clear the corrupted `partial_parse.msgpack` cache, then re-ran the command successfully.

### 3. DockerOperator DAG didn't work

**Problem:** The DAG variant using `DockerOperator` for ingestion required Docker-in-Docker socket mounting, network configuration, and image management, and ultimately failed to run reliably.

**Fix:** Dropped the `DockerOperator` DAG entirely and consolidated on a single `BashOperator` DAG. Also removed the unused `PythonOperator` DAG for the same simplicity reasons.

### 4. `if_exists='replace'` dropping tables

**Problem:** Re-running the ingestion script destroyed table structures because pandas' `to_sql(if_exists='replace')` runs `DROP TABLE` + `CREATE TABLE`, breaking any downstream references.

**Fix:** Changed to a check-then-truncate strategy: verify table existence first, then `TRUNCATE` + `APPEND` on reruns or `CREATE` on first load.

### 5. Duplicate reviews in source data

**Problem:** `review_id` was not unique in the raw `olist_order_reviews_dataset.csv`, causing `unique` test failures downstream.

**Fix:** Added `row_number()` deduplication in `stg_olist__reviews`, partitioned by `review_id` and ordered by `review_creation_date desc`, keeping only the latest review per ID.

### 6. dbt default schema naming

**Problem:** dbt prefixed custom schemas with the target schema (e.g., `public_olist_staging` instead of `olist_staging`).

**Fix:** Created a custom `generate_schema_name` macro that returns the custom schema name directly without prepending the target schema.

### 7. Hardcoded DB connection

**Problem:** The ingestion script only worked in one environment because the host and port were hardcoded.

**Fix:** Made `DB_HOST` and `DB_PORT` configurable via environment variables with sensible defaults (`localhost:5433` for local development, `postgres:5432` inside Docker).

---

## Key Design Decisions

### Why BashOperator over PythonOperator for Airflow tasks?

Three DAG variants were developed during this project — one using `PythonOperator`, one using `BashOperator`, and one using `DockerOperator`. The BashOperator version was chosen as the final implementation for several reasons:

- **Process isolation** — Each task runs in its own subprocess. If the ingestion script crashes (e.g., out-of-memory), it won't bring down the Airflow worker process. With `PythonOperator`, the callable executes in the same process as the worker.
- **No import hacks** — The `PythonOperator` version required `sys.path.insert(0, '/opt/airflow/scripts')` to import `ingest_olist.py`, since it isn't installed as a Python package. `BashOperator` simply calls `python scripts/ingest_olist.py` — clean and direct.
- **Consistency** — The dbt tasks must use `BashOperator` (dbt is a CLI tool). Using `BashOperator` for ingestion too keeps the DAG uniform and easier to reason about.
- **The `DockerOperator` variant was removed** because it introduced additional complexity (Docker-in-Docker socket mounting, image management, network configuration) without meaningful benefit for a single-host deployment.

### Why truncate-and-reload instead of `if_exists='replace'`?

Pandas' `to_sql(if_exists='replace')` runs `DROP TABLE` followed by `CREATE TABLE` on every execution. This causes problems:

- Any downstream views or foreign keys referencing the table break when it's dropped.
- Table-level grants or comments are lost.
- There's a brief window where the table doesn't exist at all, which can cause failures in concurrent queries.

The truncate-and-reload approach (`TRUNCATE` + `to_sql(if_exists='append')`) preserves the table structure while replacing all data, making the pipeline safely idempotent.

### Why a star schema for the mart layer?

The Olist dataset is transactional e-commerce data — orders, items, payments, reviews. A star schema was chosen because:

- **Query performance** — Fact-dimension joins are simple and predictable. BI tools (Power BI, Looker, Metabase) optimize well for this pattern.
- **Business alignment** — The grain of `fact_sales` (one row per order item) maps naturally to the core business question: "What was sold, by whom, to whom, and when?"
- **Extensibility** — New dimensions (e.g., `dim_geography` from the geolocation table) or new facts (e.g., `fact_payments`) can be added without restructuring existing models.
- **Industry standard** — Star schemas are the most widely understood dimensional modeling pattern, making the project accessible to other data engineers and analysts.

### Why staging views instead of tables?

Staging models are materialized as **views** (`+materialized: view`) rather than tables because:

- **No storage overhead** — Views don't duplicate the raw data, keeping the database lean.
- **Always fresh** — Views reflect the latest raw data without needing to be rebuilt.
- **Appropriate for the use case** — Staging models are intermediate transformations consumed only by downstream mart models, not queried directly by analysts. The performance cost of a view is negligible since the mart layer materializes the final aggregated results as tables.

### Why a custom `generate_schema_name` macro?

By default, dbt constructs schema names by prepending the target schema to any custom schema — for example, if the target is `public` and the model specifies `+schema: olist_staging`, dbt creates `public_olist_staging`. This is designed for multi-developer environments where each developer gets their own namespace.

For this project, a single database serves all layers, so the override macro returns the custom schema name directly (`olist_staging`, `olist_analytics`) without any prefix. This produces clean, readable schema names that match the architecture diagram.

### Why `dim_date` is derived from order data instead of a static date spine?

Many star schemas use a pre-generated date spine (e.g., every day from 2000 to 2030). This project derives `dim_date` from actual order timestamps instead because:

- **Compact** — Only dates that appear in the data end up in the dimension, avoiding thousands of unused rows.
- **No external dependencies** — No need for a dbt package like `dbt_utils.date_spine` or a seed file.
- **Sufficient for analytics** — The Olist dataset covers a fixed historical period (2016–2018). A full date spine would add no analytical value.

The trade-off is that if a BI report filters on a date with no orders, that date won't exist in `dim_date`. For a historical dataset this is acceptable; for a production system with real-time data, a pre-generated spine would be preferable.

### Why separate schemas (`olist_raw`, `olist_staging`, `olist_analytics`)?

Using distinct schemas for each layer provides:

- **Access control** — In a production setting, analysts can be granted `SELECT` on `olist_analytics` only, without exposing raw or intermediate data.
- **Clarity** — Anyone inspecting the database immediately understands which tables are raw, which are intermediate, and which are analyst-ready.
- **dbt convention** — Separating staging and marts into different schemas is a widely adopted dbt best practice, making the project structure familiar to other dbt users.
