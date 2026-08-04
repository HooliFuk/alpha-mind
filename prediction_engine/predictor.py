# prediction_engine/predictor.py
# AKUFIN - Intelligence for Wealth Accrual
# AI Prediction Engine
import sys
import os
sys.path.append(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)

import json
from datetime import datetime, timedelta
from tools.market_data import MarketDataFetcher
from tools.indicators import TechnicalIndicators
from tools.llm_router import get_llm_with_fallback
from database.connection import get_session, init_db
from database.models import Prediction
from monitoring.logger import get_logger

logger = get_logger(__name__)


class PredictionEngine:
    """
    AKUFIN AI Prediction Engine.
    Portfolio-aware and time-window-aware.
    Predictions persist until manually deleted.
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
        """Generate AKUFIN AI prediction"""
        logger.info(
            f"AKUFIN prediction: "
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

        # Portfolio context
        if portfolio == "SNIPER":
            portfolio_context = """
SNIPER PORTFOLIO RULES:
- SHORT TERM aggressive trade
- Target 3-8% price move
- Focus on momentum and breakouts
- Tight stop loss (1-2x ATR)
- Hold time: hours to 3 days
"""
        else:
            portfolio_context = """
FORTRESS PORTFOLIO RULES:
- LONG TERM safe investment
- Target 10-25% price move
- Focus on trend and fundamentals
- Wider stop loss (3-4x ATR)
- Hold time: weeks to months
"""

        # Time window context
        time_rules = {
            7: "7 DAYS: Small move 2-5%. Immediate momentum only.",
            14: "14 DAYS: Medium move 4-10%. Balance momentum and fundamentals.",
            21: "21 DAYS: Larger move 7-15%. Fundamentals matter more.",
            30: "30 DAYS: Full month 10-25%. Macro and fundamentals dominate."
        }
        time_context = time_rules.get(
            days_ahead,
            f"{days_ahead} DAYS: Adjust target proportionally."
        )

        prompt = f"""
You are the AKUFIN AI Prediction Engine.
Portfolio type: {portfolio}
Make a SPECIFIC price prediction for {ticker}.

TICKER: {ticker}
CURRENT PRICE: ${current_price:.2f}
DATE: {datetime.now().strftime('%Y-%m-%d')}
TARGET DATE: {target_date.strftime('%Y-%m-%d')}
WINDOW: {days_ahead} days
PORTFOLIO: {portfolio}

INDICATORS:
Trend: {analysis['trend']}
RSI: {analysis['rsi']['value']:.1f} ({analysis['rsi']['signal']})
MACD: {analysis['macd']['signal']}
Histogram: {analysis['macd']['histogram']:.4f}
BB Position: {analysis['bollinger_bands']['position']}
BB Upper: ${analysis['bollinger_bands']['upper']:.2f}
BB Lower: ${analysis['bollinger_bands']['lower']:.2f}
EMA20: ${analysis['moving_averages']['ema_20']:.2f} ({'ABOVE' if analysis['moving_averages']['price_above_ema20'] else 'BELOW'})
EMA50: ${analysis['moving_averages']['ema_50']:.2f} ({'ABOVE' if analysis['moving_averages']['price_above_ema50'] else 'BELOW'})
EMA200: ${analysis['moving_averages']['ema_200']:.2f} ({'ABOVE' if analysis['moving_averages']['price_above_ema200'] else 'BELOW'})
Golden Cross: {'YES' if analysis['moving_averages']['golden_cross'] else 'NO'}
VWAP: ${analysis['vwap']['value']:.2f} ({'ABOVE' if analysis['vwap']['price_above_vwap'] else 'BELOW'})
Volume Spike: {'YES' if analysis['volume']['volume_spike'] else 'NO'}
Volume Ratio: {analysis['volume']['volume_ratio']:.2f}x
ATR: ${analysis['atr']['value']:.2f}

{portfolio_context}
TIME RULE: {time_context}

RULES:
- predicted_price must NOT equal ${current_price:.2f}
- reasoning must mention {ticker} specifically
- catalysts must be real and relevant
- confidence between 0.55 and 0.92
- strategy must include exact price levels

