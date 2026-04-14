import logging

from ingestion.providers import GoogleTrendsProvider, TikTokProvider, XProvider
from utils.mock_data import get_mock_trends

logger = logging.getLogger(__name__)


class IngestionService:
    def __init__(self):
        self.providers = [TikTokProvider(), XProvider(), GoogleTrendsProvider()]

    def providers_healthcheck(self):
        statuses = []
        for provider in self.providers:
            if hasattr(provider, "healthcheck"):
                statuses.append(provider.healthcheck())
            else:
                statuses.append({"provider": provider.platform, "available": None})
        return statuses

    def collect_live_trends(self, per_provider_limit=20):
        records = []
        provider_errors = {}
        provider_stats = {}

        for provider in self.providers:
            try:
                provider_records = provider.fetch_trends(limit=per_provider_limit)
                provider_stats[provider.platform] = len(provider_records)
                records.extend(provider_records)
            except Exception as exc:  # pragma: no cover - defensive fallback path
                provider_errors[provider.platform] = str(exc)
                provider_stats[provider.platform] = 0
                logger.warning("Provider %s failed: %s", provider.platform, exc)

        if records:
            return records, False, provider_errors, provider_stats

        # Hard fallback to internal mock data for uptime.
        tiktok_trends, x_trends = get_mock_trends()
        fallback_records = []
        for t in tiktok_trends:
            fallback_records.append(
                {
                    "platform": "tiktok",
                    "text": t["text"],
                    "hashtags": t.get("hashtags", []),
                    "engagement_count": t.get("views", 0),
                    "source_url": None,
                    "language": "en",
                }
            )
        for t in x_trends:
            fallback_records.append(
                {
                    "platform": "x",
                    "text": t["text"],
                    "hashtags": t.get("hashtags", []),
                    "engagement_count": t.get("tweet_count", 0),
                    "source_url": None,
                    "language": "en",
                }
            )
        provider_stats["fallback_mock"] = len(fallback_records)
        return fallback_records, True, provider_errors, provider_stats
