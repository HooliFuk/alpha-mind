# database/connection.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config.settings import settings
from monitoring.logger import get_logger

logger = get_logger(__name__)

Base = declarative_base()

def get_engine():
    """Create database engine (SQLite for now)"""
    engine = create_engine(
        settings.DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
    )
    return engine

def get_session():
    """Get a new database session"""
    Session = sessionmaker(bind=get_engine())
    return Session()

def init_db():
    """Create all tables"""
    try:
        Base.metadata.create_all(bind=get_engine())
        logger.info("Database initialized successfully")
        print("✅ Database tables created")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        print(f"❌ Database error: {e}")