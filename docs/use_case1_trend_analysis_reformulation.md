# TrendTitan Reformulation - Use Case 1 (Trend Analysis)

## 1) Current Project Diagnosis

The current repository is a good MVP shell, but it is not yet a production-ready trend analysis system.

- Backend is duplicated (`main.py` with FastAPI and `app.py` with Flask).
- Data ingestion is still mock-based (`utils/api_client.py`, `utils/mock_data.py`).
- Trend analysis is keyword counting only (`utils/trend_analyzer.py`).
- ETL orchestration, async jobs, and observability are not yet implemented.
- Dashboard exists and can be reused as the visualization base.

## 2) Reformulated Product Scope for Use Case 1

Use Case 1 should focus on one objective:

**Continuously ingest trends from TikTok + X + Google Trends, analyze sentiment/topics, and expose ranked trends in an API/dashboard.**

To keep it functional and low-cost:

- Keep FastAPI (remove Flask path later).
- Start with scraper-first ingestion (no paid API dependency).
- Use Hugging Face + lightweight sentiment fallback.
- Add scheduled ETL and async execution before advanced generation features.

## 3) Target Architecture (Practical + Scalable)

### Ingestion Layer

- `ingestion/providers/tiktok_scraper.py` (unofficial scraper strategy)
- `ingestion/providers/x_scraper.py` (scraping/search strategy)
- `ingestion/providers/google_trends.py` (`pytrends` as extra signal)
- Normalize output to one schema.

### Processing/ETL Layer

- `pipeline/jobs/collect_trends.py` (extract)
- `pipeline/jobs/normalize_trends.py` (transform)
- `pipeline/jobs/persist_trends.py` (load)
- Schedule with `Celery + Redis` initially.
- Add Vertex AI Pipelines later when cloud scaling is required.

### NLP/Trend Intelligence Layer

- Topic extraction: `transformers` zero-shot classification or BERTopic-style pipeline.
- Sentiment:
  - General: `cardiffnlp/twitter-roberta-base-sentiment-latest`
  - Finance/markets optional: FinBERT
- Trend scoring formula:
  - recency score
  - cross-platform frequency
  - engagement velocity
  - sentiment weight

### API Layer

- FastAPI only:
  - `GET /api/v1/trends/live`
  - `GET /api/v1/trends/top`
  - `GET /api/v1/trends/{topic}`
  - `POST /api/v1/etl/run`

### Frontend Layer

- Keep current dashboard templates for MVP.
- Add filters by platform/time window and sentiment distribution chart.
- Optional phase 2: migrate to Next.js dashboard.

## 4) Data Model (Minimal Functional Schema)

Use a single canonical `raw_trends` table plus derived analytics.

- `platform` (`tiktok`, `x`, `google_trends`)
- `trend_text`
- `hashtags` (JSON)
- `engagement_count`
- `source_url`
- `collected_at`
- `language`

Derived table `trend_signals`:

- `trend_id`
- `sentiment_label`
- `sentiment_score`
- `topic_label`
- `topic_confidence`
- `velocity_score`
- `trend_score`
- `computed_at`

## 5) Concrete Refactor Path for This Repository

### Phase A - Consolidate Core (now)

1. Keep `main.py`, deprecate `app.py`.
2. Keep `database.py` + `models.py`, deprecate `db.py` + `db_models.py`.
3. Replace `utils/api_client.py` mock logic with provider adapters + fallback.
4. Move business logic from `main.py` into service modules:
   - `services/ingestion_service.py`
   - `services/analysis_service.py`
   - `services/content_service.py`

### Phase B - Functional Trend Pipeline

1. Add Celery worker and periodic schedule.
2. Store snapshots every N minutes.
3. Add deduplication key (`platform + trend_text + bucketed_timestamp`).
4. Persist NLP outputs in `trend_signals`.

### Phase C - Scale/Cloud

1. Containerize API + worker.
2. Add Vertex AI pipeline version for managed ETL jobs.
3. Add model registry/evaluation for NLP model updates.

## 6) Recommended Free/Low-Cost Stack Mapping

- Scraping: TikTok unofficial scraper + X scraper + `pytrends`
- NLP: Hugging Face Transformers + VADER fallback
- Async ETL: Celery + Redis
- API: FastAPI
- DB: PostgreSQL (Supabase is fine)
- Dashboard: current HTML/JS (short term), Next.js (later)
- Automation: n8n for non-core operational workflows

## 7) Suggested New Repository Structure

```text
TrendTitan/
  app/
    api/
      routes/
    services/
    ingestion/
      providers/
    nlp/
    db/
    schemas/
  workers/
    celery_app.py
    tasks/
  dashboard/
    templates/
    static/
  docs/
    use_case1_trend_analysis_reformulation.md
```

## 8) Priority Backlog (Execution Order)

1. Remove backend duplication (FastAPI as single source of truth).
2. Implement real ingestion adapters with graceful fallback.
3. Add scheduled ETL and deduplication.
4. Integrate transformer sentiment/topic models.
5. Expose versioned API endpoints for trend monitoring.
6. Upgrade dashboard to display trend score + sentiment/topic.

---

This reformulation keeps your current project assets, minimizes cost, and creates a clear path from prototype to scalable trend intelligence.
