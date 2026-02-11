-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- 1. Real-time OHLC Aggregations
-- Create a hypertable for raw ticks
CREATE TABLE IF NOT EXISTS ticks (
    time TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    price DOUBLE PRECISION NOT NULL
);

-- Convert to hypertable partitioned by time
SELECT create_hypertable('ticks', 'time', if_not_exists => TRUE);

-- create index on symbol for faster querying
CREATE INDEX IF NOT EXISTS ix_symbol_time ON ticks (symbol, time DESC);

-- Continuous Aggregates for 1-minute OHLC
CREATE MATERIALIZED VIEW IF NOT EXISTS ohlc_1m
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 minute', time) AS bucket,
    symbol,
    first(price, time) as open,
    max(price) as high,
    min(price) as low,
    last(price, time) as close
FROM ticks
GROUP BY bucket, symbol;

-- Continuous Aggregates for 1-hour OHLC
CREATE MATERIALIZED VIEW IF NOT EXISTS ohlc_1h
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', time) AS bucket,
    symbol,
    first(price, time) as open,
    max(price) as high,
    min(price) as low,
    last(price, time) as close
FROM ticks
GROUP BY bucket, symbol;

-- Continuous Aggregates for 1-day OHLC (Standard 00:00-00:00)
CREATE MATERIALIZED VIEW IF NOT EXISTS ohlc_1d
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', time) AS bucket,
    symbol,
    first(price, time) as open,
    max(price) as high,
    min(price) as low,
    last(price, time) as close
FROM ticks
GROUP BY bucket, symbol;

-- 2. Custom Daily View (10 PM to 10 PM)
-- Using time_bucket with origin parameter
-- Note: Continuous aggregates with origin require TimescaleDB 2.0+
-- We will create a view for this specific requirement if CAGG doesn't support origin easily in all versions,
-- but time_bucket supports origin in standard queries.
-- For a CAGG with origin, we can specify it in the view definition if supported, or just use a standard view over the ticks (slower) or 1m agg (faster).
-- A standard view over the 1h aggregate would be efficient enough.

CREATE OR REPLACE VIEW ohlc_1d_custom_10pm AS
SELECT
    time_bucket('1 day', bucket, '22:00'::timestamp) AS custom_bucket,
    symbol,
    first(open, bucket) as open,
    max(high) as high,
    min(low) as low,
    last(close, bucket) as close
FROM ohlc_1m -- Aggregating from 1m blocks is valid and reasonably fast
GROUP BY custom_bucket, symbol;