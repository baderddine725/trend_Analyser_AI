from datetime import datetime
import re

import requests
from bs4 import BeautifulSoup

class TikTokProvider:
    platform = "tiktok"

    def healthcheck(self):
        try:
            response = requests.get(
                "https://www.tiktok.com/trending",
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10,
            )
            return {
                "provider": self.platform,
                "available": response.status_code < 500,
                "status_code": response.status_code,
            }
        except Exception as exc:
            return {"provider": self.platform, "available": False, "error": str(exc)}

    def fetch_trends(self, limit=20):
        """
        Scrapes hashtag trends from TikTok trending page.
        """
        response = requests.get(
            "https://www.tiktok.com/trending",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=15,
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        now = datetime.utcnow()
        records = []

        hashtag_pattern = re.compile(r"^#?[A-Za-z0-9_]{2,50}$")
        seen = set()

        for anchor in soup.find_all("a", href=True):
            href = anchor["href"]
            text = (anchor.get_text() or "").strip()
            if "/tag/" not in href:
                continue
            hashtag = text if text.startswith("#") else f"#{text}" if text else ""
            if not hashtag or not hashtag_pattern.match(hashtag):
                continue
            normalized = hashtag.lower()
            if normalized in seen:
                continue
            seen.add(normalized)

            records.append(
                {
                    "platform": self.platform,
                    "text": f"{hashtag} trend",
                    "hashtags": [hashtag.lstrip("#").lower()],
                    "engagement_count": 0,
                    "source_url": href if href.startswith("http") else f"https://www.tiktok.com{href}",
                    "language": "en",
                    "collected_at": now,
                }
            )
            if len(records) >= limit:
                break

        if not records:
            raise RuntimeError("No TikTok trend items could be extracted from page")
        return records
        now = datetime.utcnow()
        return [
            {
                "platform": self.platform,
                "text": "Morning Routine Challenge",
                "hashtags": ["morning", "routine"],
                "engagement_count": 2000000,
                "source_url": "https://www.tiktok.com/trending",
                "language": "en",
                "collected_at": now,
            },
            {
                "platform": self.platform,
                "text": "Workout Transformation",
                "hashtags": ["fitness", "transformation"],
                "engagement_count": 1500000,
                "source_url": "https://www.tiktok.com/trending",
                "language": "en",
                "collected_at": now,
            },
        ]
