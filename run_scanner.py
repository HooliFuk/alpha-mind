# run_scanner.py
# AKUFIN - Run this to start the morning scanner
# Can be run manually or scheduled
import sys
import os
sys.path.append('.')

from agents.morning_scanner import AKUFINMorningScanner
from monitoring.logger import get_logger

logger = get_logger("AKUFIN_SCANNER")


def main():
    logger.info("AKUFIN Morning Scanner starting...")
    scanner = AKUFINMorningScanner()
    scanner.run()
    logger.info("AKUFIN Morning Scanner complete")


if __name__ == "__main__":
    main()