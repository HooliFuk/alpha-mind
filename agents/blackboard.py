# agents/blackboard.py
# AKUFIN - Intelligence for Wealth Accrual
import asyncio
from datetime import datetime
from monitoring.logger import get_logger

logger = get_logger(__name__)


class AKUFINBlackboard:
    """Central shared memory for all AKUFIN agents"""

    def __init__(self, ticker: str):
        self.ticker = ticker
        self.created_at = datetime.now().isoformat()
        self.state = {
            "ticker": ticker,
            "scoring_agent": None,
            "tactical_agent": None,
            "macro_agent": None,
            "pattern_agent": None,
            "orchestrator": None,
            "status": "INITIALIZING",
            "errors": [],
            "system": "AKUFIN"
        }
        self._lock = asyncio.Lock()
        logger.info(
            f"AKUFIN Blackboard initialized: {ticker}"
        )

    async def update(
        self, agent_name: str, data: dict
    ):
        """Thread-safe write to blackboard"""
        async with self._lock:
            self.state[agent_name] = data
            logger.info(
                f"AKUFIN Blackboard: {agent_name} "
                f"reported for {self.ticker}"
            )

    def get_state(self) -> dict:
        """Read full blackboard state"""
        return self.state

    def add_error(self, agent: str, error: str):
        """Log agent errors"""
        self.state["errors"].append({
            "agent": agent,
            "error": error,
            "time": datetime.now().isoformat()
        })
        logger.error(
            f"AKUFIN Agent Error [{agent}]: {error}"
        )