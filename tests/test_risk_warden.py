# tests/test_risk_warden.py
import sys
import os

# Fix import path - This is the most common fix for this error
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.risk_warden import RiskWarden
from tools.indicators import TechnicalIndicators
from tools.market_data import MarketDataFetcher
from monitoring.logger import get_logger

logger = get_logger("test_risk_warden")


def test_risk_warden():
    print("=" * 70)
    print("     RISK WARDEN + DATABASE INTEGRATION TEST")
    print("=" * 70)

    fetcher = MarketDataFetcher()
    indicators = TechnicalIndicators()
    warden = RiskWarden()

    test_ticker = "AAPL"
    print(f"\nRunning safety test on {test_ticker}...\n")

    # Get technical analysis
    df = fetcher.get_historical_bars(test_ticker, period="6mo")
    analysis = indicators.get_full_analysis(df, test_ticker)

    if "error" in analysis:
        print("❌ Could not get technical analysis")
        return

    proposed_trade = {
        "ticker": test_ticker,
        "signal": "BUY",
        "entry_price": analysis["current_price"],
        "stop_loss": analysis["atr"]["stop_loss"],
        "take_profit": analysis["atr"]["take_profit"],
        "quantity": 15,
        "confidence": 0.82
    }

    print("Proposed Trade:")
    print(f"   Ticker        : {proposed_trade['ticker']}")
    print(f"   Entry Price   : ${proposed_trade['entry_price']}")
    print(f"   Stop Loss     : ${proposed_trade['stop_loss']}")
    print(f"   Take Profit   : ${proposed_trade['take_profit']}")
    print(f"   R:R Ratio     : {analysis['atr']['risk_reward_ratio']}:1\n")

    # Run Risk Warden Check
    result = warden.check_all(proposed_trade)

    print("Risk Warden Decision:")
    print(f"   APPROVED      : {'✅ YES' if result['approved'] else '❌ NO'}")

    if not result['approved']:
        print("\nBlocked Reasons:")
        for reason in result.get('failed_reasons', []):
            print(f"     → {reason}")

    print("\nDetailed Safety Checks:")
    for name, check in result['checks'].items():
        status = "✅" if check['passed'] else "❌"
        print(f"   {status} {name:18} → {check['reason']}")

    # Test Database
    print("\nTesting Database Layer...")
    try:
        from database.trade_repository import TradeRepository
        repo = TradeRepository()
        
        signal_data = {
            "ticker": test_ticker,
            "signal_type": proposed_trade["signal"],
            "confidence": proposed_trade["confidence"],
            "strategy": "technical_agent",
            "indicators": analysis,
            "was_traded": result["approved"]
        }
        repo.record_signal(signal_data)
        print("   ✅ Signal saved to database successfully")

        open_count = repo.get_open_positions_count()
        print(f"   ✅ Current open positions: {open_count}")
        
    except Exception as e:
        print(f"   ❌ Database error: {e}")

    print("\n" + "=" * 70)
    print("TEST COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    test_risk_warden()