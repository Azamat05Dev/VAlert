"""
Start Command Handler - Simplified
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

from handlers.common import get_or_create_user, get_user_language, set_user_language
from locales.helpers import t

# WebApp URL (update after Vercel deployment)
WEBAPP_URL = "https://valert-webapp.vercel.app"


def get_main_menu_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    """Full main menu with WebApp"""
    keyboard = [
        # WebApp Button (Premium Feature)
        [
            InlineKeyboardButton(
                "📱 Mini App", 
                web_app=WebAppInfo(url=WEBAPP_URL)
            ),
        ],
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


async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Language selection"""
    query = update.callback_query
    await query.answer()
    
    lang = query.data.replace("set_lang_", "")
    await set_user_language(update.effective_user.id, lang)
    
    await query.edit_message_text(
        t("welcome", lang) + "\n\n" + t("main_menu", lang),
        reply_markup=get_main_menu_keyboard(lang)
    )


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Main menu"""
    query = update.callback_query
    await query.answer()
    
    lang = await get_user_language(update.effective_user.id)
    
    await query.edit_message_text(
        t("main_menu", lang),
        reply_markup=get_main_menu_keyboard(lang)
    )


async def language_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Language menu"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [
            InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="set_lang_uz"),
            InlineKeyboardButton("🇷🇺 Русский", callback_data="set_lang_ru"),
        ],
        [InlineKeyboardButton("⬅️ Orqaga", callback_data="settings")]
    ]
    
    await query.edit_message_text(
        "🌐 Tilni tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def today_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Today's rates"""
    query = update.callback_query
    await query.answer()
    
    from services.rate_manager import get_rate
    from config import POPULAR_CURRENCIES
    
    lang = await get_user_language(update.effective_user.id)
    
    message = "📅 **Bugungi kurslar**\n🏛️ Markaziy Bank\n\n"
    
    for cur in POPULAR_CURRENCIES[:5]:
        rate = await get_rate("cbu", cur)
        if rate:
            official = rate.get("official_rate", 0)
            diff = rate.get("diff", 0)
            
            if diff > 0:
                change = f"📈+{diff:.0f}"
            elif diff < 0:
                change = f"📉{diff:.0f}"
            else:
                change = "➖"
            
            message += f"💱 **{cur}**: {official:,.0f} {change}\n"
    
    keyboard = [[InlineKeyboardButton("⬅️ Orqaga", callback_data="main_menu")]]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help - show user guide"""
    help_text = """
📖 **Qanday ishlaydi?**

🏦 **Kurslar** - Barcha banklar kurslarini ko'ring
🔔 **Alert** - Kurs o'zgarganda xabar oling
📊 **Tahlil** - RSI, MACD, SMA teknik tahlil
📈 **Grafik** - Valyuta kursi grafigi
💼 **Portfel** - Valyutalaringizni kuzating
💫 **Aqlli almashtirish** - Eng yaxshi vaqtda xabar

**Buyruqlar:**
/start - Bosh menyu
/rates - Kurslar
/help - Yordam

**Eslatma:**
🏛️ Markaziy Bank - rasmiy kurs
🏦 Tijorat banklar - taxminiy kurs

_Savollar uchun: @admin_username_
"""
    
    keyboard = [[InlineKeyboardButton("🏠 Menyu", callback_data="main_menu")]]
    
    await update.message.reply_text(
        help_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


def get_start_handlers() -> list:
    """Start handlers"""
    return [
        CommandHandler("start", start_command),
        CommandHandler("help", help_command),
        CallbackQueryHandler(language_callback, pattern=r"^set_lang_"),
        CallbackQueryHandler(show_main_menu, pattern=r"^main_menu$"),
        CallbackQueryHandler(language_menu, pattern=r"^language$"),
        CallbackQueryHandler(today_callback, pattern=r"^today$"),
    ]
