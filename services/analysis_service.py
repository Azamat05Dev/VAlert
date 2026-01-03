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


def calculate_ema(prices: list[float], period: int) -> Optional[float]:
    """Exponential Moving Average"""
    if len(prices) < period:
        return None
    
    multiplier = 2 / (period + 1)
    ema = sum(prices[:period]) / period  # SMA as starting point
    
    for price in prices[period:]:
        ema = (price - ema) * multiplier + ema
    
    return ema


def calculate_macd(prices: list[float]) -> Optional[dict]:
    """
    MACD (Moving Average Convergence Divergence)
    Standard parameters: EMA 12, EMA 26, Signal 9
    
    Returns:
        macd_line: EMA12 - EMA26
        signal_line: EMA9 of MACD line
        histogram: MACD - Signal
        trend: bullish/bearish based on crossover
    """
    if len(prices) < 35:  # Need enough data for EMA26 + Signal9
        return None
    
    # Calculate EMAs
    ema_12 = []
    ema_26 = []
    
    # Initialize with SMA
    ema_12_val = sum(prices[:12]) / 12
    ema_26_val = sum(prices[:26]) / 26
    
    mult_12 = 2 / 13  # 2 / (12 + 1)
    mult_26 = 2 / 27  # 2 / (26 + 1)
    
    for i, price in enumerate(prices):
        if i < 12:
            ema_12_val = sum(prices[:i+1]) / (i + 1)
        else:
            ema_12_val = (price - ema_12_val) * mult_12 + ema_12_val
        
        if i < 26:
            ema_26_val = sum(prices[:i+1]) / (i + 1)
        else:
            ema_26_val = (price - ema_26_val) * mult_26 + ema_26_val
        
        if i >= 25:  # Start collecting after enough data
            ema_12.append(ema_12_val)
            ema_26.append(ema_26_val)
    
    # Calculate MACD line
    macd_line = [e12 - e26 for e12, e26 in zip(ema_12, ema_26)]
    
    if len(macd_line) < 9:
        return None
    
    # Calculate Signal line (EMA9 of MACD)
    signal_val = sum(macd_line[:9]) / 9
    mult_9 = 2 / 10
    
    signal_line = []
    for i, macd_val in enumerate(macd_line):
        if i < 9:
            signal_val = sum(macd_line[:i+1]) / (i + 1)
        else:
            signal_val = (macd_val - signal_val) * mult_9 + signal_val
        signal_line.append(signal_val)
    
    # Current values
    current_macd = macd_line[-1]
    current_signal = signal_line[-1]
    histogram = current_macd - current_signal
    
    # Trend detection
    if current_macd > current_signal:
        trend = "bullish"
    else:
        trend = "bearish"
    
    # Crossover detection (signal strength)
    prev_macd = macd_line[-2] if len(macd_line) >= 2 else current_macd
    prev_signal = signal_line[-2] if len(signal_line) >= 2 else current_signal
    
    crossover = None
    if prev_macd <= prev_signal and current_macd > current_signal:
        crossover = "bullish_crossover"
    elif prev_macd >= prev_signal and current_macd < current_signal:
        crossover = "bearish_crossover"
    
    return {
        "macd": round(current_macd, 2),
        "signal": round(current_signal, 2),
        "histogram": round(histogram, 2),
        "trend": trend,
        "crossover": crossover
    }


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
        macd = calculate_macd(prices)  # Real MACD calculation
        
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
            "macd": macd,  # Now includes real MACD data
            "prediction": prediction,
            "data_points": len(prices)
        }
        
    except Exception as e:
        logger.error(f"Technical analysis error: {e}")
        return {"has_data": False, "message": str(e)}
