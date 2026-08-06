# agents/tactical_agent.py
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


class AKUFINTacticalAgent:
    """AKUFIN Tactical Execution Engine"""

    def __init__(self):
        self.market = MarketDataFetcher()
        self.indicators = TechnicalIndicators()

    async def analyze(self, ticker: str) -> dict:
        """Generate precise execution levels"""
        try:
            logger.info(
                f"AKUFIN Tactical Agent: {ticker}"
            )
            df = self.market.get_historical_bars(
                ticker, period="3mo"
            )
            if df.empty:
                return {
                    "error": f"No data for {ticker}",
                    "trade_signal": "HOLD"
                }

            analysis = self.indicators.get_full_analysis(
                df, ticker
            )
            if "error" in analysis:
                return {
                    "error": analysis["error"],
                    "trade_signal": "HOLD"
                }

            price = analysis["current_price"]
            atr = analysis["atr"]["value"]

            prompt = f"""
You are the AKUFIN Tactical Execution Engine.
Generate precise trade levels.

TICKER: {ticker}
PRICE: ${price}
ATR: ${atr:.2f}
TREND: {analysis['trend']}
RSI: {analysis['rsi']['value']} ({analysis['rsi']['signal']})
MACD: {analysis['macd']['signal']}
BB: {analysis['bollinger_bands']['position']}
VWAP: {'ABOVE' if analysis['vwap']['price_above_vwap'] else 'BELOW'}
ATR Stop: ${analysis['atr']['stop_loss']}
ATR Target: ${analysis['atr']['take_profit']}

Output ONLY this JSON:
{{
    "trade_signal": "BUY",
    "entry_price": {round(price, 2)},
    "stop_loss": {analysis['atr']['stop_loss']},
    "take_profit": {analysis['atr']['take_profit']},
    "risk_reward_ratio": 2.0,
    "suggested_hold_period": "3-5 days",
    "volatility_rating": "MEDIUM",
    "execution_urgency": "NORMAL",
    "reasoning": "Brief reasoning"
}}
Rules:
trade_signal: BUY/SELL/HOLD
stop_loss: ATR-based
take_profit: minimum 2:1 R:R
volatility_rating: LOW/MEDIUM/HIGH
execution_urgency: URGENT/NORMAL/WAIT
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
                f"AKUFIN Tactical: {ticker} "
                f"→ {result.get('trade_signal')}"
            )
            return result

        except Exception as e:
            logger.error(
                f"AKUFIN Tactical error {ticker}: {e}"
            )
            return {
                "error": str(e),
                "trade_signal": "HOLD"
            }