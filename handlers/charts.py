"""
Chart Handler - Show rate history charts and trend analysis
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

from handlers.common import get_user_language
from services.chart_service import generate_rate_chart, generate_trend_analysis
from config import POPULAR_CURRENCIES


async def chart_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Grafik buyrug'i"""
    keyboard = []
    row = []
    for cur in POPULAR_CURRENCIES[:6]:
        row.append(InlineKeyboardButton(f"📈 {cur}", callback_data=f"chart_{cur}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    lang = await get_user_language(update.effective_user.id)
    keyboard.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="main_menu")])
    
    await update.message.reply_text(
        "📈 **Kurs Tarixi Grafigi**\n\n"
        "Valyutani tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def chart_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Chart menyudan"""
    query = update.callback_query
    await query.answer()
    
    keyboard = []
    row = []
    for cur in POPULAR_CURRENCIES[:6]:
        row.append(InlineKeyboardButton(f"📈 {cur}", callback_data=f"chart_{cur}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    lang = await get_user_language(update.effective_user.id)
    keyboard.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="main_menu")])
    
    await query.edit_message_text(
        "📈 **Kurs Tarixi Grafigi**\n\n"
        "Valyutani tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def show_chart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Grafikni ko'rsatish"""
    query = update.callback_query
    await query.answer("Grafik tayyorlanmoqda...")
    
    currency = query.data.replace("chart_", "")
    
    # Show period selection
    keyboard = [
        [
            InlineKeyboardButton("📅 7 kun", callback_data=f"period_{currency}_7"),
            InlineKeyboardButton("📅 30 kun", callback_data=f"period_{currency}_30"),
        ],
        [InlineKeyboardButton("📊 Trend tahlili", callback_data=f"trend_{currency}")],
        [InlineKeyboardButton("⬅️ Orqaga", callback_data="charts")]
    ]
    
    await query.edit_message_text(
        f"📈 **{currency} Grafigi**\n\n"
        f"Qancha kunlik ma'lumot kerak?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def generate_and_send_chart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Grafikni yaratish va yuborish"""
    query = update.callback_query
    await query.answer("Grafik tayyorlanmoqda...")
    
    # period_USD_7
    parts = query.data.replace("period_", "").split("_")
    currency = parts[0]
    days = int(parts[1])
    
    # Send typing action
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="upload_photo"
    )
    
    # Generate chart
    chart_bytes = await generate_rate_chart(currency, "cbu", days)
    
    if chart_bytes:
        # First send photo without buttons
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=chart_bytes,
            caption=f"📈 **{currency}** - {days} kunlik kurs tarixi",
            parse_mode="Markdown"
        )
        
        # Then send message with buttons
        keyboard = [
            [
                InlineKeyboardButton("📅 7 kun", callback_data=f"period_{currency}_7"),
                InlineKeyboardButton("📅 30 kun", callback_data=f"period_{currency}_30"),
            ],
            [InlineKeyboardButton("📊 Trend", callback_data=f"chart_trend_{currency}")],
            [InlineKeyboardButton("🏠 Menyu", callback_data="main_menu")]
        ]
        
        # Delete old message
        try:
            await query.delete_message()
        except:
            pass
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"📈 **{currency}** grafigi yuqorida.\n\nYana nimani ko'rmoqchisiz?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    else:
        from handlers.start import get_main_menu_keyboard
        lang = await get_user_language(update.effective_user.id)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ Grafik yaratishda xatolik",
            reply_markup=get_main_menu_keyboard(lang)
        )


async def show_trend(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Trend tahlilini ko'rsatish"""
    query = update.callback_query
    await query.answer()
    
    # Handle both trend_ and chart_trend_ patterns
    currency = query.data.replace("chart_trend_", "").replace("trend_", "")
    
    # Get trend analysis
    analysis = await generate_trend_analysis(currency, days=7)
    
    if not analysis.get("has_data"):
        message = f"📊 **{currency} Trend Tahlili**\n\n"
        message += "⚠️ Tarix ma'lumotlari yetarli emas.\n"
        message += "Bot ishlagan vaqt davomida ma'lumotlar to'planadi."
    else:
        change_emoji = "📈" if analysis["change"] > 0 else "📉" if analysis["change"] < 0 else "➖"
        
        message = (
            f"📊 **{currency} Trend Tahlili**\n"
            f"📅 Oxirgi {analysis['days']} kun\n\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"📈 Trend: **{analysis['trend']}**\n\n"
            f"💰 Boshlang'ich: {analysis['first_rate']:,.0f}\n"
            f"💰 Hozirgi: {analysis['last_rate']:,.0f}\n"
            f"{change_emoji} O'zgarish: **{analysis['change']:+,.0f}** ({analysis['change_pct']:+.1f}%)\n\n"
            f"📉 Minimal: {analysis['min_rate']:,.0f}\n"
            f"📈 Maksimal: {analysis['max_rate']:,.0f}\n"
            f"📊 O'rtacha: {analysis['avg_rate']:,.0f}\n\n"
            f"📊 Ma'lumotlar soni: {analysis['data_points']}"
        )
    
    keyboard = [
        [InlineKeyboardButton(f"📈 {currency} grafigi", callback_data=f"chart_{currency}")],
        [InlineKeyboardButton("⬅️ Orqaga", callback_data="charts")],
        [InlineKeyboardButton("🏠 Menyu", callback_data="main_menu")]
    ]
    
    try:
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    except:
        # If editing fails (e.g., from photo), send new message
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )


def get_chart_handlers() -> list:
    """Chart handlers"""
    return [
        CommandHandler("chart", chart_command),
        CallbackQueryHandler(chart_callback, pattern=r"^charts$"),
        CallbackQueryHandler(show_chart, pattern=r"^chart_[A-Z]+$"),
        CallbackQueryHandler(generate_and_send_chart, pattern=r"^period_"),
        CallbackQueryHandler(show_trend, pattern=r"^chart_trend_"),
        CallbackQueryHandler(show_trend, pattern=r"^trend_[A-Z]+$"),
    ]
