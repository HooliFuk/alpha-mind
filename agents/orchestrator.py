# agents/orchestrator.py
# AKUFIN - Intelligence for Wealth Accrual
# Chief Investment Officer Agent
import asyncio
import json
import sys
import os
sys.path.append(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)

from agents.blackboard import AKUFINBlackboard
from agents.scoring_agent import AKUFINScoringAgent
from agents.tactical_agent import AKUFINTacticalAgent
from agents.macro_agent import AKUFINMacroAgent
from agents.pattern_agent import AKUFINPatternAgent
from tools.llm_router import get_llm_with_fallback
from monitoring.logger import get_logger

logger = get_logger(__name__)


class AKUFINOrchestrator:
    """
    AKUFIN Chief Investment Officer.
    Runs all 4 agents simultaneously.
    Resolves conflicts. Produces final signal.
    """

    def __init__(self):
        self.scoring = AKUFINScoringAgent()
        self.tactical = AKUFINTacticalAgent()
        self.macro = AKUFINMacroAgent()
        self.pattern = AKUFINPatternAgent()

    async def analyze(self, ticker: str) -> dict:
        """Run all 4 agents simultaneously"""
        logger.info(
            f"AKUFIN Orchestrator: {ticker}"
        )

        blackboard = AKUFINBlackboard(ticker)

        async def run_scoring():
            result = await self.scoring.analyze(ticker)
            await blackboard.update(
                "scoring_agent", result
            )

        async def run_tactical():
            result = await self.tactical.analyze(ticker)
            await blackboard.update(
                "tactical_agent", result
            )

        async def run_macro():
            result = await self.macro.analyze(ticker)
            await blackboard.update(
                "macro_agent", result
            )

        async def run_pattern():
            result = await self.pattern.analyze(ticker)
            await blackboard.update(
                "pattern_agent", result
            )

        # Fire all 4 simultaneously
        await asyncio.gather(
            run_scoring(),
            run_tactical(),
            run_macro(),
            run_pattern()
        )

        logger.info(
            f"All 4 AKUFIN agents complete: {ticker}"
        )

        state = blackboard.get_state()

        synthesis_prompt = f"""
You are the AKUFIN Chief Investment Officer.
4 specialized agents analyzed {ticker}.
Synthesize into ONE final signal.

AGENT REPORTS:
{json.dumps(state, indent=2)}

CONFLICT RESOLUTION RULES:
1. Macro risk > 0.7 + Scoring BUY: reduce position 50%
2. All 4 agents agree: boost confidence 10%
3. 2 vs 2 disagreement: signal is HOLD
4. Macro risk > 0.8: override to HOLD
5. AKUFIN Score < 4: override to HOLD or SELL
6. Confidence below 0.65: must be HOLD

Output ONLY this JSON:
{{
    "ticker": "{ticker}",
    "final_signal": "BUY",
    "akufin_score": 8.2,
    "confidence": 0.82,
    "entry_price": 127.50,
    "stop_loss": 124.00,
    "take_profit": 134.50,
    "risk_reward": 2.0,
    "position_size_pct": 3.5,
    "portfolio": "SNIPER",
    "hold_period": "3-5 days",
    "detected_pattern": "Bull Flag",
    "pattern_confidence": 75,
    "macro_risk": 0.3,
    "macro_verdict": "FAVORABLE",
    "agents_agreeing": 4,
    "agents_total": 4,
    "conflict_resolved": false,
    "final_reasoning": "Full explanation here",
    "technical_score": 8,
    "fundamental_score": 7,
    "sentiment_score": 8,
    "pattern_score": 8
}}
Rules:
final_signal: BUY/SELL/HOLD only
confidence: 0.0 to 1.0
position_size_pct: 1.0 to 5.0 max
portfolio: SNIPER or FORTRESS
"""
        try:
            llm = get_llm_with_fallback(
                temperature=0.1
            )
            response = llm.invoke(synthesis_prompt)
            content = response.content.strip()

            if "```json" in content:
                content = content.split(
                    "```json"
                )[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split(
                    "```"
                )[1].split("```")[0].strip()

            final_signal = json.loads(content)
            await blackboard.update(
                "orchestrator", final_signal
            )

            logger.info(
                f"AKUFIN final: {ticker} "
                f"→ {final_signal.get('final_signal')} "
                f"({final_signal.get('confidence', 0)*100:.0f}%)"
            )
            return final_signal

        except Exception as e:
            logger.error(
                f"AKUFIN Orchestrator error: {e}"
            )
            return {
                "ticker": ticker,
                "final_signal": "HOLD",
                "confidence": 0.0,
                "error": str(e),
                "final_reasoning": (
                    "AKUFIN synthesis error. "
                    "Defaulting to HOLD."
                ),
                "akufin_score": 5,
                "technical_score": 5,
                "fundamental_score": 5,
                "sentiment_score": 5,
                "pattern_score": 5,
                "macro_risk": 0.5,
                "agents_agreeing": 0,
                "agents_total": 4
            }

    def analyze_sync(self, ticker: str) -> dict:
        """Synchronous wrapper for Streamlit"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self.analyze(ticker)
            )
            return result
        except Exception as e:
            logger.error(
                f"AKUFIN sync wrapper error: {e}"
            )
            return {
                "ticker": ticker,
                "final_signal": "HOLD",
                "confidence": 0.0,
                "error": str(e),
                "akufin_score": 5,
                "technical_score": 5,
                "fundamental_score": 5,
                "sentiment_score": 5,
                "pattern_score": 5,
                "macro_risk": 0.5,
                "agents_agreeing": 0,
                "agents_total": 4,
                "final_reasoning": "Error occurred"
            }
        finally:
            loop.close()