# prediction_engine/predictor.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from datetime import datetime, timedelta
from tools.market_data import MarketDataFetcher
from tools.indicators import TechnicalIndicators
from tools.llm_router import get_llm_with_fallback
from database.connection import get_session, init_db
from database.models import Base
from monitoring.logger import get_logger
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.sql import func

logger = get_logger(__name__)


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
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
    portfolio = Column(String(20))
    status = Column(String(20), default="ACTIVE")
    actual_price_at_target = Column(Float, nullable=True)
    prediction_correct = Column(Boolean, nullable=True)
    accuracy_pct = Column(Float, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class PredictionEngine:
    """
    Core AI prediction generator.
    Makes specific dated price predictions.
    Every prediction is logged and tracked.
    This is the VC demo feature.
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
        """Generate AI prediction for a ticker"""
        logger.info(f"Generating prediction for {ticker}")

        df = self.market_data.get_historical_bars(ticker, period="6mo")
        if df.empty:
            return {"error": f"No data for {ticker}"}

        analysis = self.indicators.get_full_analysis(df, ticker)
        if "error" in analysis:
            return {"error": analysis["error"]}

        current_price = analysis["current_price"]
        target_date = datetime.now() + timedelta(days=days_ahead)

        prompt = f"""
        You are an expert market analyst and quantitative trader.
        Analyze these technical indicators and make a specific price prediction.

        TICKER: {ticker}
        CURRENT PRICE: ${current_price}
        ANALYSIS DATE: {datetime.now().strftime('%Y-%m-%d')}
        PREDICTION TARGET DATE: {target_date.strftime('%Y-%m-%d')} ({days_ahead} days)

        TECHNICAL DATA:
        - Trend: {analysis['trend']}
        - RSI: {analysis['rsi']['value']} ({analysis['rsi']['signal']})
        - MACD Signal: {analysis['macd']['signal']}
        - Bollinger Bands Position: {analysis['bollinger_bands']['position']}
        - Price vs EMA20: {'ABOVE' if analysis['moving_averages']['price_above_ema20'] else 'BELOW'}
        - Price vs EMA50: {'ABOVE' if analysis['moving_averages']['price_above_ema50'] else 'BELOW'}
        - Price vs EMA200: {'ABOVE' if analysis['moving_averages']['price_above_ema200'] else 'BELOW'}
        - Golden Cross Active: {analysis['moving_averages']['golden_cross']}
        - Volume Spike: {analysis['volume']['volume_spike']}
        - Volume Ratio: {analysis['volume']['volume_ratio']}x average
        - ATR Value: {analysis['atr']['value']}
        - VWAP: {analysis['vwap']['value']}
        - Price Above VWAP: {analysis['vwap']['price_above_vwap']}

        PORTFOLIO TYPE: {portfolio}
        {'Focus on momentum, leverage opportunities and short term price targets.' if portfolio == 'SNIPER' else 'Focus on fundamental value, safety and long term growth potential.'}

        Respond ONLY in this exact JSON format with no other text:
        {{
            "predicted_price": 0.00,
            "predicted_direction": "UP",
            "confidence": 0.00,
            "reasoning": "Your detailed reasoning here in 2-3 sentences",
            "technical_summary": "Key technical factors driving this prediction",
            "catalysts": "Key events or factors that could push price to target",
            "risk_factors": "Key risks that could invalidate this prediction",
            "conviction_level": "LOW/MEDIUM/HIGH/VERY_HIGH"
        }}

        Important rules:
        - predicted_price must be a specific number
        - confidence must be between 0.50 and 0.95
        - Be honest. If signals are mixed say confidence 0.50-0.60
        - Only say HIGH if at least 3 indicators agree strongly
        """

        try:
            llm = get_llm_with_fallback(temperature=0.2)
            response = llm.invoke(prompt)
            content = response.content.strip()

            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            ai_output = json.loads(content)

            prediction_data = {
                "ticker": ticker,
                "current_price": current_price,
                "predicted_price": float(ai_output["predicted_price"]),
                "predicted_direction": ai_output["predicted_direction"],
                "confidence": float(ai_output["confidence"]),
                "target_date": target_date,
                "days_to_target": days_ahead,
                "reasoning": ai_output["reasoning"],
                "technical_summary": ai_output["technical_summary"],
                "catalysts": ai_output["catalysts"],
                "risk_factors": ai_output["risk_factors"],
                "portfolio": portfolio,
                "status": "ACTIVE"
            }

            saved = self._save_prediction(prediction_data)

            return {
                "id": saved.id if saved else None,
                "ticker": ticker,
                "current_price": current_price,
                "predicted_price": float(ai_output["predicted_price"]),
                "predicted_direction": ai_output["predicted_direction"],
                "confidence": float(ai_output["confidence"]),
                "conviction": ai_output.get("conviction_level", "MEDIUM"),
                "target_date": target_date.strftime("%Y-%m-%d"),
                "days_ahead": days_ahead,
                "reasoning": ai_output["reasoning"],
                "technical_summary": ai_output["technical_summary"],
                "catalysts": ai_output["catalysts"],
                "risk_factors": ai_output["risk_factors"],
                "portfolio": portfolio,
                "price_change_pct": round(
                    (float(ai_output["predicted_price"]) - current_price)
                    / current_price * 100, 2
                ),
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
            }

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error for {ticker}: {e}")
            return {"error": f"AI response parsing failed: {e}"}
        except Exception as e:
            logger.error(f"Prediction error for {ticker}: {e}")
            return {"error": str(e)}

    def _save_prediction(self, data: dict):
        """Save prediction to database"""
        session = get_session()
        try:
            pred = Prediction(**data)
            session.add(pred)
            session.commit()
            session.refresh(pred)
            logger.info(
                f"Prediction saved: {data['ticker']} → "
                f"${data['predicted_price']}"
            )
            return pred
        except Exception as e:
            logger.error(f"Failed to save prediction: {e}")
            session.rollback()
            return None
        finally:
            session.close()

    def get_all_predictions(self) -> list:
        """Get all predictions from database"""
        session = get_session()
        try:
            preds = session.query(Prediction).order_by(
                Prediction.created_at.desc()
            ).all()
            return [self._pred_to_dict(p) for p in preds]
        finally:
            session.close()

    def get_active_predictions(self) -> list:
        """Get only active predictions"""
        session = get_session()
        try:
            preds = session.query(Prediction).filter(
                Prediction.status == "ACTIVE"
            ).order_by(Prediction.created_at.desc()).all()
            return [self._pred_to_dict(p) for p in preds]
        finally:
            session.close()

    def _pred_to_dict(self, p: Prediction) -> dict:
        """Convert Prediction model to dictionary"""
        try:
            current_price = self.market_data.get_current_price(p.ticker)
        except:
            current_price = p.current_price

        price_change = round(
            (current_price - p.current_price)
            / p.current_price * 100, 2
        ) if p.current_price and p.current_price > 0 else 0

        progress = 0
        if p.predicted_price and p.current_price and p.current_price > 0:
            total_move = abs(p.predicted_price - p.current_price)
            current_move = abs(current_price - p.current_price)
            progress = min(
                round(current_move / total_move * 100, 1)
                if total_move > 0 else 0, 100
            )

        return {
            "id": p.id,
            "ticker": p.ticker,
            "current_price_at_prediction": p.current_price or 0,
            "predicted_price": p.predicted_price or 0,
            "current_price_now": current_price,
            "predicted_direction": p.predicted_direction or "UP",
            "confidence": p.confidence or 0,
            "target_date": p.target_date.strftime("%Y-%m-%d") if p.target_date else "",
            "days_to_target": p.days_to_target or 14,
            "reasoning": p.reasoning or "",
            "technical_summary": p.technical_summary or "",
            "catalysts": p.catalysts or "",
            "risk_factors": p.risk_factors or "",
            "portfolio": p.portfolio or "SNIPER",
            "status": p.status or "ACTIVE",
            "price_change_so_far_pct": price_change,
            "progress_to_target_pct": progress,
            "prediction_correct": p.prediction_correct,
            "created_at": p.created_at.strftime(
                "%Y-%m-%d %H:%M"
            ) if p.created_at else ""
        }