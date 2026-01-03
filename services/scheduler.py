"""
Scheduler Service - Fixed with timezone, user-specific times, and RateHistory
"""
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select

from config import UPDATE_INTERVAL, POPULAR_CURRENCIES, BANKS
from services.rate_manager import update_all_rates, get_rate, get_rates_by_currency
from database.db import get_session
from database.models import User, Alert, RateHistory, SmartExchange

logger = logging.getLogger(__name__)

# Uzbekistan timezone
UZ_TZ = ZoneInfo("Asia/Tashkent")

scheduler = AsyncIOScheduler(timezone=UZ_TZ)
notification_callback = None

# Store previous rates for big change detection
previous_rates = {}


def set_notification_callback(callback):
    """Set notification callback"""
    global notification_callback
    notification_callback = callback


async def update_rates_job():
    """Update rates (called every minute)"""
    await update_all_rates()
    await check_big_changes()
    await check_alerts()


async def save_rate_history():
    """Save current CBU rates to history (called every 15 minutes)"""
    try:
        async with get_session() as session:
            for currency in POPULAR_CURRENCIES[:5]:
                rate = await get_rate("cbu", currency)
                if rate:
                    history = RateHistory(
                        bank_code="cbu",
                        currency_code=currency,
                        official_rate=rate.get("official_rate"),
                        buy_rate=rate.get("buy_rate"),
                        sell_rate=rate.get("sell_rate")
                    )
                    session.add(history)
            await session.commit()
            logger.debug("Rate history saved")
    except Exception as e:
        logger.error(f"Save rate history error: {e}")


