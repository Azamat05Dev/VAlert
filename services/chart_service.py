"""
Chart Service - With CBU Historical Data Fallback
"""
import logging
import io
from datetime import datetime, timedelta
from typing import Optional
import httpx
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from sqlalchemy import select

from database.db import get_session
from database.models import RateHistory

logger = logging.getLogger(__name__)

plt.style.use('seaborn-v0_8-darkgrid')


async def fetch_cbu_history(currency_code: str, days: int = 7) -> list:
    """Fetch historical rates from CBU archive API"""
    try:
        rates = []
        today = datetime.now()
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for i in range(days):
                date = today - timedelta(days=i)
                date_str = date.strftime("%Y-%m-%d")
                
                url = f"https://cbu.uz/uz/arkhiv-kursov-valyut/json/{currency_code}/{date_str}/"
                
                try:
                    response = await client.get(url)
                    if response.status_code == 200:
                        data = response.json()
                        if data and len(data) > 0:
                            rate_data = data[0]
                            rates.append({
                                "date": date,
                                "rate": float(rate_data.get("Rate", 0)),
                                "nominal": int(rate_data.get("Nominal", 1))
                            })
                except Exception as e:
                    logger.debug(f"CBU fetch error for {date_str}: {e}")
                    continue
        
        # Sort by date ascending
        rates.sort(key=lambda x: x["date"])
        logger.info(f"CBU history: fetched {len(rates)} records for {currency_code}")
        return rates
        
    except Exception as e:
        logger.error(f"CBU history fetch error: {e}")
        return []


async def generate_rate_chart(
    currency_code: str,
    bank_code: str = "cbu",
    days: int = 7
) -> Optional[bytes]:
    """Generate rate history chart - with CBU fallback"""
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Try local history first
        async with get_session() as session:
            result = await session.execute(
                select(RateHistory).where(
                    RateHistory.currency_code == currency_code,
                    RateHistory.bank_code == bank_code,
                    RateHistory.recorded_at >= start_date
                ).order_by(RateHistory.recorded_at)
            )
            history = result.scalars().all()
        
        dates = []
        rates = []
        
        if len(history) >= 2:
            # Use local data
            dates = [h.recorded_at for h in history]
            rates = [h.official_rate or h.buy_rate or 0 for h in history]
            logger.info(f"Using local history: {len(history)} records")
        else:
            # Fallback: fetch from CBU archive
            logger.info(f"Local data insufficient, fetching from CBU archive...")
            cbu_history = await fetch_cbu_history(currency_code, days)
            
            if len(cbu_history) < 2:
                logger.info(f"Not enough data for {currency_code} chart")
                return None
            
            dates = [h["date"] for h in cbu_history]
            rates = [h["rate"] for h in cbu_history]
        
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
    """Generate trend analysis - with CBU fallback"""
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Try local history first
        async with get_session() as session:
            result = await session.execute(
                select(RateHistory).where(
                    RateHistory.currency_code == currency_code,
                    RateHistory.bank_code == "cbu",
                    RateHistory.recorded_at >= start_date
                ).order_by(RateHistory.recorded_at)
            )
            history = result.scalars().all()
        
        rates = []
        
        if len(history) >= 2:
            rates = [h.official_rate or h.buy_rate or 0 for h in history]
        else:
            # Fallback: CBU archive
            cbu_history = await fetch_cbu_history(currency_code, days)
            if len(cbu_history) < 2:
                return {
                    "has_data": False,
                    "message": "⚠️ Tarix ma'lumotlari yetarli emas."
                }
            rates = [h["rate"] for h in cbu_history]
        
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
