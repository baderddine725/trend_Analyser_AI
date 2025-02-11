from flask import Flask, render_template, jsonify, request
from utils.trend_analyzer import TrendAnalyzer
from utils.content_recommender import ContentRecommender
from utils.api_client import SocialMediaAPI
from utils.mock_data import get_mock_trends

app = Flask(__name__)

# Initialize components
api_client = SocialMediaAPI()
trend_analyzer = TrendAnalyzer()
content_recommender = ContentRecommender()

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
    return jsonify(analyzed_trends)

@app.route('/api/recommendations')
def get_recommendations():
    trend_topic = request.args.get('topic', '')
    recommendations = content_recommender.get_recommendations(trend_topic)
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
