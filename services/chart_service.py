"""
Chart Service - NO FAKE DATA, Real history only
"""
import logging
import io
from datetime import datetime, timedelta
from typing import Optional
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from sqlalchemy import select

from database.db import get_session
from database.models import RateHistory

logger = logging.getLogger(__name__)

plt.style.use('seaborn-v0_8-darkgrid')


async def generate_rate_chart(
    currency_code: str,
    bank_code: str = "cbu",
    days: int = 7
) -> Optional[bytes]:
    """Generate rate history chart - REAL DATA ONLY"""
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        async with get_session() as session:
            result = await session.execute(
                select(RateHistory).where(
                    RateHistory.currency_code == currency_code,
                    RateHistory.bank_code == bank_code,
                    RateHistory.recorded_at >= start_date
                ).order_by(RateHistory.recorded_at)
            )
            history = result.scalars().all()
        
        if len(history) < 2:
            # Not enough real data - return None (no fake data!)
            logger.info(f"Not enough data for {currency_code} chart")
            return None
        
        # Prepare data
        dates = [h.recorded_at for h in history]
        rates = [h.official_rate or h.buy_rate or 0 for h in history]
        
        # Create chart
        fig, ax = plt.subplots(figsize=(10, 5))
        
        ax.plot(dates, rates, color='#2196F3', linewidth=2, marker='o', markersize=4)
        ax.fill_between(dates, rates, alpha=0.3, color='#2196F3')
        
        ax.set_title(f'{currency_code} Kurs Tarixi ({days} kun)', fontsize=14, fontweight='bold')
        ax.set_xlabel('Sana', fontsize=10)
        ax.set_ylabel("So'm", fontsize=10)
        
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, days // 7)))
        plt.xticks(rotation=45)
        
        min_rate = min(rates)
        max_rate = max(rates)
        min_idx = rates.index(min_rate)
        max_idx = rates.index(max_rate)
        
        ax.annotate(f'Min: {min_rate:,.0f}', xy=(dates[min_idx], min_rate),
                    xytext=(5, -15), textcoords='offset points', fontsize=9,
                    color='red', fontweight='bold')
        ax.annotate(f'Max: {max_rate:,.0f}', xy=(dates[max_idx], max_rate),
                    xytext=(5, 10), textcoords='offset points', fontsize=9,
                    color='green', fontweight='bold')
        
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)
        
        return buf.getvalue()
        
    except Exception as e:
        logger.error(f"Chart generation error: {e}")
        return None


async def generate_trend_analysis(currency_code: str, days: int = 7) -> dict:
    """Generate trend analysis - REAL DATA ONLY"""
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
        
        if len(history) < 2:
            return {
                "has_data": False,
                "message": "⚠️ Tarix ma'lumotlari hali to'planmagan.\nBot ishlagan vaqt davomida ma'lumotlar yig'iladi."
            }
        
        rates = [h.official_rate or h.buy_rate or 0 for h in history]
        
        first_rate = rates[0]
        last_rate = rates[-1]
        change = last_rate - first_rate
        change_pct = (change / first_rate) * 100 if first_rate else 0
        
        min_rate = min(rates)
        max_rate = max(rates)
        avg_rate = sum(rates) / len(rates)
        
        if change_pct > 1:
            trend = "📈 Oshish"
        elif change_pct < -1:
            trend = "📉 Tushish"
        else:
            trend = "➖ Barqaror"
        
        return {
            "has_data": True,
            "currency": currency_code,
            "days": days,
            "first_rate": first_rate,
            "last_rate": last_rate,
            "change": change,
            "change_pct": change_pct,
            "min_rate": min_rate,
            "max_rate": max_rate,
            "avg_rate": avg_rate,
            "trend": trend,
            "data_points": len(rates)
        }
        
    except Exception as e:
        logger.error(f"Trend analysis error: {e}")
        return {"has_data": False, "message": str(e)}