async def cleanup_old_history():
    """Delete rate history older than 30 days (runs daily)"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        async with get_session() as session:
            from sqlalchemy import delete
            result = await session.execute(
                delete(RateHistory).where(RateHistory.recorded_at < cutoff_date)
            )
            await session.commit()
            deleted = result.rowcount
            if deleted > 0:
                logger.info(f"Cleaned up {deleted} old history records")
    except Exception as e:
        logger.error(f"History cleanup error: {e}")


async def check_big_changes():
    """Check for >1% changes and notify users"""
    global previous_rates
    
    for currency in POPULAR_CURRENCIES[:5]:
        rate = await get_rate("cbu", currency)
        if not rate:
            continue
        
        current = rate.get("official_rate", 0)
        prev = previous_rates.get(currency)
        
        if prev is not None and prev > 0:
            change_pct = abs((current - prev) / prev) * 100
            
            if change_pct >= 1.0:
                await notify_big_change(currency, prev, current, change_pct)
        
        previous_rates[currency] = current


async def notify_big_change(currency: str, prev: float, current: float, pct: float):
    """Notify users about big change"""
    if not notification_callback:
        return
    
    direction = "📈 oshdi" if current > prev else "📉 tushdi"
    diff = current - prev
    
    message = (
        f"🚨 **Katta o'zgarish!**\n\n"
        f"💱 **{currency}** {direction}\n"
        f"📊 {prev:,.0f} → {current:,.0f} ({diff:+,.0f})\n"
        f"📈 O'zgarish: **{pct:.1f}%**"
    )
    
    async with get_session() as session:
        result = await session.execute(
            select(User).where(User.big_change_notify == True, User.is_active == True)
        )
        users = result.scalars().all()
        
        for user in users:
            try:
                await notification_callback(user.id, message)
            except Exception as e:
                logger.error(f"Failed to notify {user.id}: {e}")


async def check_alerts():
    """Check user alerts including best rate alerts"""
    if not notification_callback:
        return
    
    async with get_session() as session:
        result = await session.execute(
            select(Alert).where(Alert.is_active == True, Alert.is_triggered == False)
        )
        alerts = result.scalars().all()
        
        for alert in alerts:
            try:
                await process_single_alert(alert, session)
            except Exception as e:
                logger.error(f"Alert check error: {e}")


async def process_single_alert(alert, session):
    """Process a single alert, including best rate mode"""
    
    # Handle "best rate" alerts
    if alert.bank_code in ("best_high", "best_low"):
        rates = await get_rates_by_currency(alert.currency_code)
        if not rates:
            return
        
        if alert.bank_code == "best_high":
            # Find highest buy rate
            best = max(rates, key=lambda r: r.get("buy_rate") or r.get("official_rate") or 0)
            current = best.get("buy_rate") or best.get("official_rate") or 0
            bank_name = BANKS.get(best["bank_code"], {}).get("name_uz", best["bank_code"])
        else:
            # Find lowest sell rate
            best = min(rates, key=lambda r: r.get("sell_rate") or r.get("official_rate") or float('inf'))
            current = best.get("sell_rate") or best.get("official_rate") or 0
            bank_name = BANKS.get(best["bank_code"], {}).get("name_uz", best["bank_code"])
    else:
        # Normal bank alert
        rate = await get_rate(alert.bank_code, alert.currency_code)
        if not rate:
            return
        
        if alert.rate_type == "buy":
            current = rate.get("buy_rate") or rate.get("official_rate") or 0
        else:
            current = rate.get("sell_rate") or rate.get("official_rate") or 0
        
        bank_name = BANKS.get(alert.bank_code, {}).get("name_uz", alert.bank_code)
    
    # Check trigger condition
    triggered = False
    if alert.direction == "above" and current >= alert.threshold:
        triggered = True
    elif alert.direction == "below" and current <= alert.threshold:
        triggered = True
    
    if triggered:
        rate_text = "Sotib olish" if alert.rate_type == "buy" else "Sotish"
        dir_text = "oshdi" if alert.direction == "above" else "tushdi"
        
        message = (
            f"🔔 **Alert!**\n\n"
            f"💱 **{alert.currency_code}** {dir_text}!\n"
            f"🏦 {bank_name}\n"
            f"📊 {rate_text}: **{current:,.0f}** so'm\n"
            f"🎯 Sizning chegarangiz: {alert.threshold:,.0f}"
        )
        
        try:
            await notification_callback(alert.user_id, message)
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
        
        # Update alert
        alert.is_triggered = True
        alert.last_triggered_at = datetime.utcnow()
        
        # If repeating, reset
        if alert.is_repeating:
            alert.is_triggered = False
        
        await session.commit()


async def daily_notification_check():
    """Check every minute if any user should receive daily notification"""
    if not notification_callback:
        return
    
    now = datetime.now(UZ_TZ)
    current_time = now.strftime("%H:%M")
    today = now.date()
    
    # Also check previous minute to avoid missing due to scheduler offset
    prev_minute = (now - timedelta(minutes=1)).strftime("%H:%M")
    
    async with get_session() as session:
        # Match current minute OR previous minute (2-minute window)
        result = await session.execute(
            select(User).where(
                User.daily_notify == True,
                User.is_active == True,
                (User.daily_notify_time == current_time) | (User.daily_notify_time == prev_minute)
            )
        )
        users = result.scalars().all()
        
        for user in users:
            # Check if already sent today
            if user.last_daily_sent and user.last_daily_sent.date() == today:
                continue
            
            # Build message
            message = f"📅 **Bugungi kurslar** ({current_time})\n🏛️ Markaziy Bank\n\n"
            
            for currency in POPULAR_CURRENCIES[:5]:
                rate = await get_rate("cbu", currency)
                if rate:
                    official = rate.get("official_rate", 0)
                    diff = rate.get("diff", 0)
                    
                    if diff > 0:
                        change = f"📈+{diff:.0f}"
                    elif diff < 0:
                        change = f"📉{diff:.0f}"
                    else:
                        change = "➖"
                    
                    message += f"💱 **{currency}**: {official:,.0f} {change}\n"
            
            try:
                await notification_callback(user.id, message)
                user.last_daily_sent = now
                await session.commit()
            except Exception as e:
                logger.error(f"Daily notify failed for {user.id}: {e}")


async def weekly_report_job():
    """Send weekly report on Monday at 10:00"""
    if not notification_callback:
        return
    
    async with get_session() as session:
        result = await session.execute(
            select(User).where(User.weekly_report == True, User.is_active == True)
        )
        users = result.scalars().all()
    
    message = "📊 **Haftalik hisobot**\n🏛️ Markaziy Bank\n\n"
    
    for currency in POPULAR_CURRENCIES[:5]:
        rate = await get_rate("cbu", currency)
        if rate:
            official = rate.get("official_rate", 0)
            message += f"💱 **{currency}**: {official:,.0f} so'm\n"
    
    message += "\n_Yaxshi hafta tilayman!_ 🎯"
    
    for user in users:
        try:
            await notification_callback(user.id, message)
        except Exception as e:
            logger.error(f"Weekly report failed for {user.id}: {e}")


async def check_smart_exchanges():
    """Check smart exchange alerts every 5 minutes"""
    if not notification_callback:
        return
    
    from datetime import timedelta
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    now = datetime.now(UZ_TZ)
    five_minutes_ago = now - timedelta(minutes=5)
    
    async with get_session() as session:
        result = await session.execute(
            select(SmartExchange).where(
                SmartExchange.is_active == True,
                SmartExchange.is_accepted == False
            )
        )
        exchanges = result.scalars().all()
        
        for exchange in exchanges:
            try:
                # Skip if notified less than 5 minutes ago
                if exchange.last_notified_at:
                    last_utc = exchange.last_notified_at.replace(tzinfo=None)
                    if (datetime.utcnow() - last_utc).total_seconds() < 300:
                        continue
                
                # Get current best buy rate for this currency
                rates = await get_rates_by_currency(exchange.currency_code)
                if not rates:
                    continue
                
                best_rate = 0
                best_bank = ""
                best_bank_code = ""
                
                for rate in rates:
                    buy = rate.get("buy_rate") or 0
                    if buy > best_rate:
                        best_rate = buy
                        best_bank = rate.get("bank_name", rate.get("bank_code", ""))
                        best_bank_code = rate.get("bank_code", "")
                
                # Check if rate meets the target
                target_rate = exchange.initial_best_rate + exchange.target_increase
                
                if best_rate >= target_rate:
                    increase = best_rate - exchange.initial_best_rate
                    total_value = exchange.amount * best_rate
                    
                    message = (
                        f"🔔 **Eng yaxshi vaqt!**\n\n"
                        f"💰 Sizda: **{exchange.amount:,.0f} {exchange.currency_code}**\n"
                        f"🏦 **{best_bank}** sotib olish kursi: **{best_rate:,.0f}** so'm\n"
                        f"📈 **+{increase:.0f}** so'm ko'tarildi sizning chegarangizdan!\n\n"
                        f"💵 Jami: **{total_value:,.0f}** so'm olishingiz mumkin\n\n"
                        f"_Hozir almashtirishni tavsiya qilamiz!_"
                    )
                    
                    # Send with inline buttons
                    try:
                        from telegram import Bot
                        # We need to send with keyboard, using raw API
                        keyboard_json = {
                            "inline_keyboard": [
                                [
                                    {"text": "✅ Qabul qilish", "callback_data": f"accept_smart_{exchange.id}"},
                                    {"text": "⏰ Keyinroq", "callback_data": f"skip_smart_{exchange.id}"}
                                ]
                            ]
                        }
                        import json
                        # For now, just send plain message
                        await notification_callback(
                            exchange.user_id, 
                            message + f"\n\n[Qabul qilish uchun /start bosing]"
                        )
                    except Exception as e:
                        logger.error(f"Smart exchange notification error: {e}")
                    
                    # Update last notified time
                    exchange.last_notified_at = datetime.utcnow()
                    await session.commit()
                    
            except Exception as e:
                logger.error(f"Smart exchange check error for {exchange.id}: {e}")


async def run_initial_update():
    """Run initial update"""
    await update_all_rates()


def start_scheduler():
    """Start scheduler with all jobs"""
    # Rate update every minute
    scheduler.add_job(
        update_rates_job,
        IntervalTrigger(seconds=UPDATE_INTERVAL),
        id="update_rates",
        replace_existing=True
    )
    
    # Daily notification check every minute
    scheduler.add_job(
        daily_notification_check,
        IntervalTrigger(minutes=1),
        id="daily_check",
        replace_existing=True
    )
    
    # Weekly report on Monday at 10:00 Tashkent time
    scheduler.add_job(
        weekly_report_job,
        CronTrigger(day_of_week="mon", hour=10, minute=0, timezone=UZ_TZ),
        id="weekly_report",
        replace_existing=True
    )
    
    # Smart exchange check every 5 minutes
    scheduler.add_job(
        check_smart_exchanges,
        IntervalTrigger(minutes=5),
        id="smart_exchange_check",
        replace_existing=True
    )
    
    # Rate history save every 15 minutes (not every minute to reduce DB size)
    scheduler.add_job(
        save_rate_history,
        IntervalTrigger(minutes=15),
        id="save_history",
        replace_existing=True
    )
    
    # Cleanup old history daily at 3:00 AM (30-day retention)
    scheduler.add_job(
        cleanup_old_history,
        CronTrigger(hour=3, minute=0, timezone=UZ_TZ),
        id="cleanup_history",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Scheduler started with all jobs")


def stop_scheduler():
    """Stop scheduler"""
    scheduler.shutdown(wait=False)
