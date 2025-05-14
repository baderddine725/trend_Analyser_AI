class SocialMediaAPI:
    def __init__(self):
        # Initialize with mock credentials
        self.tiktok_api_key = "mock_tiktok_key"
        self.twitter_api_key = "mock_twitter_key"

    def get_tiktok_trends(self):
        # Mock TikTok API call
        return [
            {
                'text': 'Dance Challenge 2024',
                'views': 1000000,
                'hashtags': ['dance', 'viral']
            },
            {
                'text': 'Recipe Tutorial Trend',
                'views': 500000,
                'hashtags': ['cooking', 'food']
            }
        ]

    def get_twitter_trends(self):
        # Mock Twitter API call
        return [
            {
                'text': 'Tech News Update',
                'tweet_count': 50000,
                'hashtags': ['tech', 'news']
            },
            {
                'text': 'Sports Championship',
                'tweet_count': 75000,
                'hashtags': ['sports', 'championship']
            }
        ]
