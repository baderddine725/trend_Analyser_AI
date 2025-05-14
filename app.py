from flask import Flask, render_template, jsonify, request
import os
import logging
import sys
# Import utilities from our package
from utils import (
    TrendAnalyzer,
    ContentRecommender,
    SocialMediaAPI,
    get_mock_trends
)
from db import db, init_db
from db_models import Platform, Trend, Content

# Configure logging with more detail
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)

    # Database configuration
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        logger.error("No DATABASE_URL environment variable found")
        sys.exit(1)

    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)

    logger.info(f"Configuring database with URL schema: {database_url.split('@')[0].split('://')[0]}")

    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "connect_args": {
            "sslmode": "require"
        }
    }

    try:
        # Initialize components
        logger.info("Initializing app components...")
        global api_client, trend_analyzer, content_recommender
        api_client = SocialMediaAPI()
        trend_analyzer = TrendAnalyzer()
        content_recommender = ContentRecommender()

        # Initialize database
        logger.info("Initializing database...")
        init_db(app)
        logger.info("Database initialized successfully")
        return app
    except Exception as e:
        logger.error(f"Failed to initialize application: {str(e)}", exc_info=True)
        sys.exit(1)

app = create_app()

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
    except Exception as e:
        logger.warning(f"Failed to get real trends, falling back to mock data: {str(e)}")
        tiktok_trends, twitter_trends = get_mock_trends()

    analyzed_trends = trend_analyzer.analyze_trends(tiktok_trends, twitter_trends)

    try:
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
    except Exception as e:
        logger.error(f"Error storing trends in database: {str(e)}")
        db.session.rollback()

    return jsonify(analyzed_trends)

@app.route('/api/recommendations')
def get_recommendations():
    trend_topic = request.args.get('topic', '')
    recommendations = content_recommender.get_recommendations(trend_topic)

    try:
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
    except Exception as e:
        logger.error(f"Error storing recommendations in database: {str(e)}")
        db.session.rollback()

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
    logger.info("Starting Flask application...")
    try:
        app.run(host='0.0.0.0', port=5001)  # Changed port to 5001
    except Exception as e:
        logger.error(f"Failed to start Flask application: {str(e)}", exc_info=True)
        sys.exit(1)
