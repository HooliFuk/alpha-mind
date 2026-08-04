# database/connection.py
# AKUFIN - Intelligence for Wealth Accrual
# Database Connection - Supabase PostgreSQL
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from monitoring.logger import get_logger

logger = get_logger(__name__)

Base = declarative_base()


def get_database_url() -> str:
    """
    Get database URL from environment.
    Works on both localhost and Streamlit Cloud.
    """
    # Try environment variable first
    db_url = os.getenv("DATABASE_URL", "")

    # Try Streamlit secrets if no env var
    if not db_url:
        try:
            import streamlit as st
            if hasattr(st, 'secrets'):
                db_url = st.secrets.get(
                    "DATABASE_URL", ""
                )
        except Exception:
            pass

    # Fallback to SQLite if nothing found
    if not db_url:
        logger.warning(
            "No DATABASE_URL found. "
            "Using SQLite fallback."
        )
        db_url = "sqlite:///akufin.db"

    # Fix Heroku/Supabase postgres:// prefix
    if db_url.startswith("postgres://"):
        db_url = db_url.replace(
            "postgres://", "postgresql://", 1
        )

    return db_url


def get_engine():
    """Create database engine"""
    db_url = get_database_url()

    # PostgreSQL settings
    if "postgresql" in db_url:
        engine = create_engine(
            db_url,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800,
            echo=False
        )
        logger.info(
            "AKUFIN connected to Supabase PostgreSQL"
        )
    else:
        # SQLite settings (fallback)
        engine = create_engine(
            db_url,
            echo=False,
            connect_args={
                "check_same_thread": False
            }
        )
        logger.info("AKUFIN using SQLite database")

    return engine


def get_session():
    """Get a new database session"""
    Session = sessionmaker(bind=get_engine())
    return Session()


def init_db():
    """
    Initialize all database tables.
    Creates tables if they don't exist.
    Safe to run multiple times.
    """
    try:
        from database.models import Base as ModelBase
        engine = get_engine()
        ModelBase.metadata.create_all(bind=engine)

        # Also create prediction table
        try:
            from prediction_engine.predictor import (
                Prediction
            )
            Base.metadata.create_all(bind=engine)
        except Exception:
            pass

        logger.info(
            "AKUFIN database tables initialized"
        )
        return True
    except Exception as e:
        logger.error(
            f"AKUFIN database init error: {e}"
        )
        return False