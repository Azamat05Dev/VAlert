"""
Tools Handler - Calculator, Best Rate, Portfolio
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ConversationHandler
)
from sqlalchemy import select

from handlers.common import get_user_language
from locales.helpers import t
from database.db import get_session
from database.models import Rate
from services.rate_manager import get_rate, get_rates_by_currency
from config import BANKS, POPULAR_CURRENCIES

# Calculator states
CALC_CURRENCY, CALC_AMOUNT = range(2)


# ==================== KALKULYATOR ====================

async def calc_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Valyuta kalkulyatori"""
    keyboard = []
    row = []
    for cur in POPULAR_CURRENCIES:
        row.append(InlineKeyboardButton(f"💱 {cur}", callback_data=f"calc_{cur}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("❌ Bekor qilish", callback_data="calc_cancel")])
    
    await update.message.reply_text(
        "🧮 **Valyuta Kalkulyatori**\n\n"
        "Valyutani tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return CALC_CURRENCY


async def calc_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Kalkulyator menyudan"""
    query = update.callback_query
    await query.answer()
    
    keyboard = []
    row = []
    for cur in POPULAR_CURRENCIES:
        row.append(InlineKeyboardButton(f"💱 {cur}", callback_data=f"calc_{cur}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("❌ Bekor qilish", callback_data="calc_cancel")])
    
    await query.edit_message_text(
        "🧮 **Valyuta Kalkulyatori**\n\n"
        "Valyutani tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return CALC_CURRENCY


async def calc_select_currency(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Miqdorni kiriting"""
    query = update.callback_query
    await query.answer()
    
    currency = query.data.replace("calc_", "")
    context.user_data["calc_currency"] = currency
    
    # Joriy kursni olish
    rate = await get_rate("cbu", currency)
    if rate:
        official = rate.get("official_rate", 0)
        nominal = rate.get("nominal", 1)
    else:
        official = 0
        nominal = 1
    
    context.user_data["calc_rate"] = official
    context.user_data["calc_nominal"] = nominal
    
    keyboard = [[InlineKeyboardButton("❌ Bekor qilish", callback_data="calc_cancel")]]
    
    await query.edit_message_text(
        f"🧮 **Valyuta Kalkulyatori**\n\n"
        f"💱 Valyuta: **{currency}**\n"
        f"📊 Kurs: **{nominal} {currency} = {official:,.2f} so'm**\n\n"
        f"Miqdorni kiriting:\n\n"
        f"Masalan: `100` yoki `1000`",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return CALC_AMOUNT


async def calc_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Hisoblash"""
    try:
        amount = float(update.message.text.replace(",", ".").replace(" ", ""))
    except ValueError:
        await update.message.reply_text("❌ Faqat raqam kiriting!")
        return CALC_AMOUNT
    
    currency = context.user_data.get("calc_currency", "USD")
    rate = context.user_data.get("calc_rate", 0)
    nominal = context.user_data.get("calc_nominal", 1)
    
    # Hisoblash
    uzs = (amount / nominal) * rate
    
    context.user_data.clear()
    lang = await get_user_language(update.effective_user.id)
    
    from handlers.start import get_main_menu_keyboard
    
    await update.message.reply_text(
        f"🧮 **Natija**\n\n"
        f"💱 **{amount:,.0f} {currency}** = **{uzs:,.0f} so'm**\n\n"
        f"📊 Kurs: {nominal} {currency} = {rate:,.2f} so'm\n"
        f"🏛️ Markaziy Bank kursi",
        reply_markup=get_main_menu_keyboard(lang),
        parse_mode="Markdown"
    )
    return ConversationHandler.END


async def calc_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Bekor qilish"""
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    
    lang = await get_user_language(update.effective_user.id)
    from handlers.start import get_main_menu_keyboard
    
    await query.edit_message_text("❌ Bekor qilindi.", reply_markup=get_main_menu_keyboard(lang))
    return ConversationHandler.END


# ==================== ENG YAXSHI KURS ====================

async def best_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Eng yaxshi kursni topish"""
    keyboard = []
    row = []
    for cur in POPULAR_CURRENCIES[:4]:
        row.append(InlineKeyboardButton(f"💱 {cur}", callback_data=f"best_{cur}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    lang = await get_user_language(update.effective_user.id)
    keyboard.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="main_menu")])
    
    await update.message.reply_text(
        "🏆 **Eng yaxshi kurs**\n\n"
        "Valyutani tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def best_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Eng yaxshi kurs menyudan"""
    query = update.callback_query
    await query.answer()
    
    keyboard = []
    row = []
    for cur in POPULAR_CURRENCIES[:4]:
        row.append(InlineKeyboardButton(f"💱 {cur}", callback_data=f"best_{cur}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    lang = await get_user_language(update.effective_user.id)
    keyboard.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="main_menu")])
    
    await query.edit_message_text(
        "🏆 **Eng yaxshi kurs**\n\n"
        "Valyutani tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def show_best_rate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Eng yaxshi kursni ko'rsatish"""
    query = update.callback_query
    await query.answer()
    
    currency = query.data.replace("best_", "")
    lang = await get_user_language(update.effective_user.id)
    
    rates = await get_rates_by_currency(currency)
    
    if not rates:
        await query.edit_message_text(f"❌ {currency} kurslari topilmadi.")
        return
    
    # Eng yuqori sotib olish va eng past sotish
    buy_rates = [(r, r.get("buy_rate") or r.get("official_rate") or 0) for r in rates]
    sell_rates = [(r, r.get("sell_rate") or r.get("official_rate") or 0) for r in rates]
    
    best_buy = max(buy_rates, key=lambda x: x[1])
    best_sell = min(sell_rates, key=lambda x: x[1])
    
    best_buy_bank = BANKS.get(best_buy[0]["bank_code"], {}).get("name_uz", "")
    best_sell_bank = BANKS.get(best_sell[0]["bank_code"], {}).get("name_uz", "")
    
    message = f"🏆 **{currency} - Eng yaxshi kurslar**\n\n"
    message += f"📥 **Sotib olish (eng yuqori):**\n"
    message += f"   🏦 {best_buy_bank}\n"
    message += f"   💰 **{best_buy[1]:,.0f}** so'm\n\n"
    message += f"📤 **Sotish (eng past):**\n"
    message += f"   🏦 {best_sell_bank}\n"
    message += f"   💰 **{best_sell[1]:,.0f}** so'm\n\n"
    
    # Boshqa banklar
    message += "📊 **Barcha banklar:**\n"
    sorted_buy = sorted(buy_rates, key=lambda x: x[1], reverse=True)[:5]
    for r, rate in sorted_buy:
        bank = BANKS.get(r["bank_code"], {}).get("name_uz", "")[:12]
        message += f"   {bank}: {rate:,.0f}\n"
    
    keyboard = [
        [InlineKeyboardButton("⬅️ Orqaga", callback_data="best")],
        [InlineKeyboardButton("🏠 Menyu", callback_data="main_menu")]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


# ==================== KUNLIK KURS ====================

async def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Bugungi kurslar"""
    lang = await get_user_language(update.effective_user.id)
    
    message = "📅 **Bugungi kurslar**\n\n"
    
    for cur in POPULAR_CURRENCIES[:5]:
        rate = await get_rate("cbu", cur)
        if rate:
            official = rate.get("official_rate", 0)
            diff = rate.get("diff", 0)
            nominal = rate.get("nominal", 1)
            
            if diff > 0:
                change = f"📈 +{diff:.2f}"
            elif diff < 0:
                change = f"📉 {diff:.2f}"
            else:
                change = "➖ 0"
            
            message += f"💱 **{cur}**: {official:,.2f} so'm {change}\n"
    
    from handlers.start import get_main_menu_keyboard
    
    await update.message.reply_text(
        message,
        reply_markup=get_main_menu_keyboard(lang),
        parse_mode="Markdown"
    )


# ==================== HANDLERS ====================

def get_calc_conversation_handler() -> ConversationHandler:
    """Kalkulyator conversation"""
    return ConversationHandler(
        entry_points=[
            CommandHandler("calc", calc_command),
            CallbackQueryHandler(calc_callback, pattern=r"^calculator$"),
        ],
        states={
            CALC_CURRENCY: [
                CallbackQueryHandler(calc_select_currency, pattern=r"^calc_[A-Z]+$"),
                CallbackQueryHandler(calc_cancel, pattern=r"^calc_cancel$"),
            ],
            CALC_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, calc_amount),
                CallbackQueryHandler(calc_cancel, pattern=r"^calc_cancel$"),
            ],
        },
        fallbacks=[CallbackQueryHandler(calc_cancel, pattern=r"^calc_cancel$")],
        per_user=True,
        per_chat=True,
    )


def get_tools_handlers() -> list:
    """Tools handlers"""
    return [
        CommandHandler("best", best_command),
        CommandHandler("today", today_command),
        CallbackQueryHandler(best_callback, pattern=r"^best$"),
        CallbackQueryHandler(show_best_rate, pattern=r"^best_[A-Z]+$"),
    ]
