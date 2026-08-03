# prediction_engine/predictor.py
# AKUFIN - Intelligence for Wealth Accrual
# AI Prediction Engine with improved prompting
import sys
import os
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

import json
from datetime import datetime, timedelta
from tools.market_data import MarketDataFetcher
from tools.indicators import TechnicalIndicators
from tools.llm_router import get_llm_with_fallback
from database.connection import get_session, init_db
from database.models import Base
from monitoring.logger import get_logger
from sqlalchemy import (
    Column, Integer, String, Float,
    DateTime, Text, Boolean
)
from sqlalchemy.sql import func

logger = get_logger(__name__)


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(
        Integer, primary_key=True, autoincrement=True
    )
    ticker = Column(String(10), nullable=False)
    current_price = Column(Float)
    predicted_price = Column(Float)
    predicted_direction = Column(String(10))
    confidence = Column(Float)
    target_date = Column(DateTime)
    days_to_target = Column(Integer)
    reasoning = Column(Text)
    technical_summary = Column(Text)
    catalysts = Column(Text)
    risk_factors = Column(Text)
    strategy = Column(Text)
    portfolio = Column(String(20))
    status = Column(String(20), default="ACTIVE")
    actual_price_at_target = Column(Float, nullable=True)
    prediction_correct = Column(Boolean, nullable=True)
    accuracy_pct = Column(Float, nullable=True)
    created_at = Column(
        DateTime, server_default=func.now()
    )


