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
- [Airflow DAGs](#airflow-dags)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Setup](#setup)
  - [Running the Pipeline](#running-the-pipeline)
- [Challenges & Solutions](#challenges--solutions)

---

## Overview

This project builds a complete data pipeline for the [Olist Brazilian E-Commerce dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce). It demonstrates a modern data stack approach:

1. **Ingest** — A Python script loads 9 CSV files into a PostgreSQL `olist_raw` schema.
2. **Transform** — dbt models clean, rename, and restructure the raw data into staging views and analytical mart tables following a star schema.
3. **Test** — dbt runs schema tests (unique, not_null, accepted_values, relationships) and custom data quality assertions.
4. **Orchestrate** — Apache Airflow coordinates the three steps in sequence via a DAG.

---

## Architecture

<img width="1236" height="431" alt="Week 5 Mini Pipeline Architecture Diagram-Copy of Page-1 drawio (1)" src="https://github.com/user-attachments/assets/f56b066d-ef6d-4ac4-a35a-01169f54f83f" />

The entire pipeline runs inside **Docker**. Key components:

- **Ingestion Layer** — `ingest_olist.py` reads 9 Kaggle Olist CSV files and loads them into a PostgreSQL **Raw Schema** (`olist_raw`).
- **Orchestration Layer (Airflow)** — Apache Airflow orchestrates the end-to-end workflow: ingestion → dbt run → dbt test, running on a daily schedule.
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
├── docker-compose.yml              # Multi-service Docker setup
├── airflow/
│   ├── Dockerfile                  # Airflow image with dbt + Docker provider
│   ├── requirements.txt            # Python deps for Airflow workers
│   ├── dags/
│   │   ├── olist_pipeline_dag.py          # DAG using PythonOperator
│   │   ├── olist_pipeline_dag_bash.py     # DAG using BashOperator
│   │   └── olist_pipeline_dag_docker.py   # DAG using DockerOperator
│   ├── datasets/                   # 9 Olist CSV source files
│   └── logs/                       # Airflow task logs
├── dbt/
│   ├── dbt_project.yml             # dbt project config
│   ├── profiles.yml                # Connection profiles (dev / prod)
│   ├── packages.yml                # dbt_utils dependency
│   ├── macros/
│   │   └── get_custom_schema.sql   # Custom schema naming macro
│   ├── models/
│   │   ├── staging/olist/          # 9 staging views + source/model YAML
│   │   ├── intermediate/          # (reserved for future use)
│   │   └── marts/core/            # Dimension & fact tables + model YAML
│   └── tests/                      # Custom singular data tests
├── scripts/
│   ├── Dockerfile                  # Standalone Python app image
│   └── ingest_olist.py             # CSV → PostgreSQL ingestion script
└── postgres/
    └── init.sql                    # DB bootstrap script
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

**Step 1 — Ingest:** `ingest_olist.py` reads each CSV, checks if the target table already exists, truncates it if so (preserving schema), or creates it fresh. Connection details are configurable via `DB_HOST` and `DB_PORT` environment variables.

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

---

## Data Tests

### Schema Tests (defined in YAML)

| Test Type                       | Applied To                                                                           | Purpose                                     |
| ------------------------------- | ------------------------------------------------------------------------------------ | ------------------------------------------- |
| `unique`                        | Primary keys across all models                                                       | Ensure no duplicate records                 |
| `not_null`                      | Primary/foreign keys, required fields                                                | Ensure completeness                         |
| `accepted_values`               | `order_status`, `payment_type`, `review_score`                                       | Validate categorical values                 |
| `relationships`                 | `fact_sales` → `dim_customers`, `dim_products`, `dim_sellers`, `dim_date`            | Ensure referential integrity in star schema |
| `expression_is_true`            | `price >= 0`, `freight_value >= 0`, dimensions `> 0`                                 | Validate numeric ranges                     |
| `unique_combination_of_columns` | `order_items` (order_id + order_item_id), `payments` (order_id + payment_sequential) | Validate composite keys                     |

### Custom Singular Tests

| Test                                            | Description                                                                                                                                        |
| ----------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| `assert_approved_after_purchased`               | Validates that `approved_at >= purchased_at` for all orders — enforces logical timestamp ordering                                                  |
| `assert_total_amount_equals_price_plus_freight` | Validates that `total_amount = price + freight_value` in `fact_sales` — enforces calculation correctness                                           |
| `assert_fact_sales_dates_in_dim_date`           | Validates that all dates derived from order timestamps in `fact_sales` exist in `dim_date` — enforces referential integrity for the date dimension |

---

## Airflow DAGs

Three DAG variants are provided, each using a different operator strategy for the ingestion task:

| DAG ID                            | Ingestion Operator | Use Case                                            |
| --------------------------------- | ------------------ | --------------------------------------------------- |
| `olist_ecommerce_pipeline`        | `PythonOperator`   | Runs `ingest_olist.py` in-process via Python import |
| `olist_ecommerce_pipeline_bash`   | `BashOperator`     | Runs ingestion script as a shell command            |
| `olist_ecommerce_pipeline_docker` | `DockerOperator`   | Runs ingestion in an isolated Docker container      |

All three DAGs share the same 3-step task sequence:

```
ingest_raw_data  ──►  dbt_run  ──►  dbt_test
```

- **`ingest_raw_data`** — Loads 9 CSV files into `olist_raw` schema
- **`dbt_run`** — Builds staging views and mart tables (`dbt run --target prod`)
- **`dbt_test`** — Runs all schema and singular tests (`dbt test --target prod`)

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

2. **Start all services:**

   ```bash
   docker compose up -d --build
   ```

   This starts:
   - **PostgreSQL** on port `5433` (mapped from container port `5432`)
   - **Airflow Webserver** on port `8080` (auto-initializes DB and creates an admin user)
   - **Airflow Scheduler**
   - **python-app** container (standalone ingestion image, restarts on failure)
   - **dbt** container (idle, for manual dbt commands)

3. **Access the Airflow UI:**

   Open [http://localhost:8080](http://localhost:8080) and log in:
   - Username: `admin`
   - Password: `admin`

### Running the Pipeline

**Option A — Via Airflow UI:**

1. Navigate to the DAGs page.
2. Enable and trigger one of the DAGs (e.g., `olist_ecommerce_pipeline`).
3. Monitor task progress in the Graph or Grid view.

**Option B — Manual dbt commands:**

```bash
# Enter the dbt container
docker exec -it dbt-lab-olist bash

# Run models
dbt run --profiles-dir . --target dev

# Run tests
dbt test --profiles-dir . --target dev

# Generate docs
dbt docs generate --profiles-dir . --target dev
```

**Option C — Run ingestion standalone:**

```bash
# From the host machine (connects via localhost:5433)
cd scripts
python ingest_olist.py
```

---

## Challenges & Solutions

| Challenge                                                                                                                      | Solution                                                                                                                                           |
| ------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Hardcoded DB connection** — Ingestion script only worked in one environment                                                  | Made `DB_HOST` and `DB_PORT` configurable via environment variables with sensible defaults (`localhost:5433` for local, `postgres:5432` in Docker) |
| **`if_exists='replace'` dropping tables** — Re-running ingestion destroyed table structures and broke downstream references    | Changed to a check-then-truncate strategy: verify table existence first, then `TRUNCATE` + `APPEND` on reruns or `CREATE` on first load            |
| **Duplicate reviews in source data** — `review_id` was not unique in the raw CSV                                               | Added `row_number()` deduplication in `stg_olist__reviews`, keeping only the latest review per `review_id`                                         |
| **dbt default schema naming** — dbt prefixed custom schemas with the target schema (e.g., `public_olist_staging`)              | Created a custom `generate_schema_name` macro that uses the custom schema name directly without prepending                                         |
| **Airflow write permissions to dbt target** — Airflow worker couldn't write compiled dbt artifacts to the mounted volume       | Set `--target-path /tmp/dbt_target` and `DBT_LOG_PATH=/tmp` to write to writable paths inside the container                                        |
| **Docker socket access for DockerOperator** — Airflow needed to launch sibling containers                                      | Mounted `/var/run/docker.sock` into the Airflow containers and added the `airflow` user to a `docker` group in the Dockerfile                      |
| **Source path mismatch** — Ingestion script used a hardcoded relative path instead of the parameterized `source_path` argument | Removed the hardcoded `source_path = "./airflow/datasets"` inside the function and properly used the function parameter                            |
