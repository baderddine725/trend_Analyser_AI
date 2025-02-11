# This file makes the utils directory a Python package
from .trend_analyzer import TrendAnalyzer
from .content_recommender import ContentRecommender
from .api_client import SocialMediaAPI
from .mock_data import get_mock_trends

__all__ = ['TrendAnalyzer', 'ContentRecommender', 'SocialMediaAPI', 'get_mock_trends']
