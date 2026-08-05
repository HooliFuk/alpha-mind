# database/signal_repository.py
# AKUFIN - Intelligence for Wealth Accrual
# Signal Queue Management
import sys
import os
sys.path.append(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)

from database.connection import get_session, init_db
from database.models import TradeSignal
from monitoring.logger import get_logger
from datetime import datetime

logger = get_logger(__name__)


class SignalRepository:
    """
    Manages the AKUFIN signal queue.
    Scanner saves signals here.
    Dashboard reads from here.
    """

    def __init__(self):
        init_db()

    def save_signal(self, signal_data: dict) -> int:
        """Save a new signal to the queue"""
        session = get_session()
        try:
            signal = TradeSignal(
                ticker=signal_data.get("ticker"),
                signal=signal_data.get("signal"),
                portfolio=signal_data.get("portfolio"),
                score=signal_data.get("score", 0),
                confidence=signal_data.get(
                    "confidence", 0
                ),
                entry_price=signal_data.get(
                    "entry_price", 0
                ),
                stop_loss=signal_data.get(
                    "stop_loss", 0
                ),
                take_profit=signal_data.get(
                    "take_profit", 0
                ),
                quantity=signal_data.get("quantity", 1),
                reasoning=signal_data.get(
                    "reasoning", ""
                )[:500],
                trend=signal_data.get("trend", ""),
                rsi=signal_data.get("rsi", 0),
                status="PENDING"
            )
            session.add(signal)
            session.commit()
            session.refresh(signal)
            logger.info(
                f"AKUFIN signal saved: "
                f"{signal_data.get('ticker')} "
                f"| ID: {signal.id}"
            )
            return signal.id
        except Exception as e:
            logger.error(
                f"AKUFIN save signal error: {e}"
            )
            session.rollback()
            return 0
        finally:
            session.close()

    def get_pending_signals(self) -> list:
        """Get all pending signals for dashboard"""
        session = get_session()
        try:
            signals = session.query(
                TradeSignal
            ).filter(
                TradeSignal.status == "PENDING"
            ).order_by(
                TradeSignal.created_at.desc()
            ).all()

            return [
                self._to_dict(s) for s in signals
            ]
        except Exception as e:
            logger.error(
                f"AKUFIN get signals error: {e}"
            )
            return []
        finally:
            session.close()

    def approve_signal(
        self,
        signal_id: int,
        approved_by: str,
        order_id: str = ""
    ) -> bool:
        """Mark signal as approved and executed"""
        session = get_session()
        try:
            signal = session.query(
                TradeSignal
            ).filter(
                TradeSignal.id == signal_id
            ).first()

            if signal:
                signal.status = "APPROVED"
                signal.approved_by = approved_by
                signal.alpaca_order_id = order_id
                signal.acted_at = datetime.now()
                session.commit()
                logger.info(
                    f"AKUFIN signal approved: "
                    f"{signal_id}"
                )
                return True
            return False
        except Exception as e:
            logger.error(
                f"AKUFIN approve signal error: {e}"
            )
            session.rollback()
            return False
        finally:
            session.close()

    def reject_signal(
        self,
        signal_id: int,
        rejected_by: str
    ) -> bool:
        """Mark signal as rejected"""
        session = get_session()
        try:
            signal = session.query(
                TradeSignal
            ).filter(
                TradeSignal.id == signal_id
            ).first()

            if signal:
                signal.status = "REJECTED"
                signal.approved_by = rejected_by
                signal.acted_at = datetime.now()
                session.commit()
                logger.info(
                    f"AKUFIN signal rejected: "
                    f"{signal_id}"
                )
                return True
            return False
        except Exception as e:
            logger.error(
                f"AKUFIN reject signal error: {e}"
            )
            session.rollback()
            return False
        finally:
            session.close()

    def get_all_signals(
        self, limit: int = 50
    ) -> list:
        """Get all signals history"""
        session = get_session()
        try:
            signals = session.query(
                TradeSignal
            ).order_by(
                TradeSignal.created_at.desc()
            ).limit(limit).all()

            return [
                self._to_dict(s) for s in signals
            ]
        except Exception as e:
            logger.error(
                f"AKUFIN get all signals error: {e}"
            )
            return []
        finally:
            session.close()

    def _to_dict(self, s: TradeSignal) -> dict:
        """Convert TradeSignal to dictionary"""
        return {
            "id": s.id,
            "ticker": s.ticker,
            "signal": s.signal,
            "portfolio": s.portfolio,
            "score": s.score,
            "confidence": s.confidence,
            "entry_price": s.entry_price,
            "stop_loss": s.stop_loss,
            "take_profit": s.take_profit,
            "quantity": s.quantity,
            "reasoning": s.reasoning,
            "trend": s.trend,
            "rsi": s.rsi,
            "status": s.status,
            "approved_by": s.approved_by,
            "alpaca_order_id": s.alpaca_order_id,
            "created_at": (
                s.created_at.strftime(
                    "%Y-%m-%d %H:%M"
                )
                if s.created_at else ""
            ),
            "acted_at": (
                s.acted_at.strftime(
                    "%Y-%m-%d %H:%M"
                )
                if s.acted_at else None
            )
        }