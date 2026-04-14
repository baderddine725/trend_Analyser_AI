from datetime import datetime


class XProvider:
    platform = "x"

    def healthcheck(self):
        try:
            import snscrape.modules.twitter as sntwitter

            sample = list(sntwitter.TwitterSearchScraper("trending lang:en").get_items())
            return {"provider": self.platform, "available": True, "sample_size": len(sample[:1])}
        except Exception as exc:
            return {"provider": self.platform, "available": False, "error": str(exc)}

    def fetch_trends(self, limit=20):
        """
        Uses snscrape to extract recent high-engagement posts as trend signals.
        """
        try:
            import snscrape.modules.twitter as sntwitter
        except Exception as exc:
            raise RuntimeError(f"snscrape import failed: {exc}") from exc

        now = datetime.utcnow()
        records = []
        seen_text = set()

        query = "lang:en min_faves:200 -filter:replies -filter:links"
        for tweet in sntwitter.TwitterSearchScraper(query).get_items():
            text = (tweet.content or "").strip()
            if not text:
                continue
            normalized = text.lower()
            if normalized in seen_text:
                continue
            seen_text.add(normalized)

            hashtags = [h.lower() for h in (tweet.hashtags or [])]
            engagement = (tweet.likeCount or 0) + (tweet.retweetCount or 0) + (tweet.replyCount or 0)
            source_url = f"https://x.com/{tweet.user.username}/status/{tweet.id}"

            records.append(
                {
                    "platform": self.platform,
                    "text": text[:200],
                    "hashtags": hashtags[:10],
                    "engagement_count": engagement,
                    "source_url": source_url,
                    "language": getattr(tweet, "lang", "en") or "en",
                    "collected_at": now,
                }
            )
            if len(records) >= limit:
                break

        if not records:
            raise RuntimeError("No X trend items could be extracted via snscrape")
        return records
