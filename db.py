from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
import sys

# Configure logging
logger = logging.getLogger(__name__)

db = SQLAlchemy()
migrate = Migrate()

def init_db(app):
    try:
        logger.info("Initializing SQLAlchemy with app...")
        db.init_app(app)

        logger.info("Initializing Flask-Migrate...")
        migrate.init_app(app, db)

        logger.info("Creating database tables...")
        with app.app_context():
            db.create_all()
            logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}", exc_info=True)
        raise
