"""
Analysis Handler - Technical Analysis and AI Forecast Display
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

from handlers.common import get_user_language
from services.analysis_service import get_technical_analysis
from config import POPULAR_CURRENCIES


async def analysis_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Texnik tahlil buyrug'i"""
    keyboard = []
    row = []
    for cur in POPULAR_CURRENCIES[:6]:
        row.append(InlineKeyboardButton(f"📊 {cur}", callback_data=f"analyze_{cur}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="main_menu")])
    
    await update.message.reply_text(
        "📊 **Texnik Tahlil**\n\n"
        "Valyutani tanlang:\n\n"
        "🔹 RSI - kuch indeksi\n"
        "🔹 MACD - trend o'zgarishi\n"
        "🔹 SMA - o'rtacha kurs\n"
        "🔹 AI Prognoz - bashorat",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def analysis_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Tahlil menyudan"""
    query = update.callback_query
    await query.answer()
    
    keyboard = []
    row = []
    for cur in POPULAR_CURRENCIES[:6]:
        row.append(InlineKeyboardButton(f"📊 {cur}", callback_data=f"analyze_{cur}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="main_menu")])
    
    await query.edit_message_text(
        "📊 **Texnik Tahlil**\n\n"
        "Valyutani tanlang:\n\n"
        "🔹 RSI - kuch indeksi\n"
        "🔹 MACD - trend o'zgarishi\n"
        "🔹 SMA - o'rtacha kurs\n"
        "🔹 AI Prognoz - bashorat",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def show_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Tahlilni ko'rsatish"""
    query = update.callback_query
    await query.answer("Tahlil qilinmoqda...")
    
    currency = query.data.replace("analyze_", "")
    
    # Get analysis
    analysis = await get_technical_analysis(currency)
    
    if "error" in analysis:
        await query.edit_message_text(f"❌ Xatolik: {analysis['error']}")
        return
    
    pred = analysis["prediction"]
    macd = analysis.get("macd", {})
    
    # Build message
    message = f"📊 **{currency} Texnik Tahlil**\n\n"
    
    # Price info
    change_emoji = "📈" if analysis["change"] > 0 else "📉" if analysis["change"] < 0 else "➖"
    message += f"💰 **Joriy kurs:** {analysis['current_price']:,.0f}\n"
    message += f"{change_emoji} O'zgarish: {analysis['change']:+,.0f} ({analysis['change_pct']:+.1f}%)\n\n"
    
    # RSI
    message += "━━━ **RSI (Kuch indeksi)** ━━━\n"
    if analysis["rsi"]:
        rsi = analysis["rsi"]
        if rsi < 30:
            rsi_bar = "🟢" * 3 + "⚪" * 7
            rsi_text = "📈 Oshadi (oversold)"
        elif rsi > 70:
            rsi_bar = "🟢" * 7 + "🔴" * 3
            rsi_text = "📉 Tushadi (overbought)"
        else:
            rsi_bar = "🟢" * (rsi // 10) + "⚪" * (10 - rsi // 10)
            rsi_text = "➖ Neytral"
        message += f"RSI: **{rsi}** {rsi_text}\n"
        message += f"[{rsi_bar}]\n\n"
    else:
        message += "Ma'lumot yetarli emas\n\n"
    
    # MACD
    message += "━━━ **MACD (Trend)** ━━━\n"
    if macd:
        trend_emoji = "📈" if macd.get("trend") == "bullish" else "📉"
        message += f"Trend: **{macd.get('trend', 'unknown')}** {trend_emoji}\n"
        message += f"MACD: {macd.get('macd', 0):.2f}\n\n"
    else:
        message += "Ma'lumot yetarli emas\n\n"
    
    # Moving Averages
    message += "━━━ **SMA (O'rtacha)** ━━━\n"
    if analysis["sma_7"]:
        message += f"SMA 7: {analysis['sma_7']:,}\n"
    if analysis["sma_14"]:
        message += f"SMA 14: {analysis['sma_14']:,}\n"
    if analysis["sma_30"]:
        message += f"SMA 30: {analysis['sma_30']:,}\n"
    message += "\n"
    
    # AI Prediction
    message += "━━━ **🤖 AI Prognoz** ━━━\n"
    message += f"{pred['message']}\n"
    message += f"Ishonch: **{pred['confidence']}%**\n"
    
    keyboard = [
        [
            InlineKeyboardButton("📈 7 kun grafik", callback_data=f"period_{currency}_7"),
            InlineKeyboardButton("📈 30 kun grafik", callback_data=f"period_{currency}_30"),
        ],
        [InlineKeyboardButton("🔄 Yangilash", callback_data=f"analyze_{currency}")],
        [InlineKeyboardButton("⬅️ Orqaga", callback_data="analysis")],
        [InlineKeyboardButton("🏠 Menyu", callback_data="main_menu")]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


def get_analysis_handlers() -> list:
    """Analysis handlers"""
    return [
        CommandHandler("analysis", analysis_command),
        CallbackQueryHandler(analysis_callback, pattern=r"^analysis$"),
        CallbackQueryHandler(show_analysis, pattern=r"^analyze_[A-Z]+$"),
    ]
