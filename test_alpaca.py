# test_alpaca.py
import sys
import os
sys.path.append('.')

from config.settings import settings

print("=" * 55)
print("   ALPACA PAPER TRADING CONNECTION TEST")
print("=" * 55)

try:
    from alpaca.trading.client import TradingClient

    # Connect to Alpaca
    client = TradingClient(
        api_key=settings.ALPACA_API_KEY,
        secret_key=settings.ALPACA_SECRET_KEY,
        paper=True
    )

    # Get account info
    account = client.get_account()

    print(f"\n✅ Connected to Alpaca Paper Trading!")
    print(f"\nAccount Details:")
    print(f"   Status:          {account.status}")
    print(
        f"   Portfolio Value: "
        f"${float(account.portfolio_value):,.2f}"
    )
    print(f"   Cash:            ${float(account.cash):,.2f}")
    print(
        f"   Buying Power:    "
        f"${float(account.buying_power):,.2f}"
    )

    # Get positions
    positions = client.get_all_positions()
    print(f"\nOpen Positions: {len(positions)}")

    if positions:
        for pos in positions:
            print(
                f"   {pos.symbol}: "
                f"{pos.qty} shares @ "
                f"${float(pos.avg_entry_price):.2f} | "
                f"P&L: ${float(pos.unrealized_pl):.2f}"
            )
    else:
        print("   No open positions yet")

    print("\n" + "=" * 55)
    print("   CONNECTION SUCCESSFUL")
    print("=" * 55)

except Exception as e:
    print(f"\n❌ Connection failed: {e}")
    print("\nTroubleshooting:")
    print("1. Check ALPACA_API_KEY in .env")
    print("2. Check ALPACA_SECRET_KEY in .env")
    print("3. Make sure URL has no /v2 at the end")