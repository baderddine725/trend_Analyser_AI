from collections import Counter
import re

class TrendAnalyzer:
    def __init__(self):
        self.common_words = set(['the', 'be', 'to', 'of', 'and', 'a', 'in', 'that'])

    def clean_text(self, text):
        # Remove special characters and convert to lowercase
        text = re.sub(r'[^\w\s]', '', text.lower())
        return text

    def extract_keywords(self, text):
        words = self.clean_text(text).split()
        return [w for w in words if w not in self.common_words]

    def analyze_trends(self, tiktok_trends, twitter_trends):
        # Combine trends from both platforms
        all_trends = []
        
        for trend in tiktok_trends:
            keywords = self.extract_keywords(trend['text'])
            all_trends.extend(keywords)
            
        for trend in twitter_trends:
            keywords = self.extract_keywords(trend['text'])
            all_trends.extend(keywords)

        # Count frequency of keywords
        trend_counter = Counter(all_trends)
        
        # Format results
        analyzed_trends = {
            'top_keywords': dict(trend_counter.most_common(10)),
            'platform_comparison': {
                'tiktok': len(tiktok_trends),
                'twitter': len(twitter_trends)
            },
            'trending_topics': [
                {
                    'topic': k,
                    'frequency': v,
                    'sentiment': 'positive' if v > 5 else 'neutral'
                }
                for k, v in trend_counter.most_common(5)
            ]
        }
        
        return analyzed_trends
