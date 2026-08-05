# run_scanner.py
# AKUFIN - Intelligence for Wealth Accrual
# Main scanner entry point
# Usage: python run_scanner.py
import sys
import os
import traceback
sys.path.append('.')

from agents.morning_scanner import AKUFINMorningScanner
from monitoring.logger import get_logger

logger = get_logger("AKUFIN_SCANNER")


def main():
    print("=" * 55)
    print("   💎 AKUFIN SCANNER STARTING")
    print("=" * 55)
    logger.info("AKUFIN Scanner starting...")

    try:
        scanner = AKUFINMorningScanner()
        scanner.run()
        logger.info("AKUFIN Scanner complete")
        print("\n✅ AKUFIN Scanner complete")
        print("Check your Telegram for alerts")

    except KeyboardInterrupt:
        print("\n⚠️ Scanner stopped by user")
        logger.info("AKUFIN Scanner stopped by user")

    except Exception as e:
        logger.error(f"AKUFIN Scanner error: {e}")
        print(f"\n❌ Error: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()