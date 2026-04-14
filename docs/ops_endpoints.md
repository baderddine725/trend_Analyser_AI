# Ops Monitoring Endpoints

## `GET /health`
- Minimal readiness check.
- Verifies API process is alive and database answers `SELECT 1`.

## `GET /api/v1/ops/health`
- Extended service health.
- Returns:
  - database status
  - provider health checks (`tiktok`, `x`, `google_trends`)
  - ETL worker status (thread/alive, interval, failure counters)
- `status` is `ok` or `degraded`.

## `GET /api/v1/ops/etl-status`
- Runtime ETL telemetry for operations:
  - worker thread status
  - total/success/failed run counts
  - last run timing and duration
  - last ETL result payload (inserted/updated/provider stats)
  - last error (if any)

## `POST /api/v1/etl/run`
- Manual ETL trigger.
- Also updates ops status counters and last result metadata.
