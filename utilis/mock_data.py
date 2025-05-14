def get_mock_trends():
    tiktok_trends = [
        {
            'text': 'Morning Routine Challenge',
            'views': 2000000,
            'hashtags': ['morning', 'routine']
        },
        {
            'text': 'Workout Transformation',
            'views': 1500000,
            'hashtags': ['fitness', 'transformation']
        },
        {
            'text': 'Cooking Hack Video',
            'views': 800000,
            'hashtags': ['cooking', 'hack']
        }
    ]

    twitter_trends = [
        {
            'text': 'AI Technology News',
            'tweet_count': 100000,
            'hashtags': ['AI', 'tech']
        },
        {
            'text': 'Environmental Challenge',
            'tweet_count': 80000,
            'hashtags': ['environment', 'sustainability']
        },
        {
            'text': 'Music Festival Updates',
            'tweet_count': 60000,
            'hashtags': ['music', 'festival']
        }
    ]

    return tiktok_trends, twitter_trends
