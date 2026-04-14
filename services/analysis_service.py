import math
from collections import Counter


class AnalysisService:
    POSITIVE_WORDS = {
        "win", "growth", "viral", "success", "best", "happy", "love", "innovation", "breakthrough"
    }
    NEGATIVE_WORDS = {
        "fail", "crash", "drop", "loss", "bad", "hate", "scam", "problem", "risk"
    }
    TOPIC_KEYWORDS = {
        "technology": {"ai", "tech", "smartphone", "software", "startup", "innovation"},
        "finance": {"stock", "market", "crypto", "fintech", "invest", "trading"},
        "lifestyle": {"routine", "fitness", "wellness", "health", "travel", "fashion"},
        "entertainment": {"music", "movie", "festival", "celebrity", "dance"},
        "food": {"recipe", "cooking", "food", "meal", "restaurant"},
        "sports": {"sports", "match", "championship", "fitness", "athlete"},
    }

    def score_sentiment(self, text):
        tokens = [t.strip("#.,!?").lower() for t in text.split() if t.strip()]
        if not tokens:
            return "neutral", 0.0

        pos_hits = sum(1 for token in tokens if token in self.POSITIVE_WORDS)
        neg_hits = sum(1 for token in tokens if token in self.NEGATIVE_WORDS)
        raw_score = (pos_hits - neg_hits) / max(len(tokens), 1)
        score = max(min(raw_score, 1.0), -1.0)

        if score > 0.05:
            label = "positive"
        elif score < -0.05:
            label = "negative"
        else:
            label = "neutral"
        return label, round(score, 4)

    def detect_topic(self, text, hashtags=None):
        tokens = {t.strip("#.,!?").lower() for t in text.split() if t.strip()}
        if hashtags:
            tokens.update({h.strip("#").lower() for h in hashtags})

        topic_scores = Counter()
        for topic, keywords in self.TOPIC_KEYWORDS.items():
            topic_scores[topic] = len(tokens.intersection(keywords))

        if not topic_scores:
            return "general", 0.0

        topic, score = topic_scores.most_common(1)[0]
        confidence = min(score / 3.0, 1.0)
        if score == 0:
            return "general", 0.0
        return topic, round(confidence, 4)

    def compute_trend_score(self, engagement_count, sentiment_score, recency_hours):
        # Weighted score blending engagement velocity, sentiment, and recency.
        engagement_component = math.log1p(max(engagement_count, 0))
        sentiment_component = 1 + sentiment_score
        recency_component = max(0.2, 1 - (recency_hours / 48.0))
        total = engagement_component * sentiment_component * recency_component
        return round(total, 4)
