# test_setup.py
# Run with: python test_setup.py

import json

print("=" * 55)
print("   ALPHA TRADER - SYSTEM VERIFICATION TEST")
print("=" * 55)

# ── Test 1: Settings ──────────────────────────────────
print("\n[1/6] Testing Settings...")
try:
    from config.settings import settings, validate_settings
    validate_settings()
    print("      ✅ Settings loaded")
except Exception as e:
    print(f"      ❌ Settings error: {e}")

# ── Test 2: Risk Parameters ───────────────────────────
print("\n[2/6] Testing Risk Parameters...")
try:
    from config.risk_parameters import RISK_RULES
    print(f"      ✅ {len(RISK_RULES)} risk rules active")
    print(
        f"      ✅ Max position: "
        f"{RISK_RULES['max_position_pct']*100}%"
    )
except Exception as e:
    print(f"      ❌ Risk parameters error: {e}")

# ── Test 3: Trading Hours ─────────────────────────────
print("\n[3/6] Testing Trading Hours...")
try:
    from config.trading_hours import (
        is_market_open,
        get_current_market_session
    )
    session = get_current_market_session()
    open_status = is_market_open()
    print(f"      ✅ Current session: {session}")
    print(f"      ✅ Market open: {open_status}")
except Exception as e:
    print(f"      ❌ Trading hours error: {e}")

# ── Test 4: Logger ────────────────────────────────────
print("\n[4/6] Testing Logger...")
try:
    from monitoring.logger import get_logger
    logger = get_logger("test")
    logger.info("Logger verification test")
    print("      ✅ Logger working")
    print("      ✅ Check logs/ folder for log file")
except Exception as e:
    print(f"      ❌ Logger error: {e}")

# ── Test 5: Market Data ───────────────────────────────
print("\n[5/6] Testing Market Data...")
try:
    from tools.market_data import MarketDataFetcher
    fetcher = MarketDataFetcher()
    df = fetcher.get_historical_bars("AAPL", period="1mo")
    price = fetcher.get_current_price("SPY")
    status = fetcher.get_market_status()
    print(f"      ✅ AAPL data: {len(df)} bars loaded")
    print(f"      ✅ SPY current price: ${price}")
    print(f"      ✅ Market session: {status['session']}")
except Exception as e:
    print(f"      ❌ Market data error: {e}")

# ── Test 6: Indicators ────────────────────────────────
print("\n[6/6] Testing Technical Indicators...")
try:
    from tools.indicators import TechnicalIndicators
    indicators = TechnicalIndicators()
    df = fetcher.get_historical_bars("SPY", period="6mo")
    result = indicators.get_full_analysis(df, "SPY")

    if "error" in result:
        print(f"      ❌ Indicator error: {result['error']}")
    else:
        print(f"      ✅ Price: ${result['current_price']}")
        print(f"      ✅ Trend: {result['trend']}")
        print(
            f"      ✅ RSI: {result['rsi']['value']} "
            f"({result['rsi']['signal']})"
        )
        print(f"      ✅ MACD: {result['macd']['signal']}")
        print(
            f"      ✅ Stop Loss: "
            f"${result['atr']['stop_loss']}"
        )
        print(
            f"      ✅ Take Profit: "
            f"${result['atr']['take_profit']}"
        )
        print(
            f"      ✅ R:R Ratio: "
            f"{result['atr']['risk_reward_ratio']}:1"
        )

except Exception as e:
    print(f"      ❌ Indicator error: {e}")

print("\n" + "=" * 55)
print("   FULL ANALYSIS OUTPUT (SPY):")
print("=" * 55)
try:
    df = fetcher.get_historical_bars("SPY", period="6mo")
    result = indicators.get_full_analysis(df, "SPY")
    print(json.dumps(result, indent=2))
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 55)
print("   TEST COMPLETE")
print("=" * 55)