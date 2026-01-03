"""
    start_scheduler, stop_scheduler,
    set_notification_callback, run_initial_update
)








# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, LOG_LEVEL, logging.INFO)
)
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)
















async def send_notification(user_id: int, message: str) -> None:
    """Send notification"""
    try:
        await application.bot.send_message(chat_id=user_id, text=message, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Notification failed for {user_id}: {e}")
















async def post_init(app: Application) -> None:
    """Initialize"""
    logger.info("Initializing database...")
    await init_db()
    
    logger.info("Running initial rate update...")
    await run_initial_update()
    
    logger.info("Starting scheduler...")
    set_notification_callback(send_notification)
    start_scheduler(app.bot)
    
    logger.info("Bot ready!")
















async def post_shutdown(app: Application) -> None:
    """Shutdown"""
    logger.info("Stopping scheduler...")
    stop_scheduler()
    
    logger.info("Closing database...")
    await close_db()
    
    logger.info("Shutdown complete!")
















async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors"""
    logger.error(f"Error: {context.error}")
















def main() -> None:
    """Run bot"""
    global application
    
    logger.info("Starting Currency Alert Bot...")
    
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )
    
    # Inline query handler
    application.add_handler(get_inline_handler())
    
    # Start handlers
    for handler in get_start_handlers():
        application.add_handler(handler)
    
    # Time setting conversation
    application.add_handler(get_time_conversation_handler())
    
    # Settings handlers
    for handler in get_settings_handlers():
        application.add_handler(handler)
    
    # Favorites handlers
    for handler in get_favorites_handlers():
        application.add_handler(handler)
    
        # Smart Exchange handlers
    for handler in get_smart_exchange_handlers():
        application.add_handler(handler)

    # Chart handlers
    for handler in get_chart_handlers():
        application.add_handler(handler)
    
    # Analysis handlers
