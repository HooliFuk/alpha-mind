# tools/market_data.py
import yfinance as yf
import pandas as pd
from datetime import datetime
from monitoring.logger import get_logger
from config.trading_hours import is_market_open, get_current_market_session

logger = get_logger(__name__)


class MarketDataFetcher:
    """
    Single source of truth for ALL price data.
    Every other module gets data through HERE only.
    Never call yfinance directly from another file.
    """

    def get_historical_bars(
        self,
        ticker: str,
        period: str = "1y",
        interval: str = "1d"
    ) -> pd.DataFrame:
        """
        Fetch historical OHLCV price data.

        period options:
            1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y

        interval options:
            1m, 5m, 15m, 30m, 1h, 1d, 1wk, 1mo
        """
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period=period, interval=interval)

            if df.empty:
                logger.warning(f"No data returned for {ticker}")
                return pd.DataFrame()

            # Standardize column names to lowercase
            df.columns = [col.lower() for col in df.columns]
            df.index = pd.to_datetime(df.index)

            # Keep only OHLCV columns
            keep = [
                c for c in
                ['open', 'high', 'low', 'close', 'volume']
                if c in df.columns
            ]
            df = df[keep].dropna()

            logger.info(
                f"Fetched {len(df)} bars for "
                f"{ticker} | period={period} interval={interval}"
            )
            return df

        except Exception as e:
            logger.error(f"Error fetching {ticker}: {e}")
            return pd.DataFrame()

    def get_current_price(self, ticker: str) -> float:
        """
        Returns the most recent closing price.
        """
        try:
            df = self.get_historical_bars(
                ticker, period="5d", interval="1d"
            )
            if df.empty:
                return 0.0
            price = float(df['close'].iloc[-1])
            logger.info(f"Current price {ticker}: ${price}")
            return round(price, 2)
        except Exception as e:
            logger.error(f"Price fetch error {ticker}: {e}")
            return 0.0

    def get_multiple_tickers(
        self,
        tickers: list,
        period: str = "6mo"
    ) -> dict:
        """
        Fetch data for a list of tickers.
        Returns dict: {"AAPL": DataFrame, "TSLA": DataFrame}
        """
        data = {}
        for ticker in tickers:
            df = self.get_historical_bars(ticker, period=period)
            if not df.empty:
                data[ticker] = df
            else:
                logger.warning(f"Skipped {ticker}: no data")
        logger.info(
            f"Loaded {len(data)}/{len(tickers)} tickers"
        )
        return data

    def get_market_status(self) -> dict:
        """
        Returns current market open/close status.
        No API call required.
        """
        return {
            "is_open": is_market_open(),
            "session": get_current_market_session(),
            "timestamp": datetime.now().isoformat()
        }

    def get_basic_info(self, ticker: str) -> dict:
        """
        Returns company name, sector, market cap etc.
        Used for fundamental context in AI reasoning.
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            return {
                "ticker": ticker,
                "name": info.get("longName", ticker),
                "sector": info.get("sector", "Unknown"),
                "industry": info.get("industry", "Unknown"),
                "market_cap": info.get("marketCap", 0),
                "pe_ratio": info.get("trailingPE", 0),
                "week_52_high": info.get("fiftyTwoWeekHigh", 0),
                "week_52_low": info.get("fiftyTwoWeekLow", 0),
                "avg_volume": info.get("averageVolume", 0),
            }
        except Exception as e:
            logger.error(f"Info fetch error {ticker}: {e}")
            return {"ticker": ticker, "error": str(e)}

    def get_account_info(self) -> dict:
        """
        Returns simulated account information for paper trading.
        We will later replace this with real Alpaca connection.
        """
        try:
            return {
                "portfolio_value": 10000.0,
                "buying_power": 10000.0,
                "cash": 10000.0,
                "daily_pl": 125.50,
                "daily_pl_pct": 1.26,
                "status": "ACTIVE"
            }
        except Exception as e:
            logger.error(f"Account info error: {e}")
            return {
                "portfolio_value": 10000.0,
                "buying_power": 10000.0,
                "cash": 10000.0,
                "daily_pl_pct": 0.0,
                "status": "ACTIVE"
            }