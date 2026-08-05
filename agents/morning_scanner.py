# agents/morning_scanner.py
# AKUFIN - Intelligence for Wealth Accrual
# Multi-Session Market Scanner
import sys
import os
sys.path.append(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)

from tools.market_data import MarketDataFetcher
from tools.indicators import TechnicalIndicators
from agents.human_gate import AKUFINHumanGate
from monitoring.telegram_alerts import AKUFINTelegram
from monitoring.logger import get_logger

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
    Supports Pre-Market, Regular, and After-Hours.
    Sends signals to Telegram for your approval.
    """

    def __init__(self):
        self.market = MarketDataFetcher()
        self.indicators = TechnicalIndicators()
        self.human_gate = AKUFINHumanGate()
        self.telegram = AKUFINTelegram()

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
        """
        Calculate safe position size.
        Max risk $100 per trade.
        Max 50 shares per trade.
        """
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
            logger.info(
                f"AKUFIN scanning {ticker} SNIPER"
            )
            result = self.scan_ticker(ticker, "SNIPER")
            if result and result["signal"] == "BUY":
                all_signals.append(result)

        for ticker in FORTRESS_WATCHLIST:
            logger.info(
                f"AKUFIN scanning {ticker} FORTRESS"
            )
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

    def _run_pre_market_scan(self):
        """Pre-market 4AM-9:30AM scan only no execution"""
        logger.info("AKUFIN Pre-Market Scan starting")

        self.telegram.send_message(
            "💎 <b>AKUFIN PRE-MARKET SCAN</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "🔍 Scanning for gaps and setups...\n"
            "📰 Analyzing overnight news...\n"
            "⚡ Preparing SNIPER watchlist...\n\n"
            "No trades yet. Waiting for market open."
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
                f"Will alert at 9:35 AM ET."
            )
        else:
            self.telegram.send_message(
                "📋 <b>AKUFIN PRE-MARKET</b>\n"
                "No strong setups found yet.\n"
                "Will scan again at market open."
            )

    def _run_after_hours_scan(self):
        """After-hours 4PM-8PM earnings and news focus"""
        logger.info("AKUFIN After-Hours Scan starting")

        self.telegram.send_message(
            "💎 <b>AKUFIN AFTER-HOURS SCAN</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "🏰 FORTRESS mode active\n"
            "📊 Scanning earnings reactions...\n"
            "⚠️ High risk: Wide spreads\n\n"
            "Only high conviction FORTRESS trades."
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

        if signals:
            logger.info(
                f"AKUFIN after-hours: "
                f"{len(signals)} FORTRESS signals"
            )
            for signal in signals[:1]:
                self.human_gate.process_signal(
                    signal,
                    timeout_seconds=180
                )
        else:
            self.telegram.send_message(
                "🏰 <b>AKUFIN AFTER-HOURS</b>\n"
                "No high conviction FORTRESS signals.\n"
                "Market analysis complete for today."
            )

        self.human_gate.send_daily_report()

    def _run_regular_session_scan(
        self,
        session: str
    ):
        """Regular market hours full scan and execution"""
        logger.info(
            f"AKUFIN Regular Session Scan: {session}"
        )

        if session == "LUNCH_LULL":
            self.telegram.send_message(
                "💎 <b>AKUFIN LUNCH LULL</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "📉 Volume dropping at lunch.\n"
                "Managing existing positions only.\n"
                "No new entries recommended.\n"
                "Next scan at 2:00 PM ET."
            )
            return

        self.telegram.send_message(
            f"💎 <b>AKUFIN {session}</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "🔍 Scanning 16 tickers...\n"
            "Sending top signals shortly."
        )

        signals = self.run_full_scan()
        self.telegram.send_morning_scan(signals)

        if signals:
            logger.info(
                f"AKUFIN processing top "
                f"{min(2, len(signals))} signals"
            )
            for signal in signals[:2]:
                result = self.human_gate.process_signal(
                    signal,
                    timeout_seconds=300
                )
                logger.info(
                    f"AKUFIN: {signal['ticker']} "
                    f"→ {result.get('status')}"
                )
        else:
            logger.info(
                "AKUFIN: No signals this session"
            )

    def run(self):
        """
        AKUFIN Multi-Session Scanner.
        Runs different logic for each session.
        Called automatically or manually.
        """
        from config.trading_hours import (
            get_current_session,
            get_session_strategy
        )

        session = get_current_session()
        strategy = get_session_strategy(session)

        logger.info(
            f"AKUFIN Scanner | Session: {session} | "
            f"Strategy: {strategy['strategy']}"
        )

        # Send session briefing to Telegram
        self.telegram.send_message(
            f"💎 <b>AKUFIN {session}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 Strategy: {strategy['strategy']}\n"
            f"⚠️ Risk Level: {strategy['risk_level']}\n\n"
            f"<i>{strategy['akufin_action']}</i>"
        )

        # Weekend or after hours closed
        if session in ["WEEKEND", "MARKET_CLOSED"]:
            logger.info(
                "AKUFIN: Market closed. No scan."
            )
            return

        # Opening bell - too volatile
        if session == "OPENING_BELL":
            logger.info(
                "AKUFIN: Opening bell. Waiting."
            )
            return

        # Pre-market - scan only no execution
        if session == "PRE_MARKET":
            self._run_pre_market_scan()
            return

        # After-hours - FORTRESS only
        if session == "AFTER_HOURS":
            self._run_after_hours_scan()
            return

        # Regular session - full scan and execution
        if session in [
            "MORNING_SESSION",
            "AFTERNOON_SESSION",
            "LUNCH_LULL"
        ]:
            self._run_regular_session_scan(session)
            return

        # Fallback
        logger.warning(
            f"AKUFIN: Unknown session {session}"
        )