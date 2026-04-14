import os
import logging
from urllib.parse import quote, unquote, urlsplit, urlunsplit
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load variables from local .env file.
load_dotenv(override=True)


def normalize_database_url(raw_url: str) -> str:
    url = (raw_url or "").strip()
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    parsed = urlsplit(url)
    if parsed.scheme not in {"postgresql", "postgresql+psycopg2"}:
        return url

    if "@" not in parsed.netloc:
        return url

    user_info, host_info = parsed.netloc.rsplit("@", 1)
    if ":" in user_info:
        username, password = user_info.split(":", 1)
    else:
        username, password = user_info, ""

    safe_user = quote(unquote(username), safe="")
    safe_pass = quote(unquote(password), safe="")
    safe_netloc = f"{safe_user}:{safe_pass}@{host_info}" if password else f"{safe_user}@{host_info}"
    return urlunsplit((parsed.scheme, safe_netloc, parsed.path, parsed.query, parsed.fragment))

# Get database URL from environment
DATABASE_URL = normalize_database_url(os.getenv("DATABASE_URL") or "")

if not DATABASE_URL:
    logger.error("DATABASE_URL environment variable is not set")
    raise ValueError("DATABASE_URL environment variable is not set")

logger.info("Initializing database connection...")
try:
    # Keep SSL for hosted Postgres but avoid forcing it for localhost/dev URLs.
    connect_args = {}
    if "localhost" not in DATABASE_URL and "127.0.0.1" not in DATABASE_URL:
        connect_args = {"sslmode": "require"}

    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        connect_args=connect_args
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()

    def get_db() -> Session:
        """Get database session."""
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    logger.info("Database connection initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize database: {str(e)}", exc_info=True)
    raise

# Create all tables
def init_db():
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {str(e)}", exc_info=True)
        raise
