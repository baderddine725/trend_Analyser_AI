-- 001_trend_enhancements.sql
-- Adds Use Case 1 analytics fields and deduplication support to trend table.

BEGIN;

ALTER TABLE trend ADD COLUMN IF NOT EXISTS source_url VARCHAR(500);
ALTER TABLE trend ADD COLUMN IF NOT EXISTS language VARCHAR(20) DEFAULT 'en';
ALTER TABLE trend ADD COLUMN IF NOT EXISTS dedup_bucket VARCHAR(20);
ALTER TABLE trend ADD COLUMN IF NOT EXISTS sentiment_label VARCHAR(20) DEFAULT 'neutral';
ALTER TABLE trend ADD COLUMN IF NOT EXISTS sentiment_score DOUBLE PRECISION DEFAULT 0.0;
ALTER TABLE trend ADD COLUMN IF NOT EXISTS topic_label VARCHAR(100) DEFAULT 'general';
ALTER TABLE trend ADD COLUMN IF NOT EXISTS trend_score DOUBLE PRECISION DEFAULT 0.0;
ALTER TABLE trend ADD COLUMN IF NOT EXISTS last_seen_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW();
ALTER TABLE trend ADD COLUMN IF NOT EXISTS collected_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW();

UPDATE trend
SET dedup_bucket = TO_CHAR(COALESCE(created_at, NOW()), 'YYYYMMDDHH')
WHERE dedup_bucket IS NULL;

ALTER TABLE trend ALTER COLUMN dedup_bucket SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'uq_trend_platform_text_bucket'
    ) THEN
        ALTER TABLE trend
        ADD CONSTRAINT uq_trend_platform_text_bucket
        UNIQUE (platform_id, text, dedup_bucket);
    END IF;
END $$;

COMMIT;
