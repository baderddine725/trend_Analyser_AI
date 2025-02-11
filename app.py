from flask import Flask, render_template, jsonify, request
import os
from utils.trend_analyzer import TrendAnalyzer
from utils.content_recommender import ContentRecommender
from utils.api_client import SocialMediaAPI
from utils.mock_data import get_mock_trends
from db import db, init_db
from models import Platform, Trend, Content

app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize components
api_client = SocialMediaAPI()
trend_analyzer = TrendAnalyzer()
content_recommender = ContentRecommender()

# Initialize database
init_db(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/trends')
def get_trends():
    try:
        # Try to get real data, fallback to mock data
        tiktok_trends = api_client.get_tiktok_trends()
        twitter_trends = api_client.get_twitter_trends()
    except Exception:
        tiktok_trends, twitter_trends = get_mock_trends()

    analyzed_trends = trend_analyzer.analyze_trends(tiktok_trends, twitter_trends)

    # Store trends in database
    platforms = {
        'tiktok': Platform.query.filter_by(name='TikTok').first() or Platform(name='TikTok'),
        'twitter': Platform.query.filter_by(name='Twitter').first() or Platform(name='Twitter')
    }

    for platform_name, platform in platforms.items():
        if not platform.id:
            db.session.add(platform)
    db.session.commit()

    # Store trends
    trends = tiktok_trends + twitter_trends
    for t in trends:
        platform = platforms['tiktok'] if t in tiktok_trends else platforms['twitter']
        trend = Trend(
            text=t['text'],
            hashtags=t.get('hashtags', []),
            view_count=t.get('views', t.get('tweet_count', 0)),
            platform=platform
        )
        db.session.add(trend)
    db.session.commit()

    return jsonify(analyzed_trends)

@app.route('/api/recommendations')
def get_recommendations():
    trend_topic = request.args.get('topic', '')
    recommendations = content_recommender.get_recommendations(trend_topic)

    # Store recommendations in database
    latest_trend = Trend.query.order_by(Trend.created_at.desc()).first()
    if latest_trend:
        for rec_type, ideas in recommendations.items():
            if isinstance(ideas, list) and rec_type in ['video_ideas', 'image_ideas']:
                for idea in ideas:
                    content = Content(
                        type=rec_type.split('_')[0],
                        suggestion=idea['suggestion'],
                        format=idea['format'],
                        estimated_engagement=idea['estimated_engagement'],
                        trend=latest_trend
                    )
                    db.session.add(content)
        db.session.commit()

    return jsonify(recommendations)

@app.route('/api/generate-content', methods=['POST'])
def generate_content():
    content_type = request.json.get('type')
    topic = request.json.get('topic')

    # Mock content generation
    content = {
        'type': content_type,
        'topic': topic,
        'content': f"Generated {content_type} content for {topic}",
        'suggestions': [
            'Use trending hashtags',
            'Post during peak hours',
            'Include relevant keywords'
        ]
    }
    return jsonify(content)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)