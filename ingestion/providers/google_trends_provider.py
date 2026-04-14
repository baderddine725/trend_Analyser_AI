from datetime import datetime


class GoogleTrendsProvider:
    platform = "google_trends"

    def healthcheck(self):
        try:
            from pytrends.request import TrendReq

            pytrends = TrendReq(hl="en-US", tz=360)
            result = pytrends.trending_searches(pn="united_states")
            available = not result.empty
            return {"provider": self.platform, "available": available, "rows": int(len(result.index))}
        except Exception as exc:
            return {"provider": self.platform, "available": False, "error": str(exc)}

    def fetch_trends(self, limit=20):
        """
        Retrieves Google trending searches through pytrends.
        """
        try:
            from pytrends.request import TrendReq
        except Exception as exc:
            raise RuntimeError(f"pytrends import failed: {exc}") from exc

        pytrends = TrendReq(hl="en-US", tz=360)
        df = pytrends.trending_searches(pn="united_states")
        if df.empty:
            raise RuntimeError("No Google Trends data returned")

        now = datetime.utcnow()
        records = []
        for term in df[0].head(limit).tolist():
            text = str(term).strip()
            if not text:
                continue
            hashtags = [token.lower() for token in text.replace("/", " ").split()[:3]]
            records.append(
                {
                    "platform": self.platform,
                    "text": text[:200],
                    "hashtags": hashtags,
                    "engagement_count": 0,
                    "source_url": "https://trends.google.com/trends/",
                    "language": "en",
                    "collected_at": now,
                }
            )
        if not records:
            raise RuntimeError("No trend terms extracted from Google Trends response")
        return records
