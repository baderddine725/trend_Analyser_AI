# Run Setup

## 1) Fill `.env`

Edit `.env` and provide values:

- `DATABASE_URL` (required)
- `ETL_INTERVAL_SECONDS` (optional, default `900`)
- `UVICORN_HOST` (optional, default `0.0.0.0`)
- `UVICORN_PORT` (optional, default `5001`)
- `LOG_LEVEL` (optional, default `debug`)

Example local Postgres URL:

`postgresql://postgres:postgres@localhost:5432/postgres`

## 2) Install dependencies

Use your package manager (`uv` recommended):

`uv sync`

## 3) Apply DB migrations

`python migrations/apply_migrations.py`

## 4) Run API

`python main.py`

Or use one command on Windows PowerShell:

`powershell -ExecutionPolicy Bypass -File scripts/run.ps1`

Optional (skip migrations):

`powershell -ExecutionPolicy Bypass -File scripts/run.ps1 -SkipMigrations`

## 5) Verify

- `GET /health`
- `GET /api/v1/ops/health`
- `GET /api/v1/ops/etl-status`
