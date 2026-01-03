"""
Smart Exchange Handler - Notifies when best rate increases
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler,
    CallbackQueryHandler, MessageHandler, filters
)
from sqlalchemy import select

from handlers.common import get_user_language
from database.db import get_session
from database.models import SmartExchange
from services.rate_manager import get_rates_by_currency
from config import BANKS

logger = logging.getLogger(__name__)

# Conversation states
STEP_CURRENCY, STEP_AMOUNT, STEP_INCREASE, STEP_CONFIRM = range(4)


async def start_smart_exchange(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start smart exchange setup"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [
            InlineKeyboardButton("🇺🇸 USD (Dollar)", callback_data="smart_cur_USD"),
            InlineKeyboardButton("🇰🇿 KZT (Tenge)", callback_data="smart_cur_KZT"),
        ],
        [
            InlineKeyboardButton("🇪🇺 EUR (Yevro)", callback_data="smart_cur_EUR"),
            InlineKeyboardButton("🇷🇺 RUB (Rubl)", callback_data="smart_cur_RUB"),
        ],
        [InlineKeyboardButton("⬅️ Orqaga", callback_data="main_menu")],
    ]
    
    await query.edit_message_text(
        "💫 **Aqlli Almashtirish**\n\n"
        "Bu funksiya sizga eng yuqori sotib olish kursini kuzatib, "
        "kurs sizning chegarangizga yetganda xabar beradi.\n\n"
        "**1-qadam:** Qaysi valyutangiz bor?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return STEP_CURRENCY


async def step_currency(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle currency selection"""
    query = update.callback_query
    await query.answer()
    
    currency = query.data.replace("smart_cur_", "")
    context.user_data["smart_currency"] = currency
    
    # Get current best rate for this currency
    rates = await get_rates_by_currency(currency)
    best_rate = 0
    best_bank = ""
    
    for rate in rates:
        buy = rate.get("buy_rate") or 0
        if buy > best_rate:
            best_rate = buy
            best_bank = rate.get("bank_name", rate.get("bank_code", ""))
    
    context.user_data["smart_best_rate"] = best_rate
    context.user_data["smart_best_bank"] = best_bank
    
    currency_names = {
        "USD": "🇺🇸 Dollar",
        "EUR": "🇪🇺 Yevro", 
        "RUB": "🇷🇺 Rubl",
        "KZT": "🇰🇿 Tenge"
    }
    
    keyboard = [[InlineKeyboardButton("⬅️ Orqaga", callback_data="smart_exchange")]]
    
    await query.edit_message_text(
        f"💫 **Aqlli Almashtirish**\n\n"
        f"**Valyuta:** {currency_names.get(currency, currency)}\n"
        f"**Hozirgi eng yaxshi kurs:** {best_rate:,.0f} so'm ({best_bank})\n\n"
        f"**2-qadam:** Qancha {currency} bor?\n\n"
        f"_Masalan: 1000_",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return STEP_AMOUNT


async def step_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle amount input"""
    try:
        amount = float(update.message.text.replace(",", ".").replace(" ", ""))
        if amount <= 0:
            raise ValueError("Amount must be positive")
    except ValueError:
        await update.message.reply_text(
            "❌ Noto'g'ri format!\n\nFaqat raqam kiriting, masalan: 1000"
        )
        return STEP_AMOUNT
    
    context.user_data["smart_amount"] = amount
    currency = context.user_data.get("smart_currency", "USD")
    best_rate = context.user_data.get("smart_best_rate", 0)
    
    keyboard = [[InlineKeyboardButton("⬅️ Orqaga", callback_data="smart_exchange")]]
    
    await update.message.reply_text(
        f"💫 **Aqlli Almashtirish**\n\n"
        f"**Sizda:** {amount:,.0f} {currency}\n"
        f"**Hozirgi eng yaxshi kurs:** {best_rate:,.0f} so'm\n"
        f"**Hozirgi qiymat:** {amount * best_rate:,.0f} so'm\n\n"
        f"**3-qadam:** Kurs qanchaga ko'tarilganda xabar bersin?\n\n"
        f"_Masalan: 15 (ya'ni +15 so'm)_",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return STEP_INCREASE


async def step_increase(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle target increase input"""
    try:
        increase = float(update.message.text.replace(",", ".").replace(" ", "").replace("+", ""))
        if increase <= 0:
            raise ValueError("Increase must be positive")
    except ValueError:
        await update.message.reply_text(
            "❌ Noto'g'ri format!\n\nFaqat raqam kiriting, masalan: 15"
        )
        return STEP_INCREASE
    
    context.user_data["smart_increase"] = increase
    
    currency = context.user_data.get("smart_currency", "USD")
    amount = context.user_data.get("smart_amount", 0)
    best_rate = context.user_data.get("smart_best_rate", 0)
    best_bank = context.user_data.get("smart_best_bank", "")
    target_rate = best_rate + increase
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Tasdiqlash", callback_data="smart_confirm"),
            InlineKeyboardButton("❌ Bekor qilish", callback_data="main_menu"),
        ]
    ]
    
    await update.message.reply_text(
        f"💫 **Tasdiqlash**\n\n"
        f"**Valyuta:** {currency}\n"
        f"**Miqdor:** {amount:,.0f} {currency}\n"
        f"**Hozirgi eng yaxshi kurs:** {best_rate:,.0f} so'm ({best_bank})\n"
        f"**Maqsad kurs:** {target_rate:,.0f} so'm (+{increase:.0f})\n\n"
        f"Kurs {target_rate:,.0f} ga yetganda sizga xabar keladi.\n"
        f"Xabar har 5 daqiqada takrorlanadi \"Qabul qilish\" tugmasini bosgunizcha.\n\n"
        f"**Tasdiqlaysizmi?**",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return STEP_CONFIRM


async def confirm_smart_exchange(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Save smart exchange to database"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    currency = context.user_data.get("smart_currency", "USD")
    amount = context.user_data.get("smart_amount", 0)
    increase = context.user_data.get("smart_increase", 0)
    best_rate = context.user_data.get("smart_best_rate", 0)
    best_bank = context.user_data.get("smart_best_bank", "")
    
    async with get_session() as session:
        # Deactivate previous smart exchanges for this currency
        result = await session.execute(
            select(SmartExchange).where(
                SmartExchange.user_id == user_id,
                SmartExchange.currency_code == currency,
                SmartExchange.is_active == True
            )
        )
        old_exchanges = result.scalars().all()
        for old in old_exchanges:
            old.is_active = False
        
        # Create new smart exchange
        smart = SmartExchange(
            user_id=user_id,
            currency_code=currency,
            amount=amount,
            target_increase=increase,
            initial_best_rate=best_rate,
            initial_best_bank=best_bank,
            is_active=True,
            is_accepted=False
        )
        session.add(smart)
        await session.commit()
    
    # Clear context
    context.user_data.pop("smart_currency", None)
    context.user_data.pop("smart_amount", None)
    context.user_data.pop("smart_increase", None)
    context.user_data.pop("smart_best_rate", None)
    context.user_data.pop("smart_best_bank", None)
    
    keyboard = [[InlineKeyboardButton("🏠 Bosh menyu", callback_data="main_menu")]]
    
    await query.edit_message_text(
        f"✅ **Aqlli almashtirish faol!**\n\n"
        f"**Valyuta:** {currency}\n"
        f"**Miqdor:** {amount:,.0f} {currency}\n"
        f"**Maqsad:" f"** +{increase:.0f} so'm ko'tarilganda\n\n"
        f"Sizga xabar yuboriladi kurs ko'tarilganda. 🔔",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return ConversationHandler.END


async def accept_exchange(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """User accepts the exchange notification"""
    query = update.callback_query
    await query.answer("✅ Qabul qilindi!")
    
    # Extract smart exchange ID from callback data
    smart_id = int(query.data.replace("accept_smart_", ""))
    
    async with get_session() as session:
        result = await session.execute(
            select(SmartExchange).where(SmartExchange.id == smart_id)
        )
        smart = result.scalar_one_or_none()
        
        if smart:
            smart.is_accepted = True
            smart.is_active = False
            await session.commit()
    
    await query.edit_message_text(
        f"✅ **Qabul qilindi!**\n\n"
        f"Valyutani almashtirishni unutmang! 💰\n\n"
        f"Yangi kuzatish boshlash uchun \"💫 Aqlli almashtirish\" tugmasini bosing.",
        parse_mode="Markdown"
    )


async def skip_exchange(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """User skips/delays the notification"""
    query = update.callback_query
    await query.answer("⏰ 5 daqiqadan keyin yana xabar keladi")
    
    await query.edit_message_text(
        query.message.text + "\n\n_⏰ Keyingi xabar 5 daqiqadan so'ng keladi..._",
        parse_mode="Markdown"
    )


async def my_smart_exchanges(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user's active smart exchanges"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    async with get_session() as session:
        result = await session.execute(
            select(SmartExchange).where(
                SmartExchange.user_id == user_id,
                SmartExchange.is_active == True
            )
        )
        exchanges = result.scalars().all()
    
    if not exchanges:
        keyboard = [
            [InlineKeyboardButton("💫 Yangi qo'shish", callback_data="smart_exchange")],
            [InlineKeyboardButton("⬅️ Orqaga", callback_data="main_menu")],
        ]
        await query.edit_message_text(
            "📋 **Faol kuzatuvlar yo'q**\n\n"
            "Yangi aqlli almashtirish qo'shish uchun tugmani bosing.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return
    
    message = "📋 **Faol kuzatuvlar:**\n\n"
    buttons = []
    
    for ex in exchanges:
        target = ex.initial_best_rate + ex.target_increase
        message += (
            f"💱 **{ex.currency_code}**: {ex.amount:,.0f}\n"
            f"   Maqsad: {target:,.0f} so'm (+{ex.target_increase:.0f})\n\n"
        )
        buttons.append([
            InlineKeyboardButton(
                f"❌ {ex.currency_code} - bekor qilish",
                callback_data=f"cancel_smart_{ex.id}"
            )
        ])
    
    buttons.append([InlineKeyboardButton("💫 Yangi qo'shish", callback_data="smart_exchange")])
    buttons.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="main_menu")])
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="Markdown"
    )


async def cancel_smart_exchange(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Cancel a smart exchange"""
    query = update.callback_query
    
    smart_id = int(query.data.replace("cancel_smart_", ""))
    
    async with get_session() as session:
        result = await session.execute(
            select(SmartExchange).where(SmartExchange.id == smart_id)
        )
        smart = result.scalar_one_or_none()
        
        if smart and smart.user_id == update.effective_user.id:
            smart.is_active = False
            await session.commit()
            await query.answer("✅ Bekor qilindi!")
        else:
            await query.answer("❌ Topilmadi!")
            return
    
    # Show updated list
    await my_smart_exchanges(update, context)


async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel conversation"""
    query = update.callback_query
    if query:
        await query.answer()
    
    # Clear context
    context.user_data.pop("smart_currency", None)
    context.user_data.pop("smart_amount", None)
    context.user_data.pop("smart_increase", None)
    context.user_data.pop("smart_best_rate", None)
    context.user_data.pop("smart_best_bank", None)
    
    return ConversationHandler.END


def get_smart_exchange_conversation_handler() -> ConversationHandler:
    """Get conversation handler for smart exchange"""
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_smart_exchange, pattern=r"^smart_exchange$"),
        ],
        states={
            STEP_CURRENCY: [
                CallbackQueryHandler(step_currency, pattern=r"^smart_cur_"),
                CallbackQueryHandler(cancel_conversation, pattern=r"^main_menu$"),
            ],
            STEP_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, step_amount),
                CallbackQueryHandler(cancel_conversation, pattern=r"^(main_menu|smart_exchange)$"),
            ],
            STEP_INCREASE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, step_increase),
                CallbackQueryHandler(cancel_conversation, pattern=r"^(main_menu|smart_exchange)$"),
            ],
            STEP_CONFIRM: [
                CallbackQueryHandler(confirm_smart_exchange, pattern=r"^smart_confirm$"),
                CallbackQueryHandler(cancel_conversation, pattern=r"^main_menu$"),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(cancel_conversation, pattern=r"^main_menu$"),
        ],
        per_message=False,
    )


def get_smart_exchange_handlers() -> list:
    """Get additional handlers for smart exchange"""
    return [
        CallbackQueryHandler(accept_exchange, pattern=r"^accept_smart_\d+$"),
        CallbackQueryHandler(skip_exchange, pattern=r"^skip_smart_\d+$"),
        CallbackQueryHandler(my_smart_exchanges, pattern=r"^my_smart_exchanges$"),
        CallbackQueryHandler(cancel_smart_exchange, pattern=r"^cancel_smart_\d+$"),
    ]
