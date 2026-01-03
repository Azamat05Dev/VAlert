"""
Currency Alert Bot - Main Entry Point (All Features)
"""
import logging
from telegram import Update
from telegram.ext import Application, ContextTypes

from config import BOT_TOKEN, LOG_LEVEL
from database.db import init_db, close_db
from handlers.start import get_start_handlers
from handlers.rates import get_rates_handlers
from handlers.alerts import get_alert_conversation_handler, get_alerts_handlers
from handlers.tools import get_calc_conversation_handler, get_tools_handlers
from handlers.portfolio import (
    get_portfolio_conversation_handler, 
    get_profit_conversation_handler,
    get_portfolio_handlers
)
from handlers.settings import get_settings_handlers, get_time_conversation_handler
from handlers.favorites import get_favorites_handlers
from handlers.charts import get_chart_handlers
from handlers.inline import get_inline_handler
from handlers.admin import get_admin_handlers, get_broadcast_conversation_handler
from handlers.analysis import get_analysis_handlers
from services.scheduler import (
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
    start_scheduler()
    
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
    
    # Chart handlers
    for handler in get_chart_handlers():
        application.add_handler(handler)
    
    # Analysis handlers
    for handler in get_analysis_handlers():
        application.add_handler(handler)
    
    # Rates handlers
    for handler in get_rates_handlers():
        application.add_handler(handler)
    
    # Alerts
    application.add_handler(get_alert_conversation_handler())
    for handler in get_alerts_handlers():
        application.add_handler(handler)
    
    # Calculator
    application.add_handler(get_calc_conversation_handler())
    
    # Tools
    for handler in get_tools_handlers():
        application.add_handler(handler)
    
    # Portfolio
    application.add_handler(get_portfolio_conversation_handler())
    application.add_handler(get_profit_conversation_handler())
    for handler in get_portfolio_handlers():
        application.add_handler(handler)
    
    # Admin broadcast conversation (before callback handlers)
    application.add_handler(get_broadcast_conversation_handler())
    
    # Admin
    for handler in get_admin_handlers():
        application.add_handler(handler)
    
    # Error
    application.add_error_handler(error_handler)
    
    logger.info("Bot starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
