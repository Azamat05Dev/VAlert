"""
Analysis Service - REAL DATA ONLY, NO FAKE
"""
import logging
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import select

from database.db import get_session
from database.models import RateHistory

logger = logging.getLogger(__name__)


def calculate_sma(prices: list[float], period: int) -> Optional[float]:
    """Simple Moving Average"""
    if len(prices) < period:
        return None
    return sum(prices[-period:]) / period


def calculate_rsi(prices: list[float], period: int = 14) -> Optional[float]:
    """
    Relative Strength Index (RSI)
    RSI > 70 = overbought (sotish vaqti)
    RSI < 30 = oversold (sotib olish vaqti)
    """
    if len(prices) < period + 1:
        return None
    
    gains = []
    losses = []
    
    for i in range(1, len(prices)):
        change = prices[i] - prices[i-1]
        if change >= 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))
    
    if len(gains) < period:
        return None
    
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    
    if avg_loss == 0:
        return 100
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def predict_trend(prices: list[float]) -> dict:
    """Trend prediction based on real indicators"""
    if len(prices) < 7:
        return {
            "prediction": "unknown",
            "confidence": 0,
            "message": "⚠️ Ma'lumot yetarli emas"
        }
    
    rsi = calculate_rsi(prices) if len(prices) >= 15 else None
    sma_7 = calculate_sma(prices, 7)
    current_price = prices[-1]
    
    bullish_score = 0
    bearish_score = 0
    
    if rsi:
        if rsi < 30:
            bullish_score += 2
        elif rsi > 70:
            bearish_score += 2
        elif rsi < 50:
            bullish_score += 1
        else:
            bearish_score += 1
    
    if sma_7:
        if current_price > sma_7:
            bullish_score += 1
        else:
            bearish_score += 1
    
    if len(prices) >= 3:
        recent_change = prices[-1] - prices[-3]
        if recent_change > 0:
            bullish_score += 1
        else:
            bearish_score += 1
    
    total_score = bullish_score + bearish_score
    if total_score == 0:
        confidence = 0
        prediction = "neutral"
    else:
        if bullish_score > bearish_score:
            prediction = "bullish"
            confidence = (bullish_score / total_score) * 100
        elif bearish_score > bullish_score:
            prediction = "bearish"
            confidence = (bearish_score / total_score) * 100
        else:
            prediction = "neutral"
            confidence = 50
    
    if prediction == "bullish":
        message = "📈 Kurs ko'tarilishi kutilmoqda"
    elif prediction == "bearish":
        message = "📉 Kurs tushishi kutilmoqda"
    else:
        message = "➖ Kurs barqaror qolishi mumkin"
    
    return {
        "prediction": prediction,
        "confidence": round(confidence),
        "message": message,
        "rsi": round(rsi) if rsi else None,
        "sma_7": round(sma_7) if sma_7 else None
    }


async def get_technical_analysis(currency_code: str, days: int = 30) -> dict:
    """Get technical analysis - REAL DATA ONLY"""
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        async with get_session() as session:
            result = await session.execute(
                select(RateHistory).where(
                    RateHistory.currency_code == currency_code,
                    RateHistory.bank_code == "cbu",
                    RateHistory.recorded_at >= start_date
                ).order_by(RateHistory.recorded_at)
            )
            history = result.scalars().all()
        
        if len(history) < 7:
            return {
                "currency": currency_code,
                "has_data": False,
                "message": "⚠️ Tarix ma'lumotlari hali to'planmagan.\nBot ishlagan vaqt davomida ma'lumotlar yig'iladi.",
                "data_points": len(history)
            }
        
        prices = [h.official_rate or h.buy_rate or 0 for h in history]
        
        rsi = calculate_rsi(prices)
        sma_7 = calculate_sma(prices, 7)
        sma_14 = calculate_sma(prices, 14) if len(prices) >= 14 else None
        sma_30 = calculate_sma(prices, 30) if len(prices) >= 30 else None
        
        prediction = predict_trend(prices)
        
        current = prices[-1]
        prev = prices[-2] if len(prices) >= 2 else current
        change = current - prev
        change_pct = (change / prev * 100) if prev else 0
        
        return {
            "currency": currency_code,
            "has_data": True,
            "current_price": current,
            "change": change,
            "change_pct": change_pct,
            "rsi": round(rsi) if rsi else None,
            "rsi_signal": "📈 Oshadi" if rsi and rsi < 30 else "📉 Tushadi" if rsi and rsi > 70 else "➖ Neytral",
            "sma_7": round(sma_7) if sma_7 else None,
            "sma_14": round(sma_14) if sma_14 else None,
            "sma_30": round(sma_30) if sma_30 else None,
            "prediction": prediction,
            "data_points": len(prices)
        }
        
    except Exception as e:
        logger.error(f"Technical analysis error: {e}")
        return {"has_data": False, "message": str(e)}
