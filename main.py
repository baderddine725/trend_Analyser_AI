from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import logging
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
from sqlalchemy import desc

# Import utilities
from utils import (
    TrendAnalyzer,
    ContentRecommender,
    SocialMediaAPI,
    get_mock_trends
)
from utils.trend_predictor import TrendPredictor
from models import Trend, TrendPrediction, TrendEngagement # Assuming models.py is defined elsewhere


# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Get the absolute path of the current directory
BASE_DIR = Path(__file__).resolve().parent

# Initialize FastAPI app
app = FastAPI(title="Social Media Trend Analyzer")

# Mount static files with absolute path
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Initialize templates with absolute path
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Initialize components
api_client = SocialMediaAPI()
trend_analyzer = TrendAnalyzer()
content_recommender = ContentRecommender()
trend_predictor = TrendPredictor() # Added trend predictor initialization

@app.get("/")
async def index(request: Request):
    try:
        logger.info("Accessing index route")
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        logger.error(f"Error in index route: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dashboard")
async def dashboard(request: Request):
    try:
        logger.info("Accessing dashboard route")
        return templates.TemplateResponse("dashboard.html", {"request": request})
    except Exception as e:
        logger.error(f"Error in dashboard route: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/trends")
async def get_trends():
    try:
        # Try to get real data, fallback to mock data
        tiktok_trends = api_client.get_tiktok_trends()
        twitter_trends = api_client.get_twitter_trends()
    except Exception as e:
        logger.warning(f"Failed to get real trends, falling back to mock data: {str(e)}")
        tiktok_trends, twitter_trends = get_mock_trends()

    analyzed_trends = trend_analyzer.analyze_trends(tiktok_trends, twitter_trends)
    return analyzed_trends

@app.get("/api/recommendations")
async def get_recommendations(topic: str):
    recommendations = content_recommender.get_recommendations(topic)
    return recommendations

@app.post("/api/generate-content")
async def generate_content(content_type: str, topic: str):
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
    return content

@app.get("/api/trend-predictions")
async def get_trend_predictions():
    try:
        # Get historical trends from the last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        historical_trends = []

        from db import db  # Import here to avoid circular imports

        # Using context manager for database session
        with db.session() as session:
            db_trends = session.query(Trend).filter(
                Trend.created_at >= thirty_days_ago
            ).all()

            for trend in db_trends:
                historical_trends.append({
                    'text': trend.text,
                    'timestamp': trend.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'view_count': trend.view_count
                })

            # Get predictions for trending topics
            topic_forecasts = trend_predictor.get_trending_topics_forecast(historical_trends)

            # Store predictions in database
            for topic, predictions in topic_forecasts.items():
                trend = session.query(Trend).filter(
                    Trend.text.ilike(topic)
                ).order_by(desc(Trend.created_at)).first()

                if trend:
                    for pred in predictions:
                        prediction = TrendPrediction(
                            trend_id=trend.id,
                            predicted_views=pred['predicted_views'],
                            confidence_score=pred['confidence'],
                            prediction_date=datetime.utcnow(),
                            target_date=datetime.strptime(pred['date'], '%Y-%m-%d')
                        )
                        session.add(prediction)

            session.commit()

        return {
            'predictions': topic_forecasts,
            'updated_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        }
    except Exception as e:
        logger.error(f"Error generating trend predictions: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))



if __name__ == "__main__":
    import uvicorn
    logger.info("Starting FastAPI application...")
    try:
        uvicorn.run(
            "main:app", 
            host="0.0.0.0", 
            port=5001, 
            reload=True,
            log_level="debug"
        )
    except Exception as e:
        logger.error(f"Failed to start FastAPI application: {str(e)}", exc_info=True)
        sys.exit(1)