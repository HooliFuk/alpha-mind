# agents/scoring_agent.py
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


class AKUFINScoringAgent:
    """AKUFIN Multi-Factor Scoring Engine"""

    def __init__(self):
        self.market = MarketDataFetcher()
        self.indicators = TechnicalIndicators()

    async def analyze(self, ticker: str) -> dict:
        """Generate AKUFIN Score 1-10"""
        try:
            logger.info(
                f"AKUFIN Scoring Agent: {ticker}"
            )
            df = self.market.get_historical_bars(
                ticker, period="6mo"
            )
            if df.empty:
                return self._default_score(ticker)

            analysis = self.indicators.get_full_analysis(
                df, ticker
            )
            if "error" in analysis:
                return self._default_score(ticker)

            info = self.market.get_basic_info(ticker)

            prompt = f"""
You are the AKUFIN Multi-Factor Scoring Engine.
Analyze and output an AKUFIN Score.

TICKER: {ticker}
PRICE: ${analysis['current_price']}
TREND: {analysis['trend']}
RSI: {analysis['rsi']['value']} ({analysis['rsi']['signal']})
MACD: {analysis['macd']['signal']}
BB Position: {analysis['bollinger_bands']['position']}
Golden Cross: {analysis['moving_averages']['golden_cross']}
Volume Spike: {analysis['volume']['volume_spike']}
Above VWAP: {analysis['vwap']['price_above_vwap']}
Sector: {info.get('sector', 'Unknown')}
PE Ratio: {info.get('pe_ratio', 0)}

Output ONLY this JSON:
{{
    "akufin_score": 7,
    "technical_score": 8,
    "fundamental_score": 6,
    "sentiment_score": 7,
    "primary_signal": "BULLISH",
    "key_driver": "Brief description",
    "three_month_outlook": "POSITIVE",
    "risk_level": "MEDIUM"
}}
Rules: All scores integers 1-10.
primary_signal: BULLISH/BEARISH/NEUTRAL
three_month_outlook: POSITIVE/NEGATIVE/NEUTRAL
risk_level: LOW/MEDIUM/HIGH
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
            result["current_price"] = (
                analysis["current_price"]
            )
            logger.info(
                f"AKUFIN Scoring: {ticker} "
                f"→ {result.get('akufin_score')}/10"
            )
            return result

        except Exception as e:
            logger.error(
                f"AKUFIN Scoring error {ticker}: {e}"
            )
            return self._default_score(ticker)

    def _default_score(self, ticker: str) -> dict:
        return {
            "akufin_score": 5,
            "technical_score": 5,
            "fundamental_score": 5,
            "sentiment_score": 5,
            "primary_signal": "NEUTRAL",
            "key_driver": "Insufficient data",
            "three_month_outlook": "NEUTRAL",
            "risk_level": "MEDIUM",
            "ticker": ticker
        }