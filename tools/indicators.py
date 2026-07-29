# tools/indicators.py
import pandas as pd
import numpy as np
from monitoring.logger import get_logger

logger = get_logger(__name__)


class TechnicalIndicators:
    """
    ALL math happens in this class.
    The AI never calculates indicators.
    The AI only reads the OUTPUT dictionary
    that get_full_analysis() returns.
    """

    @staticmethod
    def rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Relative Strength Index.
        Below 30 = oversold (potential buy).
        Above 70 = overbought (potential sell).
        """
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)
        avg_gain = gain.rolling(
            window=period, min_periods=period
        ).mean()
        avg_loss = loss.rolling(
            window=period, min_periods=period
        ).mean()
        rs = avg_gain / avg_loss.replace(0, 1e-10)
        return 100 - (100 / (1 + rs))

    @staticmethod
    def macd(
        df: pd.DataFrame,
        fast: int = 12,
        slow: int = 26,
        signal_period: int = 9
    ) -> tuple:
        """
        MACD Line, Signal Line, Histogram.
        Crossover = momentum shift.
        """
        ema_fast = df['close'].ewm(
            span=fast, adjust=False
        ).mean()
        ema_slow = df['close'].ewm(
            span=slow, adjust=False
        ).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(
            span=signal_period, adjust=False
        ).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram

    @staticmethod
    def bollinger_bands(
        df: pd.DataFrame,
        period: int = 20,
        std_dev: float = 2.0
    ) -> tuple:
        """
        Upper, Middle, Lower Bollinger Bands.
        Price touching lower band = potential bounce.
        Price touching upper band = potential pullback.
        """
        middle = df['close'].rolling(window=period).mean()
        std = df['close'].rolling(window=period).std()
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        return upper, middle, lower

    @staticmethod
    def ema(df: pd.DataFrame, period: int) -> pd.Series:
        """Exponential Moving Average."""
        return df['close'].ewm(
            span=period, adjust=False
        ).mean()

    @staticmethod
    def atr(
        df: pd.DataFrame, period: int = 14
    ) -> pd.Series:
        """
        Average True Range.
        Used for stop loss and take profit calculation.
        Stop Loss  = price - (ATR x 2)
        Take Profit = price + (ATR x 4)
        This gives us 2:1 reward to risk minimum.
        """
        prev_close = df['close'].shift(1)
        tr1 = df['high'] - df['low']
        tr2 = (df['high'] - prev_close).abs()
        tr3 = (df['low'] - prev_close).abs()
        true_range = pd.concat(
            [tr1, tr2, tr3], axis=1
        ).max(axis=1)
        return true_range.rolling(window=period).mean()

    @staticmethod
    def vwap(df: pd.DataFrame) -> pd.Series:
        """
        Volume Weighted Average Price.
        Institutions use this as a benchmark.
        Price above VWAP = bullish bias.
        Price below VWAP = bearish bias.
        """
        typical = (df['high'] + df['low'] + df['close']) / 3
        return (
            (typical * df['volume']).cumsum()
            / df['volume'].cumsum()
        )

    def get_full_analysis(
        self, df: pd.DataFrame, ticker: str
    ) -> dict:
        """
        THE MAIN FUNCTION.
        Call this to get everything calculated.
        Returns a clean dictionary.
        This dictionary is what gets passed to the AI.
        The AI reads numbers. It does not touch the DataFrame.
        """
        if df.empty or len(df) < 30:
            logger.warning(
                f"Not enough data for {ticker}: "
                f"{len(df)} bars (need 30+)"
            )
            return {
                "error": f"Need 30+ bars. Got {len(df)}"
            }

        try:
            # ── Calculate Everything ──────────────────
            rsi_s = self.rsi(df)
            macd_line, sig_line, hist = self.macd(df)
            bb_up, bb_mid, bb_low = self.bollinger_bands(df)
            ema20 = self.ema(df, 20)
            ema50 = self.ema(df, 50) if len(df) >= 50 else ema20
            ema200 = self.ema(df, 200) if len(df) >= 200 else ema50
            atr_s = self.atr(df)
            vwap_s = self.vwap(df)

            # ── Get Latest Values ─────────────────────
            price = float(df['close'].iloc[-1])
            rsi_val = float(rsi_s.iloc[-1])
            macd_val = float(macd_line.iloc[-1])
            sig_val = float(sig_line.iloc[-1])
            hist_val = float(hist.iloc[-1])
            bb_upper = float(bb_up.iloc[-1])
            bb_middle = float(bb_mid.iloc[-1])
            bb_lower = float(bb_low.iloc[-1])
            ema20_val = float(ema20.iloc[-1])
            ema50_val = float(ema50.iloc[-1])
            ema200_val = float(ema200.iloc[-1])
            atr_val = float(atr_s.iloc[-1])
            vwap_val = float(vwap_s.iloc[-1])
            vol_now = float(df['volume'].iloc[-1])
            vol_avg = float(
                df['volume'].rolling(20).mean().iloc[-1]
            )

            # ── Previous Values for Crossover ─────────
            prev_macd = float(macd_line.iloc[-2])
            prev_sig = float(sig_line.iloc[-2])

            # ── Trend Determination ───────────────────
            if price > ema200_val and ema50_val > ema200_val:
                trend = "STRONG_UPTREND"
            elif price > ema200_val:
                trend = "UPTREND"
            elif price < ema200_val and ema50_val < ema200_val:
                trend = "STRONG_DOWNTREND"
            elif price < ema200_val:
                trend = "DOWNTREND"
            else:
                trend = "SIDEWAYS"

            # ── RSI Signal ────────────────────────────
            if rsi_val >= 70:
                rsi_signal = "OVERBOUGHT"
            elif rsi_val <= 30:
                rsi_signal = "OVERSOLD"
            elif rsi_val >= 55:
                rsi_signal = "BULLISH"
            elif rsi_val <= 45:
                rsi_signal = "BEARISH"
            else:
                rsi_signal = "NEUTRAL"

            # ── MACD Signal ───────────────────────────
            if macd_val > sig_val and prev_macd <= prev_sig:
                macd_signal = "BULLISH_CROSSOVER"
            elif macd_val < sig_val and prev_macd >= prev_sig:
                macd_signal = "BEARISH_CROSSOVER"
            elif macd_val > sig_val:
                macd_signal = "BULLISH"
            else:
                macd_signal = "BEARISH"

            # ── Bollinger Band Position ───────────────
            if price > bb_upper:
                bb_pos = "ABOVE_UPPER"
            elif price < bb_lower:
                bb_pos = "BELOW_LOWER"
            elif price > bb_middle:
                bb_pos = "UPPER_HALF"
            else:
                bb_pos = "LOWER_HALF"

            # ── Stop Loss and Take Profit ─────────────
            stop_loss = round(price - (atr_val * 2), 2)
            take_profit = round(price + (atr_val * 4), 2)
            risk = price - stop_loss
            reward = take_profit - price
            rr = round(reward / risk, 2) if risk > 0 else 0

            return {
                "ticker": ticker,
                "current_price": round(price, 2),
                "trend": trend,
                "rsi": {
                    "value": round(rsi_val, 2),
                    "signal": rsi_signal
                },
                "macd": {
                    "macd_value": round(macd_val, 4),
                    "signal_value": round(sig_val, 4),
                    "histogram": round(hist_val, 4),
                    "signal": macd_signal
                },
                "bollinger_bands": {
                    "upper": round(bb_upper, 2),
                    "middle": round(bb_middle, 2),
                    "lower": round(bb_lower, 2),
                    "position": bb_pos
                },
                "moving_averages": {
                    "ema_20": round(ema20_val, 2),
                    "ema_50": round(ema50_val, 2),
                    "ema_200": round(ema200_val, 2),
                    "price_above_ema20": price > ema20_val,
                    "price_above_ema50": price > ema50_val,
                    "price_above_ema200": price > ema200_val,
                    "golden_cross": ema50_val > ema200_val,
                    "death_cross": ema50_val < ema200_val,
                },
                "vwap": {
                    "value": round(vwap_val, 2),
                    "price_above_vwap": price > vwap_val
                },
                "atr": {
                    "value": round(atr_val, 2),
                    "stop_loss": stop_loss,
                    "take_profit": take_profit,
                    "risk_reward_ratio": rr
                },
                "volume": {
                    "current": int(vol_now),
                    "average_20d": int(vol_avg),
                    "volume_spike": vol_now > (vol_avg * 1.5),
                    "volume_ratio": round(
                        vol_now / vol_avg, 2
                    ) if vol_avg > 0 else 0
                }
            }

        except Exception as e:
            logger.error(
                f"Indicator error for {ticker}: {e}"
            )
            return {"error": str(e)}