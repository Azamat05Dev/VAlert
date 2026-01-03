"""
Portfolio Handler - Valyuta portfeli va foyda kalkulyatori
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ConversationHandler
)
from sqlalchemy import select, delete

from handlers.common import get_user_language
from database.db import get_session
from database.models import Portfolio
from services.rate_manager import get_rate
from config import POPULAR_CURRENCIES

# States
PORT_ACTION, PORT_CURRENCY, PORT_AMOUNT, PORT_PRICE = range(4)
PROFIT_CURRENCY, PROFIT_AMOUNT, PROFIT_BUY, PROFIT_SELL = range(4, 8)


# ==================== PORTFOLIO ====================

async def portfolio_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Portfelni ko'rsatish"""
    user_id = update.effective_user.id
    lang = await get_user_language(user_id)
    
    message, keyboard = await build_portfolio_view(user_id)
    
    await update.message.reply_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def portfolio_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Portfel menyudan"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    message, keyboard = await build_portfolio_view(user_id)
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def build_portfolio_view(user_id: int) -> tuple:
    """Portfel ma'lumotlarini yig'ish"""
    async with get_session() as session:
        result = await session.execute(
            select(Portfolio).where(Portfolio.user_id == user_id)
        )
        items = result.scalars().all()
    
    if not items:
        message = "💼 **Valyuta Portfelim**\n\n"
        message += "📭 Portfel bo'sh.\n\n"
        message += "➕ Valyuta qo'shish uchun tugmani bosing."
        keyboard = [
            [InlineKeyboardButton("➕ Valyuta qo'shish", callback_data="port_add")],
            [InlineKeyboardButton("⬅️ Orqaga", callback_data="main_menu")]
        ]
        return message, keyboard
    
    message = "💼 **Valyuta Portfelim**\n\n"
    total_uzs = 0
    total_profit = 0
    
    for item in items:
        # Joriy kursni olish
        rate = await get_rate("cbu", item.currency_code)
        if rate:
            current_rate = rate.get("official_rate", 0)
            nominal = rate.get("nominal", 1)
            current_value = (item.amount / nominal) * current_rate
            
            # Foyda hisoblash
            if item.buy_price:
                buy_value = item.amount * item.buy_price
                profit = current_value - buy_value
                profit_pct = ((current_value / buy_value) - 1) * 100 if buy_value else 0
                profit_emoji = "📈" if profit >= 0 else "📉"
                profit_text = f" {profit_emoji} {profit:+,.0f}"
            else:
                profit = 0
                profit_text = ""
            
            total_uzs += current_value
            total_profit += profit
            
            message += f"💱 **{item.amount:,.0f} {item.currency_code}**\n"
            message += f"   💰 {current_value:,.0f} so'm{profit_text}\n\n"
    
    profit_emoji = "📈" if total_profit >= 0 else "📉"
    message += f"━━━━━━━━━━━━━━━━━\n"
    message += f"💰 **Jami**: {total_uzs:,.0f} so'm\n"
    message += f"{profit_emoji} **Foyda**: {total_profit:+,.0f} so'm"
    
    keyboard = [
        [InlineKeyboardButton("➕ Qo'shish", callback_data="port_add")],
        [InlineKeyboardButton("🗑️ O'chirish", callback_data="port_delete")],
        [InlineKeyboardButton("⬅️ Orqaga", callback_data="main_menu")]
    ]
    
    return message, keyboard


