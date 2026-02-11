# Real-time FX OHLC Project

This project implements a backend service for real-time FX market data ingestion and OHLC (Open, High, Low, Close) aggregation using Python (FastAPI) and PostgreSQL with TimescaleDB.

## Architecture & SQL Strategy

### Database Schema (TimescaleDB)
The core of the solution relies on TimescaleDB's **Hypertables** and **Continuous Aggregates**.

1.  **Ingestion Table (`ticks`)**:
    -   A hypertable partitioned by time.
    -   Stores raw 1-second updates (`time`, `symbol`, `price`).
    -   High write throughput optimized.

2.  **Real-time Aggregations (Continuous Aggregates)**:
    -   We define materialized views for standard timeframes: `ohlc_1m`, `ohlc_1h`, `ohlc_1d`.
    -   These views are incrementally updated by TimescaleDB in the background, making queries for OHLC data extremely fast (O(1) relative to raw data size).
    -   Query: `SELECT ... FROM ohlc_1m WHERE ...`

3.  **Custom Daily View (10 PM - 10 PM)**:
    -   Implemented as a custom view `ohlc_1d_custom_10pm`.
    -   Uses `time_bucket('1 day', time, '22:00'::timestamp)` to offset the aggregation window.
    -   This allows querying daily candles that respect the NY Close (5 PM EST) or any other custom session close (e.g., 10 PM).

### Backend (FastAPI)
-   `POST /ticks`: Endpoint to receive real-time tick data.
-   `GET /ohlc/{timeframe}`: Generic endpoint to retrieve aggregated data. Supports `1m`, `1h`, `1d`, and `1d_custom`.

## Setup Instructions

### Prerequisites
-   Python 3.9+
-   PostgreSQL with TimescaleDB extension enabled.

### Installation
1.  Create virtual environment and install dependencies:
    ```bash
    python -m venv venv
    .\venv\Scripts\pip install -r requirements.txt
    ```
2.  Setup Database:
    -   Ensure PostgreSQL is running.
    -   Execute `sql/schema.sql` to create tables and views.
    ```bash
    psql -U postgres -d fxdata -f sql/schema.sql
    ```
    *(Note: Update `app/database.py` if your DB credentials differ).*

### Running the App
```bash
python -m uvicorn app.main:app --reload
```

## GitHub Submission
1.  Initialize Git:
    ```bash
    git init
    git add .
    git commit -m "Initial commit: Real-time OHLC implementation"
    ```
2.  Push to GitHub:
    ```bash
    git remote add origin https://github.com/sky2110/your-repo-name.git
    git push -u origin master
    ```

## Assumptions & Trade-offs
-   **Assumption**: Ticks arrive roughly in order. TimescaleDB handles out-of-order data well within a configured window.
-   **Trade-off**: Used `FLOAT` for price for simplicity; in production, `DECIMAL` or integer (micros) is better for precision.
-   **Limitation**: The custom 10 PM daily view is a standard view on top of raw/1m data. For extreme scale, a specific Continuous Aggregate with logic for the offset would be more performant.
