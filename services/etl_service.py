from datetime import datetime

from sqlalchemy import desc, func

from models import Platform, Trend
from services.analysis_service import AnalysisService
from services.ingestion_service import IngestionService


class ETLService:
    def __init__(self):
        self.ingestion_service = IngestionService()
        self.analysis_service = AnalysisService()

    @staticmethod
    def _bucket_from_dt(dt):
        return dt.strftime("%Y%m%d%H")

    def _get_or_create_platform(self, db, platform_name):
        normalized = platform_name.lower()
        platform = db.query(Platform).filter(func.lower(Platform.name) == normalized).first()
        if platform:
            if platform.name != normalized:
                platform.name = normalized
            return platform
        platform = Platform(name=normalized)
        db.add(platform)
        db.flush()
        return platform

    def run_collection_cycle(self, db, per_provider_limit=20):
        raw_records, used_fallback, provider_errors, provider_stats = self.ingestion_service.collect_live_trends(
            per_provider_limit=per_provider_limit
        )
        now = datetime.utcnow()
        inserted = 0
        updated = 0
        processed_ids = []

        for record in raw_records:
            collected_at = record.get("collected_at") or now
            dedup_bucket = self._bucket_from_dt(collected_at)
            platform = self._get_or_create_platform(db, record["platform"])

            sentiment_label, sentiment_score = self.analysis_service.score_sentiment(record["text"])
            topic_label, _topic_conf = self.analysis_service.detect_topic(
                record["text"], record.get("hashtags")
            )
            recency_hours = max((now - collected_at).total_seconds() / 3600.0, 0.0)
            trend_score = self.analysis_service.compute_trend_score(
                record.get("engagement_count", 0), sentiment_score, recency_hours
            )

            existing = (
                db.query(Trend)
                .filter_by(
                    platform_id=platform.id,
                    text=record["text"],
                    dedup_bucket=dedup_bucket,
                )
                .first()
            )

            if existing:
                existing.view_count = max(existing.view_count or 0, record.get("engagement_count", 0))
                existing.hashtags = record.get("hashtags", existing.hashtags)
                existing.sentiment_label = sentiment_label
                existing.sentiment_score = sentiment_score
                existing.topic_label = topic_label
                existing.trend_score = trend_score
                existing.last_seen_at = now
                updated += 1
                processed_ids.append(existing.id)
                continue

            trend = Trend(
                text=record["text"],
                hashtags=record.get("hashtags", []),
                view_count=record.get("engagement_count", 0),
                source_url=record.get("source_url"),
                language=record.get("language", "en"),
                platform_id=platform.id,
                dedup_bucket=dedup_bucket,
                sentiment_label=sentiment_label,
                sentiment_score=sentiment_score,
                topic_label=topic_label,
                trend_score=trend_score,
                last_seen_at=now,
                collected_at=collected_at,
            )
            db.add(trend)
            db.flush()
            inserted += 1
            processed_ids.append(trend.id)

        db.commit()
        return {
            "inserted": inserted,
            "updated": updated,
            "processed_count": len(raw_records),
            "used_fallback": used_fallback,
            "provider_errors": provider_errors,
            "provider_stats": provider_stats,
            "trend_ids": processed_ids,
            "collected_at": now.isoformat(),
        }

    def get_live_trends(self, db, limit=50):
        return (
            db.query(Trend)
            .order_by(desc(Trend.collected_at), desc(Trend.trend_score))
            .limit(limit)
            .all()
        )

    def get_top_trends(self, db, limit=20):
        return (
            db.query(Trend)
            .order_by(desc(Trend.trend_score), desc(Trend.view_count), desc(Trend.collected_at))
            .limit(limit)
            .all()
        )
