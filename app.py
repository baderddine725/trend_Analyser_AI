from flask import Flask, render_template, jsonify
from models.database import init_db
from services.tiktok_api import TikTokAPI
from services.twitter_api import TwitterAPI
from services.trend_analyzer import TrendAnalyzer
from services.content_suggester import ContentSuggester
import schedule
import time
import threading

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = '7g1mmDbULPQa2QTn6RvMKO0t7'

    # Initialize services
    app.tiktok_api = TikTokAPI()
    app.twitter_api = TwitterAPI()
    app.trend_analyzer = TrendAnalyzer()
    app.content_suggester = ContentSuggester()

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/dashboard')
    def dashboard():
        return render_template('dashboard.html')

    @app.route('/suggestions')
    def suggestions():
        return render_template('suggestions.html')

    @app.route('/api/trends')
    def get_trends():
        trends = app.trend_analyzer.get_current_trends()
        return jsonify(trends)

    @app.route('/api/suggestions')
    def get_suggestions():
        suggestions = app.content_suggester.get_suggestions()
        return jsonify(suggestions)

    return app

def collect_trend_data(app):
    """Collect trend data from both platforms"""
    tiktok_trends = app.tiktok_api.get_trends()
    twitter_trends = app.twitter_api.get_trends()
    app.trend_analyzer.analyze_trends(tiktok_trends, twitter_trends)

def scheduled_data_collection(app):
    """Run scheduled tasks"""
    while True:
        schedule.run_pending()
        time.sleep(1)

def init_scheduler(app):
    """Initialize the scheduler for data collection"""
    schedule.every(6).hours.do(collect_trend_data, app)
    thread = threading.Thread(target=scheduled_data_collection, args=(app,))
    thread.daemon = True
    thread.start()

if __name__ == '__main__':
    # Create and initialize the application
    app = create_app()

    # Initialize database
    init_db()

    # Initialize scheduler
    init_scheduler(app)

    # Run the application
    app.run(host='0.0.0.0', port=5000, debug=True)