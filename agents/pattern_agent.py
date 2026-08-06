# agents/pattern_agent.py
# AKUFIN - Intelligence for Wealth Accrual
import json
import sys
import os
sys.path.append(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)

from tools.market_data import MarketDataFetcher
from tools.indicators import TechnicalIndicators
from tools.llm_router import get_llm_with_fallback
from monitoring.logger import get_logger

logger = get_logger(__name__)


class AKUFINPatternAgent:
    """AKUFIN Pattern Recognition Engine"""

    def __init__(self):
        self.market = MarketDataFetcher()
        self.indicators = TechnicalIndicators()

    async def analyze(self, ticker: str) -> dict:
        """Detect chart patterns"""
        try:
            logger.info(
                f"AKUFIN Pattern Agent: {ticker}"
            )
            df = self.market.get_historical_bars(
                ticker, period="6mo"
            )
            if df.empty:
                return self._default_pattern(ticker)

            analysis = self.indicators.get_full_analysis(
                df, ticker
            )
            if "error" in analysis:
                return self._default_pattern(ticker)

            price = analysis['current_price']
            bb_upper = analysis['bollinger_bands']['upper']
            bb_lower = analysis['bollinger_bands']['lower']
            bb_width = round(
                (bb_upper - bb_lower) / price * 100, 2
            )
            recent = df['close'].tail(
                10
            ).round(2).tolist()

            prompt = f"""
You are the AKUFIN Pattern Recognition Engine.

TICKER: {ticker}
PRICE: ${price}
TREND: {analysis['trend']}
Last 10 closes: {recent}
BB Width: {bb_width}%
RSI: {analysis['rsi']['value']}
Volume Spike: {analysis['volume']['volume_spike']}
Golden Cross: {analysis['moving_averages']['golden_cross']}
Above VWAP: {analysis['vwap']['price_above_vwap']}

Output ONLY this JSON:
{{
    "detected_pattern": "Bull Flag",
    "pattern_confidence": 75,
    "trend_direction": "UP",
    "trend_strength": "STRONG",
    "breakout_probability": 68,
    "key_resistance": {round(bb_upper, 2)},
    "key_support": {round(bb_lower, 2)},
    "pattern_target": {round(price * 1.05, 2)},
    "pattern_invalidation": {round(price * 0.97, 2)},
    "days_to_resolution": 7
}}
Patterns: Bull Flag, Bear Flag, Cup and Handle,
Double Bottom, Double Top, Ascending Triangle,
Bollinger Squeeze, VWAP Reclaim, Golden Cross Breakout
Rules:
pattern_confidence: 0-100
trend_direction: UP/DOWN
trend_strength: WEAK/MODERATE/STRONG
breakout_probability: 0-100
"""
            llm = get_llm_with_fallback(
                temperature=0.0
            )
            response = llm.invoke(prompt)
            content = response.content.strip()

            if "```json" in content:
                content = content.split(
                    "```json"
                )[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split(
                    "```"
                )[1].split("```")[0].strip()

            result = json.loads(content)
            result["ticker"] = ticker
            logger.info(
                f"AKUFIN Pattern: {ticker} "
                f"→ {result.get('detected_pattern')}"
            )
            return result

        except Exception as e:
            logger.error(
                f"AKUFIN Pattern error {ticker}: {e}"
            )
            return self._default_pattern(ticker)

    def _default_pattern(self, ticker: str) -> dict:
        return {
            "detected_pattern": "Undetermined",
            "pattern_confidence": 50,
            "trend_direction": "NEUTRAL",
            "trend_strength": "WEAK",
            "breakout_probability": 50,
            "ticker": ticker
        }