# database/connection.py
# AKUFIN - Intelligence for Wealth Accrual
# Database Connection Manager
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from monitoring.logger import get_logger

logger = get_logger(__name__)

Base = declarative_base()


def get_database_url() -> str:
    """
    Get database URL.
    Checks environment then Streamlit secrets.
    """
    db_url = os.getenv("DATABASE_URL", "")

    if not db_url:
        try:
            import streamlit as st
            if hasattr(st, 'secrets'):
                db_url = st.secrets.get(
                    "DATABASE_URL", ""
                )
        except Exception:
            pass

    if not db_url:
        logger.warning(
            "No DATABASE_URL found. Using SQLite."
        )
        db_url = "sqlite:///akufin.db"

    # Fix postgres:// prefix for SQLAlchemy
    if db_url.startswith("postgres://"):
        db_url = db_url.replace(
            "postgres://", "postgresql://", 1
        )

    return db_url


def get_engine():
    """Create database engine"""
    db_url = get_database_url()

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
    Initialize all AKUFIN database tables.
    Import ALL models here to register them.
    """
    try:
        from database.models import (
            Base as ModelBase,
            Trade,
            Signal,
            Prediction
        )
        engine = get_engine()
        ModelBase.metadata.create_all(bind=engine)
        logger.info(
            "AKUFIN database tables ready"
        )
        return True
    except Exception as e:
        logger.error(
            f"AKUFIN database init error: {e}"
        )
        return False