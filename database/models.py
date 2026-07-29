# database/models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON, Text
from sqlalchemy.sql import func
from datetime import datetime
from database.connection import Base


class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True)
    ticker = Column(String(10), nullable=False)
    side = Column(String(4))                    # BUY or SELL
    strategy = Column(String(30), default="agent")
    entry_price = Column(Float)
    exit_price = Column(Float)
    quantity = Column(Integer)
    stop_loss = Column(Float)
    take_profit = Column(Float)
    status = Column(String(20), default="OPEN")   # OPEN, CLOSED, BLOCKED
    pnl = Column(Float, default=0.0)
    pnl_pct = Column(Float, default=0.0)
    confidence = Column(Float, default=0.0)
    alpaca_order_id = Column(String(100))
    risk_check_result = Column(JSON)
    agent_reasoning = Column(Text)
    indicators_snapshot = Column(JSON)
    entry_time = Column(DateTime, default=datetime.utcnow)
    exit_time = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())


class Signal(Base):
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True)
    ticker = Column(String(10))
    signal_type = Column(String(10))            # BUY, SELL, HOLD
    confidence = Column(Float)
    strategy = Column(String(30))
    indicators = Column(JSON)
    was_traded = Column(Boolean, default=False)
    trade_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())