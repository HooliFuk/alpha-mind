# agents/macro_agent.py
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
from tools.llm_router import get_llm_with_fallback
from monitoring.logger import get_logger

logger = get_logger(__name__)


class AKUFINMacroAgent:
    """AKUFIN Macro Risk Engine"""

    def __init__(self):
        self.market = MarketDataFetcher()

    async def analyze(self, ticker: str) -> dict:
        """Assess macro risk"""
        try:
            logger.info(
                f"AKUFIN Macro Agent: {ticker}"
            )
            info = self.market.get_basic_info(ticker)

            spy_df = self.market.get_historical_bars(
                "SPY", period="3mo"
            )
            spy_change = 0
            if not spy_df.empty:
                spy_change = round(
                    (
                        spy_df['close'].iloc[-1]
                        - spy_df['close'].iloc[-20]
                    )
                    / spy_df['close'].iloc[-20] * 100,
                    2
                )

            sector = info.get("sector", "Technology")

            prompt = f"""
You are the AKUFIN Macro Risk Analyst.

TICKER: {ticker}
SECTOR: {sector}
SPY 20-DAY RETURN: {spy_change}%
MARKET CAP: ${info.get('market_cap', 0):,}

Output ONLY this JSON:
{{
    "macro_risk_score": 0.3,
    "sector_momentum": "POSITIVE",
    "market_regime": "RISK_ON",
    "correlation_risk": "LOW",
    "hedging_required": false,
    "macro_tailwinds": "Brief description",
    "macro_headwinds": "Brief description",
    "overall_macro_verdict": "FAVORABLE"
}}
Rules:
macro_risk_score: 0.0 (safe) to 1.0 (danger)
sector_momentum: POSITIVE/NEGATIVE/NEUTRAL
market_regime: RISK_ON/RISK_OFF/MIXED
overall_macro_verdict: FAVORABLE/UNFAVORABLE/NEUTRAL
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
            result["sector"] = sector
            logger.info(
                f"AKUFIN Macro: {ticker} "
                f"→ Risk {result.get('macro_risk_score')}"
            )
            return result

        except Exception as e:
            logger.error(
                f"AKUFIN Macro error {ticker}: {e}"
            )
            return {
                "macro_risk_score": 0.5,
                "sector_momentum": "NEUTRAL",
                "market_regime": "MIXED",
                "hedging_required": False,
                "overall_macro_verdict": "NEUTRAL",
                "error": str(e)
            }