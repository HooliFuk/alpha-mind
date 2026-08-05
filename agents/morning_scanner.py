# agents/morning_scanner.py
# AKUFIN - Intelligence for Wealth Accrual
# Multi-Session Market Scanner
# Saves signals to database for dashboard approval
import sys
import os
sys.path.append(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)

from tools.market_data import MarketDataFetcher
from tools.indicators import TechnicalIndicators
from monitoring.telegram_alerts import AKUFINTelegram
from monitoring.logger import get_logger
from database.signal_repository import SignalRepository

logger = get_logger(__name__)

SNIPER_WATCHLIST = [
    "NVDA", "TSLA", "AMD", "META",
    "AAPL", "MSFT", "AMZN", "GOOGL"
]

FORTRESS_WATCHLIST = [
    "SPY", "QQQ", "AAPL", "MSFT",
    "JNJ", "V", "WMT", "BRK-B"
]


class AKUFINMorningScanner:
    """
    AKUFIN Multi-Session Market Scanner.
    Scans markets across all 3 sessions.
    Saves signals to database.
    Sends Telegram notification.
    User approves via dashboard.
    """

    def __init__(self):
        self.market = MarketDataFetcher()
        self.indicators = TechnicalIndicators()
        self.telegram = AKUFINTelegram()
        self.signal_repo = SignalRepository()

    def scan_ticker(
        self,
        ticker: str,
        portfolio: str
    ) -> dict:
        """Analyze a single ticker for signals"""
        try:
            df = self.market.get_historical_bars(
                ticker, period="3mo"
            )
            if df.empty:
                return None

            analysis = self.indicators.get_full_analysis(
                df, ticker
            )
            if "error" in analysis:
                return None

            price = analysis["current_price"]
            rsi = analysis["rsi"]["value"]
            macd = analysis["macd"]["signal"]
            trend = analysis["trend"]
            volume_spike = analysis["volume"]["volume_spike"]
            above_vwap = analysis["vwap"]["price_above_vwap"]
            above_ema20 = analysis["moving_averages"]["price_above_ema20"]
            above_ema50 = analysis["moving_averages"]["price_above_ema50"]
            golden_cross = analysis["moving_averages"]["golden_cross"]
            stop_loss = analysis["atr"]["stop_loss"]
            take_profit = analysis["atr"]["take_profit"]

            score = 0
            reasons = []

            if rsi < 35:
                score += 2
                reasons.append("RSI oversold")
            elif rsi < 45:
                score += 1
                reasons.append("RSI bullish")

            if macd == "BULLISH_CROSSOVER":
                score += 3
                reasons.append("MACD crossover")
            elif macd == "BULLISH":
                score += 1
                reasons.append("MACD bullish")

            if above_vwap:
                score += 1
                reasons.append("Above VWAP")

            if above_ema20 and above_ema50:
                score += 1
                reasons.append("Above EMAs")

            if golden_cross:
                score += 1
                reasons.append("Golden cross")

            if volume_spike:
                score += 1
                reasons.append("Volume spike")

            if "UPTREND" in trend:
                score += 1
                reasons.append("Uptrend")

            if score >= 4:
                signal = "BUY"
            elif score <= 2:
                signal = "SELL"
            else:
                signal = "HOLD"

            confidence = min(score / 10, 0.92)

            return {
                "ticker": ticker,
                "signal": signal,
                "portfolio": portfolio,
                "score": score,
                "confidence": confidence,
                "entry_price": price,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "quantity": self._calc_quantity(
                    price, stop_loss
                ),
                "reasoning": (
                    ", ".join(reasons)
                    if reasons
                    else "Technical setup"
                ),
                "trend": trend,
                "rsi": rsi
            }

        except Exception as e:
            logger.error(
                f"AKUFIN scan error {ticker}: {e}"
            )
            return None

    def _calc_quantity(
        self,
        price: float,
        stop_loss: float,
        max_risk_dollars: float = 100
    ) -> int:
        """Calculate safe position size"""
        risk_per_share = abs(price - stop_loss)
        if risk_per_share <= 0:
            return 1
        qty = int(max_risk_dollars / risk_per_share)
        return max(1, min(qty, 50))

    def run_full_scan(self) -> list:
        """Scan all watchlist tickers"""
        logger.info("AKUFIN running full scan...")
        all_signals = []

        for ticker in SNIPER_WATCHLIST:
            result = self.scan_ticker(ticker, "SNIPER")
            if result and result["signal"] == "BUY":
                all_signals.append(result)

        for ticker in FORTRESS_WATCHLIST:
            result = self.scan_ticker(
                ticker, "FORTRESS"
            )
            if result and result["signal"] == "BUY":
                all_signals.append(result)

        all_signals.sort(
            key=lambda x: x["score"],
            reverse=True
        )

        logger.info(
            f"AKUFIN scan complete: "
            f"{len(all_signals)} signals found"
        )
        return all_signals

    def _save_signals_and_notify(
        self, signals: list, session_name: str
    ):
        """
        Save top signals to database.
        Send Telegram notification.
        User approves via dashboard.
        """
        if not signals:
            self.telegram.send_message(
                f"💎 <b>AKUFIN {session_name}</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "🔍 Scan complete.\n"
                "No high conviction signals found.\n"
                "Will scan again next session."
            )
            return

        # Save top 3 signals to database
        saved_signals = []
        for signal in signals[:3]:
            signal_id = self.signal_repo.save_signal(
                signal
            )
            if signal_id:
                signal["id"] = signal_id
                saved_signals.append(signal)

        if not saved_signals:
            return

        # Build Telegram notification
        signal_text = ""
        for i, s in enumerate(saved_signals, 1):
            port_icon = (
                "⚡" if s["portfolio"] == "SNIPER"
                else "🏰"
            )
            risk = round(
                s["entry_price"] - s["stop_loss"], 2
            )
            reward = round(
                s["take_profit"] - s["entry_price"], 2
            )
            rr = round(
                reward / risk, 1
            ) if risk > 0 else 0

            signal_text += (
                f"\n{i}. {port_icon} "
                f"<b>{s['ticker']}</b> BUY\n"
                f"   Entry: ${s['entry_price']:.2f} | "
                f"Stop: ${s['stop_loss']:.2f}\n"
                f"   Target: ${s['take_profit']:.2f} | "
                f"R:R: {rr}:1\n"
                f"   Score: {s['score']}/10 | "
                f"Confidence: {s['confidence']*100:.0f}%\n"
                f"   📊 {s['reasoning']}\n"
            )

        self.telegram.send_message(
            f"💎 <b>AKUFIN {session_name} SIGNALS</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔍 Scanned 16 tickers\n"
            f"🎯 Found {len(saved_signals)} signals\n"
            f"{signal_text}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📱 <b>Go to AKUFIN Dashboard</b>\n"
            f"→ Pending Approvals page\n"
            f"→ Review and approve trades\n"
            f"→ alpha-mind.streamlit.app"
        )

        logger.info(
            f"AKUFIN: {len(saved_signals)} signals "
            f"saved and notified"
        )

    def _run_pre_market_scan(self):
        """Pre-market scan - notify only"""
        logger.info("AKUFIN Pre-Market Scan")

        self.telegram.send_message(
            "💎 <b>AKUFIN PRE-MARKET SCAN</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "🔍 Scanning for gaps and setups...\n"
            "⚡ Preparing SNIPER watchlist...\n\n"
            "No trades yet. Market opens at 9:30 AM ET."
        )

        signals = self.run_full_scan()

        if signals:
            top = signals[:3]
            signal_text = ""
            for i, s in enumerate(top, 1):
                signal_text += (
                    f"\n{i}. <b>{s['ticker']}</b> "
                    f"Score: {s['score']}/10 "
                    f"({s['confidence']*100:.0f}%)"
                )
            self.telegram.send_message(
                f"📋 <b>AKUFIN PRE-MARKET WATCHLIST</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"Watch these at market open:"
                f"{signal_text}\n\n"
                f"Signals will be sent at 9:35 AM ET."
            )
        else:
            self.telegram.send_message(
                "📋 <b>AKUFIN PRE-MARKET</b>\n"
                "No strong setups found yet.\n"
                "Will scan again at market open."
            )

    def _run_after_hours_scan(self):
        """After-hours scan - FORTRESS only"""
        logger.info("AKUFIN After-Hours Scan")

        self.telegram.send_message(
            "💎 <b>AKUFIN AFTER-HOURS SCAN</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "🏰 FORTRESS mode active\n"
            "📊 Scanning earnings reactions...\n"
            "⚠️ High risk: Wide spreads"
        )

        signals = []
        for ticker in FORTRESS_WATCHLIST:
            result = self.scan_ticker(
                ticker, "FORTRESS"
            )
            if (
                result
                and result["signal"] == "BUY"
                and result["score"] >= 7
            ):
                signals.append(result)

        self._save_signals_and_notify(
            signals, "AFTER-HOURS"
        )

        # Send daily report
        self._send_daily_report()

    def _run_regular_session_scan(
        self, session: str
    ):
        """Regular session scan with signal saving"""
        logger.info(
            f"AKUFIN Regular Scan: {session}"
        )

        if session == "LUNCH_LULL":
            self.telegram.send_message(
                "💎 <b>AKUFIN LUNCH LULL</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "📉 Volume dropping at lunch.\n"
                "Managing existing positions only.\n"
                "Next scan at 2:00 PM ET."
            )
            return

        signals = self.run_full_scan()
        self._save_signals_and_notify(
            signals, session
        )

    def _send_daily_report(self):
        """Send daily performance summary"""
        try:
            from tools.alpaca_broker import AlpacaBroker
            broker = AlpacaBroker()
            summary = broker.get_portfolio_summary()
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
                if p.get(
                    "prediction_correct"
                ) is not None
            )
            accuracy = (
                round(correct / resolved * 100, 1)
                if resolved > 0 else 0
            )

            self.telegram.send_message(
                f"📊 <b>AKUFIN DAILY REPORT</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"💰 Portfolio: "
                f"<b>${account.get('portfolio_value', 0):,.2f}</b>\n"
                f"📈 Daily P&L: "
                f"<b>${account.get('daily_pl', 0):+,.2f}</b>\n"
                f"📊 Positions: "
                f"<b>{summary.get('total_positions', 0)}</b>\n"
                f"🎯 Predictions: <b>{total}</b>\n"
                f"✅ Accuracy: <b>{accuracy:.1f}%</b>\n\n"
                f"💎 AKUFIN - Intelligence for Wealth Accrual"
            )
        except Exception as e:
            logger.error(
                f"AKUFIN daily report error: {e}"
            )

    def run(self):
        """
        AKUFIN Multi-Session Scanner.
        Saves signals to database.
        Notifies via Telegram.
        User approves via dashboard.
        """
        from config.trading_hours import (
            get_current_session,
            get_session_strategy
        )

        session = get_current_session()
        strategy = get_session_strategy(session)

        logger.info(
            f"AKUFIN Scanner | Session: {session}"
        )

        self.telegram.send_message(
            f"💎 <b>AKUFIN {session}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 Strategy: {strategy['strategy']}\n"
            f"⚠️ Risk: {strategy['risk_level']}\n\n"
            f"<i>{strategy['akufin_action']}</i>"
        )

        if session in ["WEEKEND", "MARKET_CLOSED"]:
            logger.info("AKUFIN: Market closed.")
            return

        if session == "OPENING_BELL":
            logger.info("AKUFIN: Opening bell wait.")
            return

        if session == "PRE_MARKET":
            self._run_pre_market_scan()
            return

        if session == "AFTER_HOURS":
            self._run_after_hours_scan()
            return

        if session in [
            "MORNING_SESSION",
            "AFTERNOON_SESSION",
            "LUNCH_LULL"
        ]:
            self._run_regular_session_scan(session)
            return