# agents/human_gate.py
# AKUFIN - Intelligence for Wealth Accrual
# Human Gate - Connects Telegram to Alpaca
import sys
import os
sys.path.append(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)

from monitoring.telegram_alerts import AKUFINTelegram
from tools.alpaca_broker import AlpacaBroker
from agents.risk_warden import RiskWarden
from database.trade_repository import TradeRepository
from monitoring.logger import get_logger

logger = get_logger(__name__)


class AKUFINHumanGate:
    """
    AKUFIN Human Gate.
    The bridge between AI signals and real execution.
    Every trade must pass through here.
    You approve via Telegram.
    System executes on Alpaca.
    """

    def __init__(self):
        self.telegram = AKUFINTelegram()
        self.broker = AlpacaBroker()
        self.risk_warden = RiskWarden()
        self.trade_repo = TradeRepository()

    def process_signal(
        self,
        signal: dict,
        timeout_seconds: int = 300
    ) -> dict:
        """
        Full pipeline:
        1. Risk check
        2. Send Telegram alert
        3. Wait for your approval
        4. Execute or reject
        5. Send confirmation
        """
        ticker = signal.get("ticker", "N/A")
        logger.info(
            f"AKUFIN Human Gate: {ticker}"
        )

        # Step 1: Risk Warden Check First
        risk_result = self.risk_warden.check_all(
            signal
        )

        if not risk_result["approved"]:
            reasons = risk_result.get(
                "failed_reasons", []
            )
            logger.warning(
                f"AKUFIN Risk blocked: {reasons}"
            )
            self.telegram.send_message(
                f"🛡️ <b>AKUFIN RISK WARDEN</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"Signal blocked for {ticker}:\n"
                f"<i>{chr(10).join(reasons)}</i>"
            )
            return {
                "status": "BLOCKED",
                "ticker": ticker,
                "reasons": reasons
            }

        # Step 2: Send Telegram Signal
        logger.info(
            f"AKUFIN sending {ticker} to Telegram"
        )
        send_result = self.telegram.send_trade_signal(
            signal
        )

        if not send_result.get("success"):
            logger.error(
                "AKUFIN Telegram send failed"
            )
            return {
                "status": "FAILED",
                "reason": "Telegram send failed"
            }

        # Step 3: Wait For Your Decision
        logger.info(
            "AKUFIN waiting for human decision..."
        )
        decision = self.telegram.wait_for_approval(
            timeout_seconds=timeout_seconds
        )

        # Step 4: Execute Based On Decision
        if decision == "YES":
            return self._execute_trade(signal)

        elif decision == "NO":
            self.telegram.send_trade_rejected(
                ticker,
                "Rejected by you via Telegram"
            )
            self._log_rejected_trade(signal, "REJECTED")
            return {
                "status": "REJECTED",
                "ticker": ticker
            }

        elif decision == "WAIT":
            # Re-alert in 15 minutes
            logger.info(
                f"AKUFIN: {ticker} delayed 15 mins"
            )
            import time
            time.sleep(900)  # 15 minutes
            self.telegram.send_message(
                f"⏰ <b>AKUFIN REMINDER</b>\n"
                f"Still waiting on {ticker} signal.\n"
                f"Reply YES, NO, or WAIT"
            )
            # Wait again
            decision2 = self.telegram.wait_for_approval(
                timeout_seconds=300
            )
            if decision2 == "YES":
                return self._execute_trade(signal)
            else:
                self._log_rejected_trade(
                    signal, "EXPIRED"
                )
                return {
                    "status": "EXPIRED",
                    "ticker": ticker
                }

        else:  # TIMEOUT
            self.telegram.send_message(
                f"⏰ <b>AKUFIN TIMEOUT</b>\n"
                f"{ticker} signal expired.\n"
                f"No response received.\n"
                f"Trade cancelled for safety."
            )
            self._log_rejected_trade(
                signal, "TIMEOUT"
            )
            return {
                "status": "TIMEOUT",
                "ticker": ticker
            }

    def _execute_trade(self, signal: dict) -> dict:
        """Execute the approved trade on Alpaca"""
        ticker = signal.get("ticker")
        side = signal.get("signal", "BUY").lower()
        qty = signal.get("quantity", 1)
        reason = signal.get("reasoning", "")

        logger.info(
            f"AKUFIN executing: {side} {qty} {ticker}"
        )

        result = self.broker.place_market_order(
            symbol=ticker,
            qty=qty,
            side=side,
            reason=f"Human approved: {reason}"
        )

        if result.get("success"):
            self.telegram.send_trade_executed(result)
            self._log_trade(signal, result)
            logger.info(
                f"AKUFIN trade executed: {ticker}"
            )
            return {
                "status": "EXECUTED",
                "ticker": ticker,
                "order_id": result.get("order_id")
            }
        else:
            error = result.get("error", "Unknown")
            self.telegram.send_error_alert(
                f"Trade execution failed: {error}"
            )
            logger.error(
                f"AKUFIN execution failed: {error}"
            )
            return {
                "status": "FAILED",
                "ticker": ticker,
                "error": error
            }

    def _log_trade(
        self,
        signal: dict,
        result: dict
    ):
        """Log executed trade to database"""
        try:
            self.trade_repo.create_trade({
                "ticker": signal.get("ticker"),
                "side": signal.get("signal", "BUY"),
                "entry_price": signal.get(
                    "entry_price", 0
                ),
                "quantity": signal.get("quantity", 1),
                "stop_loss": signal.get("stop_loss", 0),
                "take_profit": signal.get(
                    "take_profit", 0
                ),
                "status": "OPEN",
                "alpaca_order_id": result.get(
                    "order_id", ""
                ),
                "agent_reasoning": signal.get(
                    "reasoning", ""
                ),
                "confidence": signal.get(
                    "confidence", 0
                )
            })
        except Exception as e:
            logger.error(f"AKUFIN log trade error: {e}")

    def _log_rejected_trade(
        self,
        signal: dict,
        status: str
    ):
        """Log rejected/timeout trade"""
        try:
            self.trade_repo.create_trade({
                "ticker": signal.get("ticker"),
                "side": signal.get("signal", "BUY"),
                "entry_price": signal.get(
                    "entry_price", 0
                ),
                "quantity": signal.get("quantity", 1),
                "stop_loss": signal.get("stop_loss", 0),
                "take_profit": signal.get(
                    "take_profit", 0
                ),
                "status": status,
                "agent_reasoning": signal.get(
                    "reasoning", ""
                ),
                "confidence": signal.get(
                    "confidence", 0
                )
            })
        except Exception as e:
            logger.error(
                f"AKUFIN log rejected error: {e}"
            )

    def send_daily_report(self):
        """Send daily performance report"""
        try:
            summary = self.broker.get_portfolio_summary()
            account = summary["account"]

            from prediction_engine.predictor import (
                PredictionEngine
            )
            predictor = PredictionEngine()
            predictions = predictor.get_all_predictions()
            total = len(predictions)
            correct = sum(
                1 for p in predictions
                if p.get("prediction_correct") is True
            )
            resolved = sum(
                1 for p in predictions
                if p.get("prediction_correct") is not None
            )
            accuracy = (
                round(correct / resolved * 100, 1)
                if resolved > 0 else 0
            )

            report = {
                "portfolio_value": account.get(
                    "portfolio_value", 0
                ),
                "daily_pl": account.get("daily_pl", 0),
                "open_positions": summary.get(
                    "total_positions", 0
                ),
                "total_predictions": total,
                "accuracy": accuracy,
                "top_signals": (
                    f"{correct}/{resolved} correct"
                    if resolved > 0
                    else "Building track record..."
                )
            }

            self.telegram.send_daily_report(report)
            logger.info("AKUFIN daily report sent")

        except Exception as e:
            logger.error(
                f"AKUFIN daily report error: {e}"
            )
            self.telegram.send_error_alert(str(e))