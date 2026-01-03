"""
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




async def run_initial_update():
    """Run initial update"""
    await update_all_rates()




def start_scheduler(bot):
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
    
        # Check smart exchanges every 5 minutes
    scheduler.add_job(
        check_smart_exchanges,
        IntervalTrigger(minutes=5),
        args=[bot],
        id="smart_exchanges",
        replace_existing=True
    )

    # Weekly report on Monday at 10:00 Tashkent time
    scheduler.add_job(
        weekly_report_job,
        CronTrigger(day_of_week="mon", hour=10, minute=0, timezone=UZ_TZ),
        id="weekly_report",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Scheduler started with all jobs")




def stop_scheduler():
    """Stop scheduler"""
    scheduler.shutdown(wait=False)

