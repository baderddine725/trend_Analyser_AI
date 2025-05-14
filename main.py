from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
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
from models import Trend, TrendPrediction, TrendEngagement, Platform, Content
from database import get_db, init_db

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

# Mount static files
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Initialize templates
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Initialize components
api_client = SocialMediaAPI()
trend_analyzer = TrendAnalyzer()
content_recommender = ContentRecommender()
trend_predictor = TrendPredictor()

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    logger.info("Initializing database...")
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        sys.exit(1)

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
async def get_trends(db: Session = Depends(get_db)):
    try:
        logger.info("Fetching trends data")
        # Try to get real data, fallback to mock data
        try:
            tiktok_trends = api_client.get_tiktok_trends()
            twitter_trends = api_client.get_twitter_trends()
        except Exception as e:
            logger.warning(f"Failed to get real trends, falling back to mock data: {str(e)}")
            tiktok_trends, twitter_trends = get_mock_trends()

        analyzed_trends = trend_analyzer.analyze_trends(tiktok_trends, twitter_trends)

        # Store trends in database
        platforms = {
            'tiktok': db.query(Platform).filter_by(name='TikTok').first() or Platform(name='TikTok'),
            'twitter': db.query(Platform).filter_by(name='Twitter').first() or Platform(name='Twitter')
        }

        for platform_name, platform in platforms.items():
            if not platform.id:
                db.add(platform)
        db.commit()

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
            db.add(trend)
        db.commit()

        return analyzed_trends
    except Exception as e:
        logger.error(f"Error in get_trends: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/recommendations")
async def get_recommendations(topic: str, db: Session = Depends(get_db)):
    try:
        logger.info(f"Generating recommendations for topic: {topic}")
        recommendations = content_recommender.get_recommendations(topic)

        # Store recommendations
        latest_trend = db.query(Trend).order_by(desc(Trend.created_at)).first()
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
                        db.add(content)
            db.commit()

        return recommendations
    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/trend-predictions")
async def get_trend_predictions(db: Session = Depends(get_db)):
    try:
        logger.info("Generating trend predictions")
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        historical_trends = []

        logger.debug("Querying historical trends from database")
        db_trends = db.query(Trend).filter(
            Trend.created_at >= thirty_days_ago
        ).all()

        for trend in db_trends:
            historical_trends.append({
                'text': trend.text,
                'timestamp': trend.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'view_count': trend.view_count
            })

        logger.debug(f"Found {len(historical_trends)} historical trends")
        topic_forecasts = trend_predictor.get_trending_topics_forecast(historical_trends)

        # Store predictions
        for topic, predictions in topic_forecasts.items():
            trend = db.query(Trend).filter(
                Trend.text.ilike(topic)
            ).order_by(desc(Trend.created_at)).first()

            if trend:
                logger.debug(f"Storing predictions for trend: {topic}")
                for pred in predictions:
                    prediction = TrendPrediction(
                        trend_id=trend.id,
                        predicted_views=pred['predicted_views'],
                        confidence_score=pred['confidence'],
                        prediction_date=datetime.utcnow(),
                        target_date=datetime.strptime(pred['date'], '%Y-%m-%d')
                    )
                    db.add(prediction)
        db.commit()

        return {
            'predictions': topic_forecasts,
            'updated_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        }
    except Exception as e:
        logger.error(f"Error generating trend predictions: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-content")
async def generate_content(content_type: str, topic: str, db: Session = Depends(get_db)):
    try:
        logger.info(f"Generating {content_type} content for topic: {topic}")
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
        
        # Store generated content in the database
        latest_trend = db.query(Trend).order_by(desc(Trend.created_at)).first()
        if latest_trend:
            new_content = Content(type=content_type, suggestion=content['content'], trend=latest_trend)
            db.add(new_content)
            db.commit()

        return content
    except Exception as e:
        logger.error(f"Error generating content: {str(e)}", exc_info=True)
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