Output ONLY valid JSON:
{{
    "predicted_price": 0.00,
    "predicted_direction": "UP",
    "confidence": 0.00,
    "reasoning": "Specific reasoning for {ticker}",
    "technical_summary": "Top 3 technical signals",
    "catalysts": "Real catalysts for {ticker}",
    "risk_factors": "Specific risks for {ticker}",
    "conviction_level": "LOW/MEDIUM/HIGH/VERY_HIGH",
    "strategy": "Entry strategy with exact prices"
}}
"""

        try:
            llm = get_llm_with_fallback(
                temperature=0.3
            )
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

            pred_price = float(
                ai_output["predicted_price"]
            )

            # Ensure price is different
            if pred_price == current_price:
                direction = ai_output.get(
                    "predicted_direction", "UP"
                )
                if direction == "UP":
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
                "risk_factors": ai_output[
                    "risk_factors"
                ],
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
                "risk_factors": ai_output[
                    "risk_factors"
                ],
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
                f"AKUFIN JSON error {ticker}: {e}"
            )
            return {
                "error": f"AI parsing failed: {e}"
            }
        except Exception as e:
            logger.error(
                f"AKUFIN prediction error: {e}"
            )
            return {"error": str(e)}

    def _save_prediction(self, data: dict):
        """Save prediction to Supabase"""
        session = get_session()
        try:
            pred = Prediction(**data)
            session.add(pred)
            session.commit()
            session.refresh(pred)
            logger.info(
                f"AKUFIN saved: {data['ticker']} "
                f"→ ${data['predicted_price']}"
            )
            return pred
        except Exception as e:
            logger.error(f"AKUFIN save error: {e}")
            session.rollback()
            return None
        finally:
            session.close()

    def get_all_predictions(self) -> list:
        """Get ALL predictions - never auto-deleted"""
        session = get_session()
        try:
            preds = session.query(
                Prediction
            ).order_by(
                Prediction.created_at.desc()
            ).all()
            return [
                self._pred_to_dict(p) for p in preds
            ]
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
            preds = session.query(
                Prediction
            ).filter(
                Prediction.status == "ACTIVE"
            ).order_by(
                Prediction.created_at.desc()
            ).all()
            return [
                self._pred_to_dict(p) for p in preds
            ]
        except Exception as e:
            logger.error(
                f"AKUFIN active preds error: {e}"
            )
            return []
        finally:
            session.close()

    def delete_prediction(
        self, pred_id: int
    ) -> bool:
        """
        Manually delete a prediction.
        Only way to remove predictions.
        They do NOT auto-delete.
        """
        session = get_session()
        try:
            pred = session.query(
                Prediction
            ).filter(
                Prediction.id == pred_id
            ).first()
            if pred:
                session.delete(pred)
                session.commit()
                logger.info(
                    f"AKUFIN prediction deleted: "
                    f"{pred_id}"
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
        """Mark prediction resolved and track accuracy"""
        session = get_session()
        try:
            pred = session.query(
                Prediction
            ).filter(
                Prediction.id == pred_id
            ).first()

            if not pred:
                return {
                    "success": False,
                    "error": "Not found"
                }

            pred.actual_price_at_target = actual_price
            pred.status = "RESOLVED"

            direction = pred.predicted_direction
            pred_price = pred.predicted_price

            correct = (
                actual_price >= pred_price
                if direction == "UP"
                else actual_price <= pred_price
            )

            pred.prediction_correct = correct
            pred.accuracy_pct = round(
                abs(actual_price - pred_price)
                / pred_price * 100, 2
            )

            session.commit()
            logger.info(
                f"AKUFIN resolved: {pred.ticker} "
                f"| Correct: {correct}"
            )

            return {
                "success": True,
                "ticker": pred.ticker,
                "predicted": pred_price,
                "actual": actual_price,
                "correct": correct
            }

        except Exception as e:
            logger.error(
                f"AKUFIN resolve error: {e}"
            )
            session.rollback()
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            session.close()

    def _pred_to_dict(self, p: Prediction) -> dict:
        """Convert Prediction model to dictionary"""
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
            "prediction_correct": (
                p.prediction_correct
            ),
            "accuracy_pct": p.accuracy_pct,
            "created_at": (
                p.created_at.strftime(
                    "%Y-%m-%d %H:%M"
                )
                if p.created_at else ""
            )
        }