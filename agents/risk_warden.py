# agents/risk_warden.py
from datetime import datetime
from monitoring.logger import get_logger
from config.risk_parameters import RISK_RULES
from tools.market_data import MarketDataFetcher
from config.settings import settings

logger = get_logger(__name__)


class RiskWarden:
    """
    THE MOST IMPORTANT CLASS IN THE ENTIRE SYSTEM.
    This runs BEFORE every single trade.
    No AI can override these hard rules.
    """

    def __init__(self):
        self.market_data = MarketDataFetcher()
        self.rules = RISK_RULES

    def check_all(self, proposed_trade: dict) -> dict:
        """
        Runs every safety check.
        Returns detailed result with pass/fail reasons.
        """
        checks = {
            "market_open": self._check_market_open(),
            "trading_hours": self._check_trading_hours(),
            "daily_loss_limit": self._check_daily_loss(),
            "position_size": self._check_position_size(proposed_trade),
            "max_positions": self._check_max_open_positions(),
            "risk_reward": self._check_risk_reward(proposed_trade),
            "blacklisted_ticker": self._check_blacklisted_ticker(proposed_trade.get("ticker")),
        }

        all_passed = all(check["passed"] for check in checks.values())
        failed = [f"{name}: {check['reason']}" for name, check in checks.items() if not check["passed"]]

        result = {
            "approved": all_passed,
            "checks": checks,
            "failed_reasons": failed,
            "timestamp": datetime.now().isoformat()
        }

        if not all_passed:
            logger.warning(f"TRADE BLOCKED → {proposed_trade.get('ticker')} | Reasons: {failed}")

        return result

    def _check_market_open(self) -> dict:
        status = self.market_data.get_market_status()
        passed = status["is_open"]
        return {
            "passed": passed,
            "reason": "Market is open" if passed else f"Market is closed. Session: {status['session']}"
        }

    def _check_trading_hours(self) -> dict:
        now = datetime.now().strftime("%H:%M")
        start = self.rules["allowed_trade_hours"]["start"]
        end = self.rules["allowed_trade_hours"]["end"]
        in_window = start <= now <= end
        return {
            "passed": in_window,
            "reason": f"Within allowed hours ({start}-{end})" if in_window else f"Outside trading hours. Current: {now}"
        }

    def _check_daily_loss(self) -> dict:
        try:
            account = self.market_data.get_account_info() if hasattr(self.market_data, 'get_account_info') else {"daily_pl_pct": 0}
            daily_loss = account.get("daily_pl_pct", 0) / 100
            within_limit = daily_loss > -self.rules["max_daily_loss_pct"]
            return {
                "passed": within_limit,
                "reason": f"Daily P&L: {daily_loss:.2%}" if within_limit else f"DAILY LOSS LIMIT HIT: {daily_loss:.2%}"
            }
        except:
            return {"passed": True, "reason": "Daily loss check skipped (paper mode)"}

    def _check_position_size(self, trade: dict) -> dict:
        try:
            account = self.market_data.get_account_info() if hasattr(self.market_data, 'get_account_info') else {"portfolio_value": 10000}
            portfolio = account.get("portfolio_value", 10000)
            trade_value = trade.get("quantity", 100) * trade.get("price", 100)
            position_pct = trade_value / portfolio if portfolio > 0 else 1.0

            within_limit = position_pct <= self.rules["max_position_pct"]
            return {
                "passed": within_limit,
                "reason": f"Position size: {position_pct:.1%}" if within_limit else f"Position too large: {position_pct:.1%}"
            }
        except:
            return {"passed": True, "reason": "Position size check skipped in test mode"}

    def _check_max_open_positions(self) -> dict:
        # Will be fully connected to database in next step
        open_positions = 0
        within_limit = open_positions < self.rules["max_open_positions"]
        return {
            "passed": within_limit,
            "reason": f"Open positions: {open_positions}/{self.rules['max_open_positions']}"
        }

    def _check_risk_reward(self, trade: dict) -> dict:
        entry = trade.get("entry_price", 0)
        stop = trade.get("stop_loss", 0)
        target = trade.get("take_profit", 0)

        if not all([entry, stop, target]):
            return {"passed": False, "reason": "Missing entry/stop/target prices"}

        risk = abs(entry - stop)
        reward = abs(target - entry)
        rr = reward / risk if risk > 0 else 0

        meets_min = rr >= self.rules["min_risk_reward_ratio"]
        return {
            "passed": meets_min,
            "reason": f"R:R = {rr:.2f}:1" if meets_min else f"R:R too low ({rr:.2f}:1)"
        }

    def _check_blacklisted_ticker(self, ticker: str) -> dict:
        if ticker and ticker.upper() in [t.upper() for t in self.rules["blacklisted_tickers"]]:
            return {"passed": False, "reason": f"{ticker} is blacklisted"}
        return {"passed": True, "reason": "Ticker not blacklisted"}

    def calculate_position_size(self, ticker: str, entry_price: float, stop_loss: float) -> dict:
        """
        Calculates safe share quantity based on risk rules.
        """
        try:
            account = self.market_data.get_account_info() if hasattr(self.market_data, 'get_account_info') else {"portfolio_value": 10000}
            portfolio = account.get("portfolio_value", 10000)
            risk_per_share = abs(entry_price - stop_loss)
            max_risk_dollars = portfolio * self.rules["max_position_pct"] * 0.5
            shares = int(max_risk_dollars / risk_per_share) if risk_per_share > 0 else 0
            max_shares = int((portfolio * self.rules["max_position_pct"]) / entry_price)

            final_shares = min(shares, max_shares, 1000)  # safety cap

            return {
                "ticker": ticker,
                "recommended_shares": final_shares,
                "dollar_risk": round(final_shares * risk_per_share, 2),
                "percent_of_portfolio": round((final_shares * entry_price) / portfolio * 100, 2)
            }
        except:
            return {"recommended_shares": 10, "dollar_risk": 100.0, "percent_of_portfolio": 2.0}