class PredictionEngine:
    """
    AKUFIN AI Prediction Engine.
    Generates specific dated price predictions.
    Portfolio-aware and time-window-aware.
    Every prediction persists until manually deleted.
    """

    def __init__(self):
        self.market_data = MarketDataFetcher()
        self.indicators = TechnicalIndicators()
        init_db()

    def generate_prediction(
        self,
        ticker: str,
        portfolio: str = "SNIPER",
        days_ahead: int = 14
    ) -> dict:
        """
        Generate AKUFIN AI prediction for a ticker.
        Results differ based on portfolio and time window.
        """
        logger.info(
            f"AKUFIN generating prediction: "
            f"{ticker} | {portfolio} | {days_ahead}d"
        )

        df = self.market_data.get_historical_bars(
            ticker, period="6mo"
        )
        if df.empty:
            return {"error": f"No data for {ticker}"}

        analysis = self.indicators.get_full_analysis(
            df, ticker
        )
        if "error" in analysis:
            return {"error": analysis["error"]}

        current_price = analysis["current_price"]
        target_date = (
            datetime.now() + timedelta(days=days_ahead)
        )

        # Portfolio specific settings
        if portfolio == "SNIPER":
            portfolio_context = """
SNIPER PORTFOLIO RULES:
- This is a SHORT TERM aggressive trade
- Target 3-8% price move maximum
- Focus on: momentum, volume, breakouts
- Entry timing is critical
- Stop loss must be tight (1-2x ATR)
- Look for: RSI bounces, MACD crossovers,
  BB breakouts, volume spikes
- Preferred hold time: hours to 3 days
"""
        else:
            portfolio_context = """
FORTRESS PORTFOLIO RULES:
- This is a LONG TERM safe investment
- Target 10-25% price move over weeks/months
- Focus on: trend strength, fundamentals,
  macro environment, sector momentum
- Entry timing is less critical
- Stop loss can be wider (3-4x ATR)
- Look for: golden cross, strong uptrend,
  price above all EMAs, healthy volume
- Preferred hold time: weeks to months
"""

        # Time window specific rules
        if days_ahead == 7:
            time_context = """
7-DAY WINDOW:
- Small move expected: 2-5% maximum
- Focus on immediate price momentum
- Short term catalysts only
- Be conservative with targets
"""
        elif days_ahead == 14:
            time_context = """
14-DAY WINDOW:
- Medium move expected: 4-10%
- Balance momentum and fundamentals
- Include near-term catalysts
- Moderate confidence range
"""
        elif days_ahead == 21:
            time_context = """
21-DAY WINDOW:
- Larger move possible: 7-15%
- Fundamentals start to matter more
- Include sector and macro factors
- Higher conviction required
"""
        else:
            time_context = """
30-DAY WINDOW:
- Full month projection: 10-25% possible
- Macro and fundamental factors dominate
- Technical setup must support long term trend
- Only high conviction calls
"""

        prompt = f"""
You are the AKUFIN AI Prediction Engine.
You specialize in {portfolio} portfolio trades.
Make a SPECIFIC and UNIQUE price prediction.

═══════════════════════════════════════════
TICKER: {ticker}
CURRENT PRICE: ${current_price:.2f}
ANALYSIS DATE: {datetime.now().strftime('%Y-%m-%d')}
TARGET DATE: {target_date.strftime('%Y-%m-%d')}
PREDICTION WINDOW: {days_ahead} days
PORTFOLIO: {portfolio}
═══════════════════════════════════════════

TECHNICAL INDICATORS:
━━━━━━━━━━━━━━━━━━━━
Trend: {analysis['trend']}
RSI: {analysis['rsi']['value']:.1f} → {analysis['rsi']['signal']}
MACD: {analysis['macd']['signal']}
MACD Histogram: {analysis['macd']['histogram']:.4f}
BB Position: {analysis['bollinger_bands']['position']}
BB Upper: ${analysis['bollinger_bands']['upper']:.2f}
BB Lower: ${analysis['bollinger_bands']['lower']:.2f}
EMA20: ${analysis['moving_averages']['ema_20']:.2f} → Price {'ABOVE ✅' if analysis['moving_averages']['price_above_ema20'] else 'BELOW ❌'}
EMA50: ${analysis['moving_averages']['ema_50']:.2f} → Price {'ABOVE ✅' if analysis['moving_averages']['price_above_ema50'] else 'BELOW ❌'}
EMA200: ${analysis['moving_averages']['ema_200']:.2f} → Price {'ABOVE ✅' if analysis['moving_averages']['price_above_ema200'] else 'BELOW ❌'}
Golden Cross: {'YES ✅' if analysis['moving_averages']['golden_cross'] else 'NO ❌'}
Death Cross: {'YES ⚠️' if analysis['moving_averages']['death_cross'] else 'NO ✅'}
VWAP: ${analysis['vwap']['value']:.2f} → Price {'ABOVE ✅' if analysis['vwap']['price_above_vwap'] else 'BELOW ❌'}
Volume Spike: {'YES - unusual activity' if analysis['volume']['volume_spike'] else 'NO - normal volume'}
Volume Ratio: {analysis['volume']['volume_ratio']:.2f}x 20-day average
ATR: ${analysis['atr']['value']:.2f}
ATR Stop Loss: ${analysis['atr']['stop_loss']:.2f}
ATR Take Profit: ${analysis['atr']['take_profit']:.2f}

{portfolio_context}
{time_context}

IMPORTANT - MAKE YOUR PREDICTION SPECIFIC:
1. predicted_price must NOT be ${current_price:.2f}
2. Your reasoning must mention {ticker} specifically
3. Catalysts must be real and relevant to {ticker}
4. Do NOT copy/repeat previous predictions
5. For SNIPER: be more aggressive on targets
6. For FORTRESS: be more conservative and safe

Output ONLY this JSON with no extra text:
{{
    "predicted_price": 0.00,
    "predicted_direction": "UP",
    "confidence": 0.00,
    "reasoning": "Specific 2-3 sentence reasoning for {ticker} based on current setup",
    "technical_summary": "The 3 most important technical signals for this prediction",
    "catalysts": "Specific real catalysts that could drive {ticker} to target",
    "risk_factors": "Specific risks that could invalidate this {ticker} prediction",
    "conviction_level": "LOW/MEDIUM/HIGH/VERY_HIGH",
    "strategy": "Specific {portfolio} entry strategy with price levels"
}}

JSON RULES:
- predicted_price: realistic number close to ${current_price:.2f}
- confidence: between 0.55 and 0.92 only
- All text fields: specific to {ticker} not generic
- strategy: include exact entry, stop and target prices
"""

        try:
            llm = get_llm_with_fallback(temperature=0.3)
            response = llm.invoke(prompt)
            content = response.content.strip()

            if "```json" in content:
                content = content.split(
                    "```json"
                )[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split(
                    "```"
                )[1].split("```")[0].strip()

            ai_output = json.loads(content)

            # Validate predicted price is different
            pred_price = float(
                ai_output["predicted_price"]
            )
            if pred_price == current_price:
                if ai_output.get(
                    "predicted_direction"
                ) == "UP":
                    pred_price = round(
                        current_price * 1.05, 2
                    )
                else:
                    pred_price = round(
                        current_price * 0.95, 2
                    )

            prediction_data = {
                "ticker": ticker,
                "current_price": current_price,
                "predicted_price": pred_price,
                "predicted_direction": ai_output[
                    "predicted_direction"
                ],
                "confidence": float(
                    ai_output["confidence"]
                ),
                "target_date": target_date,
                "days_to_target": days_ahead,
                "reasoning": ai_output["reasoning"],
                "technical_summary": ai_output[
                    "technical_summary"
                ],
                "catalysts": ai_output["catalysts"],
                "risk_factors": ai_output["risk_factors"],
                "strategy": ai_output.get(
                    "strategy", ""
                ),
                "portfolio": portfolio,
                "status": "ACTIVE"
            }

            saved = self._save_prediction(
                prediction_data
            )

            price_change_pct = round(
                (pred_price - current_price)
                / current_price * 100, 2
            )

            return {
                "id": saved.id if saved else None,
                "ticker": ticker,
                "current_price": current_price,
                "predicted_price": pred_price,
                "predicted_direction": ai_output[
                    "predicted_direction"
                ],
                "confidence": float(
                    ai_output["confidence"]
                ),
                "conviction": ai_output.get(
                    "conviction_level", "MEDIUM"
                ),
                "target_date": target_date.strftime(
                    "%Y-%m-%d"
                ),
                "days_ahead": days_ahead,
                "reasoning": ai_output["reasoning"],
                "technical_summary": ai_output[
                    "technical_summary"
                ],
                "catalysts": ai_output["catalysts"],
                "risk_factors": ai_output["risk_factors"],
                "strategy": ai_output.get(
                    "strategy", ""
                ),
                "portfolio": portfolio,
                "price_change_pct": price_change_pct,
                "created_at": datetime.now().strftime(
                    "%Y-%m-%d %H:%M"
                )
            }

        except json.JSONDecodeError as e:
            logger.error(
                f"AKUFIN JSON parse error {ticker}: {e}"
            )
            return {
                "error": f"AI response parsing failed: {e}"
            }
        except Exception as e:
            logger.error(
                f"AKUFIN prediction error {ticker}: {e}"
            )
            return {"error": str(e)}

    def _save_prediction(self, data: dict):
        """Save prediction to database permanently"""
        session = get_session()
        try:
            pred = Prediction(**data)
            session.add(pred)
            session.commit()
            session.refresh(pred)
            logger.info(
                f"AKUFIN prediction saved: "
                f"{data['ticker']} → "
                f"${data['predicted_price']}"
            )
            return pred
        except Exception as e:
            logger.error(
                f"AKUFIN save error: {e}"
            )
            session.rollback()
            return None
        finally:
            session.close()

    def get_all_predictions(self) -> list:
        """
        Get ALL predictions from database.
        Predictions persist until manually deleted.
        """
        session = get_session()
        try:
            preds = session.query(Prediction).order_by(
                Prediction.created_at.desc()
            ).all()
            return [self._pred_to_dict(p) for p in preds]
        except Exception as e:
            logger.error(
                f"AKUFIN get predictions error: {e}"
            )
            return []
        finally:
            session.close()

    def get_active_predictions(self) -> list:
        """Get only ACTIVE predictions"""
        session = get_session()
        try:
            preds = session.query(Prediction).filter(
                Prediction.status == "ACTIVE"
            ).order_by(
                Prediction.created_at.desc()
            ).all()
            return [self._pred_to_dict(p) for p in preds]
        except Exception as e:
            logger.error(
                f"AKUFIN active predictions error: {e}"
            )
            return []
        finally:
            session.close()

    def delete_prediction(self, pred_id: int) -> bool:
        """
        Manually delete a prediction.
        Only way predictions are removed.
        They do NOT auto-delete.
        """
        session = get_session()
        try:
            pred = session.query(Prediction).filter(
                Prediction.id == pred_id
            ).first()
            if pred:
                session.delete(pred)
                session.commit()
                logger.info(
                    f"AKUFIN prediction deleted: {pred_id}"
                )
                return True
            return False
        except Exception as e:
            logger.error(
                f"AKUFIN delete error: {e}"
            )
            session.rollback()
            return False
        finally:
            session.close()

    def resolve_prediction(
        self,
        pred_id: int,
        actual_price: float
    ) -> dict:
        """
        Mark a prediction as resolved.
        Compare predicted vs actual price.
        Updates accuracy tracking.
        """
        session = get_session()
        try:
            pred = session.query(Prediction).filter(
                Prediction.id == pred_id
            ).first()

            if not pred:
                return {
                    "success": False,
                    "error": "Prediction not found"
                }

            pred.actual_price_at_target = actual_price
            pred.status = "RESOLVED"

            pred_price = pred.predicted_price
            direction = pred.predicted_direction
            start_price = pred.current_price

            if direction == "UP":
                correct = actual_price >= pred_price
            else:
                correct = actual_price <= pred_price

            pred.prediction_correct = correct
            pred.accuracy_pct = round(
                abs(
                    actual_price - pred_price
                ) / pred_price * 100, 2
            )

            session.commit()

            logger.info(
                f"AKUFIN prediction resolved: "
                f"{pred.ticker} | "
                f"Correct: {correct}"
            )

            return {
                "success": True,
                "ticker": pred.ticker,
                "predicted": pred_price,
                "actual": actual_price,
                "correct": correct,
                "accuracy_pct": pred.accuracy_pct
            }

        except Exception as e:
            logger.error(
                f"AKUFIN resolve error: {e}"
            )
            session.rollback()
            return {"success": False, "error": str(e)}
        finally:
            session.close()

    def _pred_to_dict(self, p: Prediction) -> dict:
        """Convert Prediction model to dict"""
        try:
            current_price = (
                self.market_data.get_current_price(
                    p.ticker
                )
            )
        except Exception:
            current_price = p.current_price or 0

        price_change = 0
        if p.current_price and p.current_price > 0:
            price_change = round(
                (current_price - p.current_price)
                / p.current_price * 100, 2
            )

        progress = 0
        if (
            p.predicted_price
            and p.current_price
            and p.current_price > 0
        ):
            total_move = abs(
                p.predicted_price - p.current_price
            )
            current_move = abs(
                current_price - p.current_price
            )
            if total_move > 0:
                progress = min(
                    round(
                        current_move / total_move * 100,
                        1
                    ),
                    100
                )

        return {
            "id": p.id,
            "ticker": p.ticker,
            "current_price_at_prediction": (
                p.current_price or 0
            ),
            "predicted_price": p.predicted_price or 0,
            "current_price_now": current_price,
            "predicted_direction": (
                p.predicted_direction or "UP"
            ),
            "confidence": p.confidence or 0,
            "target_date": (
                p.target_date.strftime("%Y-%m-%d")
                if p.target_date else ""
            ),
            "days_to_target": p.days_to_target or 14,
            "reasoning": p.reasoning or "",
            "technical_summary": (
                p.technical_summary or ""
            ),
            "catalysts": p.catalysts or "",
            "risk_factors": p.risk_factors or "",
            "strategy": p.strategy or "",
            "portfolio": p.portfolio or "SNIPER",
            "status": p.status or "ACTIVE",
            "price_change_so_far_pct": price_change,
            "progress_to_target_pct": progress,
            "prediction_correct": p.prediction_correct,
            "accuracy_pct": p.accuracy_pct,
            "created_at": (
                p.created_at.strftime("%Y-%m-%d %H:%M")
                if p.created_at else ""
            )
        }