# database/models.py
# AKUFIN - Intelligence for Wealth Accrual
# All database models in ONE place
from sqlalchemy import (
    Column, Integer, String, Float,
    DateTime, Boolean, JSON, Text
)
from sqlalchemy.sql import func
from datetime import datetime
from database.connection import Base


class Trade(Base):
    __tablename__ = "trades"

    id = Column(
        Integer, primary_key=True, autoincrement=True
    )
    ticker = Column(String(10), nullable=False)
    side = Column(String(4))
    strategy = Column(String(30), default="agent")
    entry_price = Column(Float)
    exit_price = Column(Float)
    quantity = Column(Integer)
    stop_loss = Column(Float)
    take_profit = Column(Float)
    status = Column(String(20), default="OPEN")
    pnl = Column(Float, default=0.0)
    pnl_pct = Column(Float, default=0.0)
    confidence = Column(Float, default=0.0)
    alpaca_order_id = Column(
        String(100), nullable=True
    )
    risk_check_result = Column(JSON, nullable=True)
    agent_reasoning = Column(Text, nullable=True)
    indicators_snapshot = Column(JSON, nullable=True)
    entry_time = Column(
        DateTime, default=datetime.utcnow
    )
    exit_time = Column(DateTime, nullable=True)
    created_at = Column(
        DateTime, server_default=func.now()
    )


class Signal(Base):
    __tablename__ = "signals"

    id = Column(
        Integer, primary_key=True, autoincrement=True
    )
    ticker = Column(String(10))
    signal_type = Column(String(10))
    confidence = Column(Float)
    strategy = Column(String(30))
    indicators = Column(JSON)
    was_traded = Column(Boolean, default=False)
    trade_id = Column(Integer, nullable=True)
    created_at = Column(
        DateTime, server_default=func.now()
    )


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(
        Integer, primary_key=True, autoincrement=True
    )
    ticker = Column(String(10), nullable=False)
    current_price = Column(Float)
    predicted_price = Column(Float)
    predicted_direction = Column(String(10))
    confidence = Column(Float)
    target_date = Column(DateTime)
    days_to_target = Column(Integer)
    reasoning = Column(Text)
    technical_summary = Column(Text)
    catalysts = Column(Text)
    risk_factors = Column(Text)
    strategy = Column(Text)
    portfolio = Column(String(20))
    status = Column(
        String(20), default="ACTIVE"
    )
    actual_price_at_target = Column(
        Float, nullable=True
    )
    prediction_correct = Column(
        Boolean, nullable=True
    )
    accuracy_pct = Column(Float, nullable=True)
    created_at = Column(
        DateTime, server_default=func.now()
    )