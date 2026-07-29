# tools/alpaca_broker.py
import sys
import os
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from config.settings import settings
from monitoring.logger import get_logger

logger = get_logger(__name__)


def safe_float(value, default=0.0) -> float:
    """
    Safely convert any value to float.
    Returns default if value is None or invalid.
    """
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


class AlpacaBroker:
    """
    Single interface to Alpaca Paper Trading.
    All trades go through here.
    """

    def __init__(self):
        self.client = TradingClient(
            api_key=settings.ALPACA_API_KEY,
            secret_key=settings.ALPACA_SECRET_KEY,
            paper=True
        )
        logger.info(
            "Alpaca broker connected (Paper Trading)"
        )

    def get_account(self) -> dict:
        """Get full account details"""
        try:
            acc = self.client.get_account()

            equity = safe_float(acc.equity)
            last_equity = safe_float(acc.last_equity)
            daily_pl = equity - last_equity
            daily_pl_pct = round(
                daily_pl / last_equity * 100, 2
            ) if last_equity > 0 else 0.0

            return {
                "status": str(acc.status),
                "portfolio_value": safe_float(
                    acc.portfolio_value
                ),
                "cash": safe_float(acc.cash),
                "buying_power": safe_float(
                    acc.buying_power
                ),
                "equity": equity,
                "last_equity": last_equity,
                "daily_pl": round(daily_pl, 2),
                "daily_pl_pct": daily_pl_pct,
                "day_trade_count": int(
                    acc.daytrade_count or 0
                )
            }

        except Exception as e:
            logger.error(f"Account fetch error: {e}")
            return {
                "status": "ERROR",
                "portfolio_value": 100000.0,
                "cash": 100000.0,
                "buying_power": 400000.0,
                "equity": 100000.0,
                "last_equity": 100000.0,
                "daily_pl": 0.0,
                "daily_pl_pct": 0.0,
                "day_trade_count": 0
            }

    def get_positions(self) -> list:
        """Get all open positions"""
        try:
            positions = self.client.get_all_positions()
            result = []
            for pos in positions:
                entry = safe_float(pos.avg_entry_price)
                current = safe_float(pos.current_price)
                qty = safe_float(pos.qty)
                unreal_pl = safe_float(pos.unrealized_pl)
                unreal_plpc = safe_float(
                    pos.unrealized_plpc
                ) * 100

                result.append({
                    "symbol": pos.symbol,
                    "qty": qty,
                    "side": str(pos.side),
                    "avg_entry_price": entry,
                    "current_price": current,
                    "market_value": safe_float(
                        pos.market_value
                    ),
                    "unrealized_pl": round(unreal_pl, 2),
                    "unrealized_plpc": round(unreal_plpc, 2),
                    "portfolio": "SNIPER"
                })

            logger.info(
                f"Fetched {len(result)} positions"
            )
            return result

        except Exception as e:
            logger.error(f"Positions fetch error: {e}")
            return []

    def get_orders(self, limit: int = 20) -> list:
        """Get recent orders"""
        try:
            orders = self.client.get_orders()
            result = []
            for order in list(orders)[:limit]:
                result.append({
                    "id": str(order.id),
                    "symbol": order.symbol,
                    "qty": safe_float(order.qty),
                    "side": str(order.side),
                    "type": str(order.type),
                    "status": str(order.status),
                    "filled_price": safe_float(
                        order.filled_avg_price
                    ),
                    "submitted_at": str(
                        order.submitted_at
                    ),
                    "filled_at": str(
                        order.filled_at
                    ) if order.filled_at else "Pending"
                })
            return result

        except Exception as e:
            logger.error(f"Orders fetch error: {e}")
            return []

    def place_market_order(
        self,
        symbol: str,
        qty: int,
        side: str,
        reason: str = ""
    ) -> dict:
        """Place a market order"""
        try:
            order_side = (
                OrderSide.BUY
                if side.lower() == "buy"
                else OrderSide.SELL
            )

            order_request = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=order_side,
                time_in_force=TimeInForce.DAY
            )

            order = self.client.submit_order(order_request)

            logger.info(
                f"Order placed: {side.upper()} "
                f"{qty} {symbol} | ID: {order.id}"
            )

            return {
                "success": True,
                "order_id": str(order.id),
                "symbol": symbol,
                "qty": qty,
                "side": side.upper(),
                "status": str(order.status),
                "reason": reason
            }

        except Exception as e:
            logger.error(
                f"Order failed {side} {qty} {symbol}: {e}"
            )
            return {
                "success": False,
                "error": str(e),
                "symbol": symbol,
                "qty": qty,
                "side": side
            }

    def close_position(self, symbol: str) -> dict:
        """Close an entire position"""
        try:
            self.client.close_position(symbol)
            logger.info(f"Position closed: {symbol}")
            return {"success": True, "symbol": symbol}
        except Exception as e:
            logger.error(
                f"Failed to close {symbol}: {e}"
            )
            return {
                "success": False,
                "error": str(e)
            }

    def get_portfolio_summary(self) -> dict:
        """Full portfolio summary for dashboard"""
        account = self.get_account()
        positions = self.get_positions()
        orders = self.get_orders(limit=10)

        total_unrealized_pl = sum(
            p.get("unrealized_pl", 0)
            for p in positions
        )

        return {
            "account": account,
            "positions": positions,
            "recent_orders": orders,
            "total_positions": len(positions),
            "total_unrealized_pl": round(
                total_unrealized_pl, 2
            ),
            "portfolio_value": account.get(
                "portfolio_value", 100000
            ),
            "cash": account.get("cash", 100000),
            "buying_power": account.get(
                "buying_power", 400000
            ),
            "daily_pl": account.get("daily_pl", 0),
            "daily_pl_pct": account.get(
                "daily_pl_pct", 0
            )
        }