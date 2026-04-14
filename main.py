from datetime import datetime, timedelta
from pathlib import Path
import logging
import os
import sys
import threading
from dotenv import load_dotenv

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import desc, text
from sqlalchemy.orm import Session

from database import SessionLocal, get_db, init_db
from models import Content, Trend, TrendPrediction
from services import ETLService
from utils import ContentRecommender, TrendAnalyzer
from utils.trend_predictor import TrendPredictor

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Get the absolute path of the current directory
BASE_DIR = Path(__file__).resolve().parent

# Load .env values for runtime configuration.
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Social Media Trend Analyzer")

# Mount static files
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Initialize templates
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Initialize components
trend_analyzer = TrendAnalyzer()
content_recommender = ContentRecommender()
trend_predictor = TrendPredictor()
etl_service = ETLService()

_etl_thread = None
_etl_stop_event = threading.Event()
_ops_lock = threading.Lock()
_ops_state = {
    "etl_interval_seconds": int(os.getenv("ETL_INTERVAL_SECONDS", "900")),
    "thread_started_at": None,
    "last_run_started_at": None,
    "last_run_finished_at": None,
    "last_run_duration_ms": None,
    "last_run_success": None,
    "last_error": None,
    "last_result": None,
    "total_runs": 0,
    "success_runs": 0,
    "failed_runs": 0,
}


def _serialize_trend(trend: Trend):
    return {
        "id": trend.id,
        "text": trend.text,
        "platform": trend.platform.name if trend.platform else None,
        "hashtags": trend.hashtags or [],
        "view_count": trend.view_count or 0,
        "source_url": trend.source_url,
        "language": trend.language,
        "topic_label": trend.topic_label,
        "sentiment_label": trend.sentiment_label,
        "sentiment_score": trend.sentiment_score,
        "trend_score": trend.trend_score,
        "collected_at": trend.collected_at.isoformat() if trend.collected_at else None,
        "last_seen_at": trend.last_seen_at.isoformat() if trend.last_seen_at else None,
    }


def _run_periodic_etl(interval_seconds: int):
    logger.info("Periodic ETL thread started (interval=%ss)", interval_seconds)
    with _ops_lock:
        _ops_state["thread_started_at"] = datetime.utcnow().isoformat()
    while not _etl_stop_event.is_set():
        db = SessionLocal()
        started = datetime.utcnow()
        with _ops_lock:
            _ops_state["last_run_started_at"] = started.isoformat()
            _ops_state["total_runs"] += 1
        try:
            result = etl_service.run_collection_cycle(db)
            finished = datetime.utcnow()
            duration_ms = int((finished - started).total_seconds() * 1000)
            with _ops_lock:
                _ops_state["last_run_finished_at"] = finished.isoformat()
                _ops_state["last_run_duration_ms"] = duration_ms
                _ops_state["last_run_success"] = True
                _ops_state["last_error"] = None
                _ops_state["last_result"] = result
                _ops_state["success_runs"] += 1
            logger.info(
                "Periodic ETL completed. inserted=%s updated=%s processed=%s",
                result["inserted"],
                result["updated"],
                result["processed_count"],
            )
        except Exception as exc:
            logger.error("Periodic ETL cycle failed: %s", exc, exc_info=True)
            finished = datetime.utcnow()
            duration_ms = int((finished - started).total_seconds() * 1000)
            with _ops_lock:
                _ops_state["last_run_finished_at"] = finished.isoformat()
                _ops_state["last_run_duration_ms"] = duration_ms
                _ops_state["last_run_success"] = False
                _ops_state["last_error"] = str(exc)
                _ops_state["failed_runs"] += 1
            db.rollback()
        finally:
            db.close()
        _etl_stop_event.wait(interval_seconds)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    logger.info("Initializing database...")
    try:
        init_db()
        interval_seconds = int(os.getenv("ETL_INTERVAL_SECONDS", "900"))
        with _ops_lock:
            _ops_state["etl_interval_seconds"] = interval_seconds
        global _etl_thread
        if _etl_thread is None:
            _etl_thread = threading.Thread(
                target=_run_periodic_etl,
                args=(interval_seconds,),
                daemon=True,
            )
            _etl_thread.start()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        sys.exit(1)