async def port_add_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Valyuta qo'shish - boshlanish"""
    query = update.callback_query
    await query.answer()
    
    keyboard = []
    row = []
    for cur in POPULAR_CURRENCIES:
        row.append(InlineKeyboardButton(f"💱 {cur}", callback_data=f"padd_{cur}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("❌ Bekor", callback_data="port_cancel")])
    
    await query.edit_message_text(
        "💼 **Portfelga qo'shish**\n\n"
        "Valyutani tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return PORT_CURRENCY


async def port_currency(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Valyuta tanlash"""
    query = update.callback_query
    await query.answer()
    
    currency = query.data.replace("padd_", "")
    context.user_data["port_currency"] = currency
    
    keyboard = [[InlineKeyboardButton("❌ Bekor", callback_data="port_cancel")]]
    
    await query.edit_message_text(
        f"💼 **Portfelga qo'shish**\n\n"
        f"💱 Valyuta: **{currency}**\n\n"
        f"Miqdorini kiriting:\n"
        f"Masalan: `500`",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return PORT_AMOUNT


async def port_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Miqdorni kiritish"""
    try:
        amount = float(update.message.text.replace(",", ".").replace(" ", ""))
    except ValueError:
        await update.message.reply_text("❌ Faqat raqam kiriting!")
        return PORT_AMOUNT
    
    context.user_data["port_amount"] = amount
    currency = context.user_data["port_currency"]
    
    keyboard = [
        [InlineKeyboardButton("⏭️ Narxsiz qo'shish", callback_data="port_skip_price")],
        [InlineKeyboardButton("❌ Bekor", callback_data="port_cancel")]
    ]
    
    await update.message.reply_text(
        f"💼 **Portfelga qo'shish**\n\n"
        f"💱 Valyuta: **{currency}**\n"
        f"📊 Miqdor: **{amount:,.0f}**\n\n"
        f"Sotib olgan narxingiz (so'mda):\n"
        f"Masalan: `12500`\n\n"
        f"_Yoki narxsiz qo'shish tugmasini bosing_",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return PORT_PRICE


async def port_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Narxni kiritish va saqlash"""
    try:
        price = float(update.message.text.replace(",", ".").replace(" ", ""))
    except ValueError:
        await update.message.reply_text("❌ Faqat raqam kiriting!")
        return PORT_PRICE
    
    return await save_portfolio(update, context, price)


async def port_skip_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Narxsiz saqlash"""
    query = update.callback_query
    await query.answer()
    
    return await save_portfolio(update, context, None, is_callback=True)


async def save_portfolio(update, context, price, is_callback=False):
    """Portfelni saqlash"""
    user_id = update.effective_user.id
    currency = context.user_data["port_currency"]
    amount = context.user_data["port_amount"]
    
    async with get_session() as session:
        item = Portfolio(
            user_id=user_id,
            currency_code=currency,
            amount=amount,
            buy_price=price
        )
        session.add(item)
        await session.commit()
    
    context.user_data.clear()
    lang = await get_user_language(user_id)
    
    from handlers.start import get_main_menu_keyboard
    
    message = (
        f"✅ **Portfelga qo'shildi!**\n\n"
        f"💱 **{amount:,.0f} {currency}**\n"
    )
    if price:
        message += f"💰 Narx: {price:,.0f} so'm"
    
    if is_callback:
        await update.callback_query.edit_message_text(
            message,
            reply_markup=get_main_menu_keyboard(lang),
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            message,
            reply_markup=get_main_menu_keyboard(lang),
            parse_mode="Markdown"
        )
    
    return ConversationHandler.END


async def port_delete_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """O'chirish uchun tanlash"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    async with get_session() as session:
        result = await session.execute(
            select(Portfolio).where(Portfolio.user_id == user_id)
        )
        items = result.scalars().all()
    
    if not items:
        await query.edit_message_text("📭 Portfel bo'sh.")
        return
    
    keyboard = []
    for item in items:
        keyboard.append([
            InlineKeyboardButton(
                f"🗑️ {item.amount:,.0f} {item.currency_code}",
                callback_data=f"pdel_{item.id}"
            )
        ])
    keyboard.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="portfolio")])
    
    await query.edit_message_text(
        "🗑️ **O'chirish uchun tanlang:**",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def port_delete_item(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Elementni o'chirish"""
    query = update.callback_query
    await query.answer()
    
    item_id = int(query.data.replace("pdel_", ""))
    user_id = update.effective_user.id
    
    async with get_session() as session:
        await session.execute(
            delete(Portfolio).where(Portfolio.id == item_id, Portfolio.user_id == user_id)
        )
        await session.commit()
    
    message, keyboard = await build_portfolio_view(user_id)
    message = "✅ O'chirildi!\n\n" + message
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def port_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Bekor qilish"""
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    
    user_id = update.effective_user.id
    message, keyboard = await build_portfolio_view(user_id)
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return ConversationHandler.END


# ==================== FOYDA KALKULYATORI ====================

async def profit_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Foyda kalkulyatori"""
    keyboard = []
    row = []
    for cur in POPULAR_CURRENCIES[:6]:
        row.append(InlineKeyboardButton(f"💱 {cur}", callback_data=f"prof_{cur}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("❌ Bekor", callback_data="prof_cancel")])
    
    await update.message.reply_text(
        "💰 **Foyda Kalkulyatori**\n\n"
        "Valyutani tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return PROFIT_CURRENCY


async def profit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Foyda kalkulyatori menyudan"""
    query = update.callback_query
    await query.answer()
    
    keyboard = []
    row = []
    for cur in POPULAR_CURRENCIES[:6]:
        row.append(InlineKeyboardButton(f"💱 {cur}", callback_data=f"prof_{cur}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("❌ Bekor", callback_data="prof_cancel")])
    
    await query.edit_message_text(
        "💰 **Foyda Kalkulyatori**\n\n"
        "Valyutani tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return PROFIT_CURRENCY


async def profit_currency(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Valyuta tanlash"""
    query = update.callback_query
    await query.answer()
    
    currency = query.data.replace("prof_", "")
    context.user_data["profit_currency"] = currency
    
    keyboard = [[InlineKeyboardButton("❌ Bekor", callback_data="prof_cancel")]]
    
    await query.edit_message_text(
        f"💰 **Foyda Kalkulyatori**\n\n"
        f"💱 Valyuta: **{currency}**\n\n"
        f"Necha {currency} sotib oldingiz?\n"
        f"Masalan: `1000`",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return PROFIT_AMOUNT


async def profit_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Miqdor kiritish"""
    try:
        amount = float(update.message.text.replace(",", ".").replace(" ", ""))
    except ValueError:
        await update.message.reply_text("❌ Faqat raqam kiriting!")
        return PROFIT_AMOUNT
    
    context.user_data["profit_amount"] = amount
    currency = context.user_data["profit_currency"]
    
    keyboard = [[InlineKeyboardButton("❌ Bekor", callback_data="prof_cancel")]]
    
    await update.message.reply_text(
        f"💰 **Foyda Kalkulyatori**\n\n"
        f"💱 Valyuta: **{currency}**\n"
        f"📊 Miqdor: **{amount:,.0f}**\n\n"
        f"Qancha narxda sotib oldingiz? (so'mda)\n"
        f"Masalan: `12500`",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return PROFIT_BUY


async def profit_buy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Sotib olish narxi"""
    try:
        buy_price = float(update.message.text.replace(",", ".").replace(" ", ""))
    except ValueError:
        await update.message.reply_text("❌ Faqat raqam kiriting!")
        return PROFIT_BUY
    
    context.user_data["profit_buy"] = buy_price
    currency = context.user_data["profit_currency"]
    amount = context.user_data["profit_amount"]
    
    keyboard = [[InlineKeyboardButton("❌ Bekor", callback_data="prof_cancel")]]
    
    await update.message.reply_text(
        f"💰 **Foyda Kalkulyatori**\n\n"
        f"💱 Valyuta: **{currency}**\n"
        f"📊 Miqdor: **{amount:,.0f}**\n"
        f"📥 Sotib olish: **{buy_price:,.0f}** so'm\n\n"
        f"Qancha narxda sotmoqchisiz? (so'mda)\n"
        f"Masalan: `12800`",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return PROFIT_SELL


async def profit_sell(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Sotish narxi va hisoblash"""
    try:
        sell_price = float(update.message.text.replace(",", ".").replace(" ", ""))
    except ValueError:
        await update.message.reply_text("❌ Faqat raqam kiriting!")
        return PROFIT_SELL
    
    currency = context.user_data["profit_currency"]
    amount = context.user_data["profit_amount"]
    buy_price = context.user_data["profit_buy"]
    
    # Hisoblash
    buy_total = amount * buy_price
    sell_total = amount * sell_price
    profit = sell_total - buy_total
    profit_pct = ((sell_price / buy_price) - 1) * 100
    
    context.user_data.clear()
    lang = await get_user_language(update.effective_user.id)
    
    from handlers.start import get_main_menu_keyboard
    
    profit_emoji = "📈" if profit >= 0 else "📉"
    
    await update.message.reply_text(
        f"💰 **Foyda Kalkulyatori - Natija**\n\n"
        f"💱 **{amount:,.0f} {currency}**\n\n"
        f"📥 Sotib olish: {buy_price:,.0f} × {amount:,.0f} = **{buy_total:,.0f}** so'm\n"
        f"📤 Sotish: {sell_price:,.0f} × {amount:,.0f} = **{sell_total:,.0f}** so'm\n\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"{profit_emoji} **Foyda: {profit:+,.0f} so'm** ({profit_pct:+.1f}%)",
        reply_markup=get_main_menu_keyboard(lang),
        parse_mode="Markdown"
    )
    return ConversationHandler.END


async def prof_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Bekor qilish"""
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    
    lang = await get_user_language(update.effective_user.id)
    from handlers.start import get_main_menu_keyboard
    
    await query.edit_message_text("❌ Bekor qilindi.", reply_markup=get_main_menu_keyboard(lang))
    return ConversationHandler.END


# ==================== HANDLERS ====================

def get_portfolio_conversation_handler() -> ConversationHandler:
    """Portfolio add conversation"""
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(port_add_start, pattern=r"^port_add$"),
        ],
        states={
            PORT_CURRENCY: [
                CallbackQueryHandler(port_currency, pattern=r"^padd_"),
                CallbackQueryHandler(port_cancel, pattern=r"^port_cancel$"),
            ],
            PORT_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, port_amount),
                CallbackQueryHandler(port_cancel, pattern=r"^port_cancel$"),
            ],
            PORT_PRICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, port_price),
                CallbackQueryHandler(port_skip_price, pattern=r"^port_skip_price$"),
                CallbackQueryHandler(port_cancel, pattern=r"^port_cancel$"),
            ],
        },
        fallbacks=[CallbackQueryHandler(port_cancel, pattern=r"^port_cancel$")],
        per_user=True,
        per_chat=True,
    )


def get_profit_conversation_handler() -> ConversationHandler:
    """Profit calc conversation"""
    return ConversationHandler(
        entry_points=[
            CommandHandler("profit", profit_command),
            CallbackQueryHandler(profit_callback, pattern=r"^profit$"),
        ],
        states={
            PROFIT_CURRENCY: [
                CallbackQueryHandler(profit_currency, pattern=r"^prof_"),
                CallbackQueryHandler(prof_cancel, pattern=r"^prof_cancel$"),
            ],
            PROFIT_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, profit_amount),
                CallbackQueryHandler(prof_cancel, pattern=r"^prof_cancel$"),
            ],
            PROFIT_BUY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, profit_buy),
                CallbackQueryHandler(prof_cancel, pattern=r"^prof_cancel$"),
            ],
            PROFIT_SELL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, profit_sell),
                CallbackQueryHandler(prof_cancel, pattern=r"^prof_cancel$"),
            ],
        },
        fallbacks=[CallbackQueryHandler(prof_cancel, pattern=r"^prof_cancel$")],
        per_user=True,
        per_chat=True,
    )


def get_portfolio_handlers() -> list:
    """Portfolio handlers"""
    return [
        CommandHandler("portfolio", portfolio_command),
        CallbackQueryHandler(portfolio_callback, pattern=r"^portfolio$"),
        CallbackQueryHandler(port_delete_start, pattern=r"^port_delete$"),
        CallbackQueryHandler(port_delete_item, pattern=r"^pdel_"),
    ]
