"""
Start Command Handler - Simplified
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler


from handlers.common import get_or_create_user, get_user_language, set_user_language
from locales.helpers import t




def get_main_menu_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    """Full main menu"""
    keyboard = [
        [
            InlineKeyboardButton("📊 Kurslar", callback_data="rates"),
            InlineKeyboardButton("🏆 Eng yaxshi", callback_data="best"),
        ],
        [
            InlineKeyboardButton("🔔 Alert", callback_data="new_alert"),
            InlineKeyboardButton("📋 Alertlarim", callback_data="my_alerts"),
        ],
        [
            InlineKeyboardButton("📈 Grafik", callback_data="charts"),
            InlineKeyboardButton("🤖 Tahlil", callback_data="analysis"),
        ],
        [
            InlineKeyboardButton("🧮 Kalkulyator", callback_data="calculator"),
            InlineKeyboardButton("💰 Foyda", callback_data="profit"),
        ],
        [
            InlineKeyboardButton("💼 Portfel", callback_data="portfolio"),
            InlineKeyboardButton("📅 Bugun", callback_data="today"),
        ],
        [
            InlineKeyboardButton("💫 Aqlli almashtirish", callback_data="smart_exchange"),
        ],
        [
            InlineKeyboardButton("⚙️ Sozlamalar", callback_data="settings"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)




async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start"""
    user = update.effective_user
    
    db_user = await get_or_create_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    keyboard = [
        [
            InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="set_lang_uz"),
            InlineKeyboardButton("🇷🇺 Русский", callback_data="set_lang_ru"),
        ]
    ]
    
    await update.message.reply_text(
        t("choose_language", db_user.language),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )



