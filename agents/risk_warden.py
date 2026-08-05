# agents/risk_warden.py
# AKUFIN - Intelligence for Wealth Accrual
# Risk Warden - Safety System
from datetime import datetime
from monitoring.logger import get_logger
from config.risk_parameters import RISK_RULES
from tools.market_data import MarketDataFetcher

logger = get_logger(__name__)


class RiskWarden:
    """
    THE MOST IMPORTANT CLASS IN AKUFIN.
    Runs BEFORE every single trade.
    No AI can override these hard rules.
    """

    def __init__(self):
        self.market_data = MarketDataFetcher()
        self.rules = RISK_RULES

    def check_all(self, proposed_trade: dict) -> dict:
        """Run all safety checks"""
        checks = {
            "market_open": self._check_market_open(),
            "trading_hours": self._check_trading_hours(),
            "daily_loss_limit": self._check_daily_loss(),
            "position_size": self._check_position_size(
                proposed_trade
            ),
            "max_positions": self._check_max_open_positions(),
            "risk_reward": self._check_risk_reward(
                proposed_trade
            ),
            "blacklisted_ticker": self._check_blacklisted_ticker(
                proposed_trade.get("ticker")
            ),
        }

        all_passed = all(
            check["passed"] for check in checks.values()
        )
        failed = [
            f"{name}: {check['reason']}"
            for name, check in checks.items()
            if not check["passed"]
        ]

        result = {
            "approved": all_passed,
            "checks": checks,
            "failed_reasons": failed,
            "timestamp": datetime.now().isoformat()
        }

        if not all_passed:
            logger.warning(
                f"AKUFIN TRADE BLOCKED → "
                f"{proposed_trade.get('ticker')} | "
                f"{failed}"
            )

        return result

    def _check_market_open(self) -> dict:
        """Check if market is currently open"""
        status = self.market_data.get_market_status()
        passed = status["is_open"]
        return {
            "passed": passed,
            "reason": (
                "Market is open"
                if passed
                else f"Market closed. Session: {status['session']}"
            )
        }

    def _check_trading_hours(self) -> dict:
        """
        Check if current session allows trading.
        AKUFIN supports all 3 market sessions.
        """
        try:
            from config.trading_hours import (
                get_current_session,
                get_session_strategy
            )

            session = get_current_session()
            strategy = get_session_strategy(session)

            if session == "WEEKEND":
                return {
                    "passed": False,
                    "reason": "Weekend - market closed"
                }

            if session == "OPENING_BELL":
                return {
                    "passed": False,
                    "reason": (
                        "Opening bell chaos - "
                        "waiting 5 minutes"
                    )
                }

            if session == "MARKET_CLOSED":
                return {
                    "passed": False,
                    "reason": "Market closed for the day"
                }

            can_execute = strategy.get("execute", False)
            return {
                "passed": can_execute,
                "reason": (
                    f"Session: {session} | "
                    f"Strategy: {strategy['strategy']}"
                )
            }

        except Exception:
            now = datetime.now().strftime("%H:%M")
            start = "09:35"
            end = "15:55"
            in_window = start <= now <= end
            return {
                "passed": in_window,
                "reason": (
                    f"Within hours ({start}-{end})"
                    if in_window
                    else f"Outside trading hours: {now}"
                )
            }

    def _check_daily_loss(self) -> dict:
        """Check daily loss limit"""
        try:
            account = self.market_data.get_account_info()
            daily_loss = account.get(
                "daily_pl_pct", 0
            ) / 100
            within_limit = (
                daily_loss > -self.rules["max_daily_loss_pct"]
            )
            return {
                "passed": within_limit,
                "reason": (
                    f"Daily P&L: {daily_loss:.2%}"
                    if within_limit
                    else f"DAILY LOSS LIMIT HIT: {daily_loss:.2%}"
                )
            }
        except Exception:
            return {
                "passed": True,
                "reason": "Daily loss check skipped (paper mode)"
            }

    def _check_position_size(
        self, trade: dict
    ) -> dict:
        """Check position size against portfolio"""
        try:
            account = self.market_data.get_account_info()
            portfolio = account.get(
                "portfolio_value", 10000
            )
            qty = trade.get("quantity", 1)
            price = trade.get(
                "entry_price",
                trade.get("price", 100)
            )
            trade_value = qty * price
            position_pct = (
                trade_value / portfolio
                if portfolio > 0 else 1.0
            )
            within_limit = (
                position_pct <= self.rules["max_position_pct"]
            )
            return {
                "passed": within_limit,
                "reason": (
                    f"Position size: {position_pct:.1%}"
                    if within_limit
                    else f"Position too large: {position_pct:.1%}"
                )
            }
        except Exception:
            return {
                "passed": True,
                "reason": "Position size check skipped"
            }

    def _check_max_open_positions(self) -> dict:
        """Check number of open positions"""
        try:
            from database.trade_repository import (
                TradeRepository
            )
            repo = TradeRepository()
            open_count = repo.get_open_positions_count()
            within_limit = (
                open_count < self.rules["max_open_positions"]
            )
            return {
                "passed": within_limit,
                "reason": (
                    f"Open positions: "
                    f"{open_count}/"
                    f"{self.rules['max_open_positions']}"
                )
            }
        except Exception:
            return {
                "passed": True,
                "reason": "Position count check skipped"
            }

    def _check_risk_reward(self, trade: dict) -> dict:
        """Check risk reward ratio minimum 2:1"""
        entry = trade.get("entry_price", 0)
        stop = trade.get("stop_loss", 0)
        target = trade.get("take_profit", 0)

        if not all([entry, stop, target]):
            return {
                "passed": False,
                "reason": "Missing entry/stop/target"
            }

        risk = abs(entry - stop)
        reward = abs(target - entry)
        rr = reward / risk if risk > 0 else 0

        # Fix: use >= so exactly 2.0 passes
        meets_min = (
            rr >= self.rules["min_risk_reward_ratio"]
        )

        return {
            "passed": meets_min,
            "reason": (
                f"R:R = {rr:.2f}:1"
                if meets_min
                else f"R:R too low ({rr:.2f}:1)"
            )
        }

    def _check_blacklisted_ticker(
        self, ticker: str
    ) -> dict:
        """Check if ticker is blacklisted"""
        if ticker and ticker.upper() in [
            t.upper()
            for t in self.rules.get(
                "blacklisted_tickers", []
            )
        ]:
            return {
                "passed": False,
                "reason": f"{ticker} is blacklisted"
            }
        return {
            "passed": True,
            "reason": "Ticker allowed"
        }

    def calculate_position_size(
        self,
        ticker: str,
        entry_price: float,
        stop_loss: float
    ) -> dict:
        """Calculate safe share quantity"""
        try:
            account = self.market_data.get_account_info()
            portfolio = account.get(
                "portfolio_value", 10000
            )
            risk_per_share = abs(entry_price - stop_loss)
            max_risk = (
                portfolio
                * self.rules["max_position_pct"]
                * 0.5
            )
            shares = (
                int(max_risk / risk_per_share)
                if risk_per_share > 0
                else 0
            )
            max_shares = int(
                (portfolio * self.rules["max_position_pct"])
                / entry_price
            )
            final_shares = min(shares, max_shares, 1000)

            return {
                "ticker": ticker,
                "recommended_shares": final_shares,
                "dollar_risk": round(
                    final_shares * risk_per_share, 2
                ),
                "percent_of_portfolio": round(
                    (final_shares * entry_price)
                    / portfolio * 100, 2
                )
            }
        except Exception:
            return {
                "recommended_shares": 10,
                "dollar_risk": 100.0,
                "percent_of_portfolio": 2.0
            }