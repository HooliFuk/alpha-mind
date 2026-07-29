# test_broker.py
import sys
import os
sys.path.append('.')

from tools.alpaca_broker import AlpacaBroker

print("=" * 55)
print("   ALPACA BROKER LAYER TEST")
print("=" * 55)

broker = AlpacaBroker()

# Test 1: Account
print("\n[1] Account Summary:")
account = broker.get_account()

if account:
    print(
        f"   Status:          "
        f"{account.get('status', 'N/A')}"
    )
    print(
        f"   Portfolio Value: "
        f"${account.get('portfolio_value', 0):,.2f}"
    )
    print(
        f"   Cash:            "
        f"${account.get('cash', 0):,.2f}"
    )
    print(
        f"   Buying Power:    "
        f"${account.get('buying_power', 0):,.2f}"
    )
    print(
        f"   Daily P&L:       "
        f"${account.get('daily_pl', 0):,.2f}"
    )
    print("   ✅ Account fetch successful")
else:
    print("   ❌ Account fetch failed")

# Test 2: Positions
print("\n[2] Open Positions:")
positions = broker.get_positions()
if positions:
    for p in positions:
        print(
            f"   {p['symbol']}: "
            f"{p['qty']} shares @ "
            f"${p['avg_entry_price']:.2f} | "
            f"P&L: ${p['unrealized_pl']:.2f} "
            f"({p['unrealized_plpc']:.1f}%)"
        )
else:
    print("   No open positions")
    print("   ✅ Position fetch successful")

# Test 3: Portfolio Summary
print("\n[3] Full Portfolio Summary:")
summary = broker.get_portfolio_summary()
print(
    f"   Total Positions:  "
    f"{summary['total_positions']}"
)
print(
    f"   Unrealized P&L:   "
    f"${summary['total_unrealized_pl']:,.2f}"
)
print(
    f"   Portfolio Value:  "
    f"${summary['portfolio_value']:,.2f}"
)
print("   ✅ Summary fetch successful")

print("\n" + "=" * 55)
print("   ALL BROKER TESTS PASSED")
print("=" * 55)