# agents/morning_scanner.py
# AKUFIN - Intelligence for Wealth Accrual
# Morning Market Scanner
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
from config.trading_hours import is_market_open

logger = get_logger(__name__)

# Your daily watchlist
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
    AKUFIN Morning Scanner.
    Runs at market open (9:35 AM ET).
    Scans watchlists for best opportunities.
    Sends top signals to your Telegram.
    Waits for your approval.
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

            # Score the setup 0-10
            score = 0
            signal = "HOLD"
            reasons = []

            # Bullish signals
            if rsi < 35:
                score += 2
                reasons.append("RSI oversold")
            elif rsi < 45:
                score += 1
                reasons.append("RSI bullish")

            if macd in ["BULLISH_CROSSOVER"]:
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

            # Determine signal
            if score >= 6:
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
                "reasoning": ", ".join(reasons),
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
        max_risk_dollars: float = 200
    ) -> int:
        """Calculate safe position size"""
        risk_per_share = abs(price - stop_loss)
        if risk_per_share <= 0:
            return 1
        qty = int(max_risk_dollars / risk_per_share)
        return max(1, min(qty, 50))

    def run_full_scan(self) -> list:
        """
        Scan all watchlist tickers.
        Returns ranked list of signals.
        """
        logger.info(
            "AKUFIN Morning Scanner starting..."
        )
        all_signals = []

        # Scan SNIPER watchlist
        for ticker in SNIPER_WATCHLIST:
            logger.info(f"Scanning {ticker} (SNIPER)")
            result = self.scan_ticker(
                ticker, "SNIPER"
            )
            if result and result["signal"] == "BUY":
                all_signals.append(result)

        # Scan FORTRESS watchlist
        for ticker in FORTRESS_WATCHLIST:
            logger.info(
                f"Scanning {ticker} (FORTRESS)"
            )
            result = self.scan_ticker(
                ticker, "FORTRESS"
            )
            if result and result["signal"] == "BUY":
                all_signals.append(result)

        # Sort by score (highest first)
        all_signals.sort(
            key=lambda x: x["score"],
            reverse=True
        )

        logger.info(
            f"AKUFIN scan complete: "
            f"{len(all_signals)} signals found"
        )
        return all_signals

    def run(self):
        """
        Full morning scan pipeline:
        1. Check market is open
        2. Scan all tickers
        3. Send top signals to Telegram
        4. Process your approvals
        """
        logger.info("AKUFIN Morning Scanner running")

        # Check market is open
        if not is_market_open():
            logger.info(
                "AKUFIN: Market closed. Skipping scan."
            )
            self.telegram.send_message(
                "💎 <b>AKUFIN Scanner</b>\n"
                "Market is closed. No scan today."
            )
            return

        # Send scan started notification
        self.telegram.send_message(
            "💎 <b>AKUFIN MORNING SCAN</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "🔍 Scanning 16 tickers...\n"
            "Will send top signals shortly."
        )

        # Run the scan
        signals = self.run_full_scan()

        if not signals:
            self.telegram.send_morning_scan([])
            return

        # Send summary of what was found
        self.telegram.send_morning_scan(signals)

        # Process top 2 signals through Human Gate
        top_signals = signals[:2]

        for signal in top_signals:
            logger.info(
                f"AKUFIN processing: "
                f"{signal['ticker']}"
            )
            result = self.human_gate.process_signal(
                signal,
                timeout_seconds=300
            )
            logger.info(
                f"AKUFIN result: {result['status']}"
            )

        # Send daily report at end
        self.human_gate.send_daily_report()