@app.on_event("shutdown")
async def shutdown_event():
    _etl_stop_event.set()

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
        # Backward-compatible endpoint now delegates to v1 ETL and analysis.
        etl_service.run_collection_cycle(db)
        live = etl_service.get_live_trends(db, limit=50)
        tiktok_trends = [{"text": t.text} for t in live if (t.platform and t.platform.name == "tiktok")]
        x_trends = [{"text": t.text} for t in live if (t.platform and t.platform.name == "x")]
        analyzed_trends = trend_analyzer.analyze_trends(tiktok_trends, x_trends)
        analyzed_trends["live_trends"] = [_serialize_trend(t) for t in live]
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


@app.post("/api/v1/etl/run")
async def run_etl_now(db: Session = Depends(get_db)):
    try:
        started = datetime.utcnow()
        with _ops_lock:
            _ops_state["last_run_started_at"] = started.isoformat()
            _ops_state["total_runs"] += 1
        result = etl_service.run_collection_cycle(db)
        finished = datetime.utcnow()
        duration_ms = int((finished - started).total_seconds() * 1000)
        with _ops_lock:
            _ops_state["last_run_finished_at"] = finished.isoformat()
            _ops_state["last_run_duration_ms"] = duration_ms
            _ops_state["last_run_success"] = True
            _ops_state["last_error"] = None
            _ops_state["last_result"] = result
            _ops_state["success_runs"] += 1
        return result
    except Exception as e:
        logger.error(f"Error running ETL now: {str(e)}", exc_info=True)
        with _ops_lock:
            _ops_state["last_run_success"] = False
            _ops_state["last_error"] = str(e)
            _ops_state["failed_runs"] += 1
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/trends/live")
async def get_live_trends(limit: int = 50, db: Session = Depends(get_db)):
    try:
        trends = etl_service.get_live_trends(db, limit=max(1, min(limit, 200)))
        return {"count": len(trends), "items": [_serialize_trend(t) for t in trends]}
    except Exception as e:
        logger.error(f"Error fetching live trends: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/trends/top")
async def get_top_trends(limit: int = 20, db: Session = Depends(get_db)):
    try:
        trends = etl_service.get_top_trends(db, limit=max(1, min(limit, 200)))
        return {"count": len(trends), "items": [_serialize_trend(t) for t in trends]}
    except Exception as e:
        logger.error(f"Error fetching top trends: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def basic_health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "ok", "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"health check failed: {e}")


@app.get("/api/v1/ops/etl-status")
async def etl_status():
    with _ops_lock:
        state = dict(_ops_state)
    return {
        "worker": {
            "thread_alive": _etl_thread.is_alive() if _etl_thread else False,
            "stop_requested": _etl_stop_event.is_set(),
            "interval_seconds": state["etl_interval_seconds"],
        },
        "runs": {
            "total": state["total_runs"],
            "success": state["success_runs"],
            "failed": state["failed_runs"],
            "last_success": state["last_run_success"],
        },
        "timing": {
            "thread_started_at": state["thread_started_at"],
            "last_run_started_at": state["last_run_started_at"],
            "last_run_finished_at": state["last_run_finished_at"],
            "last_run_duration_ms": state["last_run_duration_ms"],
        },
        "last_result": state["last_result"],
        "last_error": state["last_error"],
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/api/v1/ops/health")
async def detailed_health(db: Session = Depends(get_db)):
    checks = {}
    overall = "ok"

    try:
        db.execute(text("SELECT 1"))
        checks["database"] = {"status": "ok"}
    except Exception as exc:
        checks["database"] = {"status": "down", "error": str(exc)}
        overall = "degraded"

    provider_checks = etl_service.ingestion_service.providers_healthcheck()
    checks["providers"] = provider_checks
    if any(item.get("available") is False for item in provider_checks):
        overall = "degraded"

    with _ops_lock:
        state = dict(_ops_state)
    checks["etl_worker"] = {
        "thread_alive": _etl_thread.is_alive() if _etl_thread else False,
        "interval_seconds": state["etl_interval_seconds"],
        "last_run_success": state["last_run_success"],
        "last_run_finished_at": state["last_run_finished_at"],
        "failed_runs": state["failed_runs"],
    }
    if not checks["etl_worker"]["thread_alive"]:
        overall = "degraded"

    return {
        "status": overall,
        "service": "trendtitan-api",
        "version": "v1",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks,
    }


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting FastAPI application...")
    try:
        host = os.getenv("UVICORN_HOST", "0.0.0.0")
        port = int(os.getenv("UVICORN_PORT", "5001"))
        log_level = os.getenv("LOG_LEVEL", "debug").lower()
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=True,
            log_level=log_level
        )
    except Exception as e:
        logger.error(f"Failed to start FastAPI application: {str(e)}", exc_info=True)
        sys.exit(1)