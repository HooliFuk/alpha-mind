# database/trade_repository.py
from database.connection import get_session, init_db
from database.models import Trade, Signal
from monitoring.logger import get_logger
from datetime import datetime, timedelta

logger = get_logger(__name__)


class TradeRepository:
    def __init__(self):
        init_db()

    def create_trade(self, data: dict) -> Trade:
        session = get_session()
        try:
            trade = Trade(**data)
            session.add(trade)
            session.commit()
            session.refresh(trade)
            logger.info(f"Trade recorded: {data.get('ticker')} {data.get('side')}")
            return trade
        except Exception as e:
            logger.error(f"Failed to record trade: {e}")
            session.rollback()
            raise
        finally:
            session.close()

    def get_open_positions_count(self) -> int:
        session = get_session()
        try:
            count = session.query(Trade).filter(Trade.status == "OPEN").count()
            return count
        finally:
            session.close()

    def get_todays_pnl(self) -> float:
        session = get_session()
        try:
            today = datetime.utcnow().date()
            trades = session.query(Trade).filter(
                Trade.entry_time >= today,
                Trade.status == "CLOSED"
            ).all()
            return sum(t.pnl for t in trades)
        finally:
            session.close()

    def record_signal(self, signal_data: dict):
        session = get_session()
        try:
            signal = Signal(**signal_data)
            session.add(signal)
            session.commit()
        except Exception as e:
            logger.error(f"Failed to record signal: {e}")
            session.rollback()
        finally:
            session.close()