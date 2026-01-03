"""
Alerts Handler - Super Simple Flow
1. Valyuta tanlang (USD, EUR...)
2. Bank tanlang
3. Xabar bersin: Sotib olish oshganda / Sotib olish tushganda / Sotish oshganda / Sotish tushganda
4. Narx kiriting
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, ConversationHandler
)
from sqlalchemy import select, delete

from handlers.common import get_user_language
from locales.helpers import t
from database.db import get_session
from database.models import Alert
from services.rate_manager import get_rate
from config import BANKS, POPULAR_CURRENCIES

# States: Valyuta → Bank → Xabar turi → Narx → Takroriy
STEP_CURRENCY, STEP_BANK, STEP_ALERT_TYPE, STEP_PRICE, STEP_REPEAT = range(5)


async def alert_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """1-qadam: Valyutani tanlang"""
    keyboard = []
    row = []
    for currency in POPULAR_CURRENCIES:
        row.append(InlineKeyboardButton(f"💱 {currency}", callback_data=f"c_{currency}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel")])
    
    await update.message.reply_text(
        "🔔 **Alert yaratish**\n\n"
        "1️⃣ Valyutani tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return STEP_CURRENCY


async def new_alert_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Alert yaratish menyudan"""
    query = update.callback_query
    await query.answer()
    
    keyboard = []
    row = []
    for currency in POPULAR_CURRENCIES:
        row.append(InlineKeyboardButton(f"💱 {currency}", callback_data=f"c_{currency}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel")])
    
    await query.edit_message_text(
        "🔔 **Alert yaratish**\n\n"
        "1️⃣ Valyutani tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return STEP_CURRENCY


async def step_currency(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """2-qadam: Bankni tanlang"""
    query = update.callback_query
    await query.answer()
    
    currency = query.data.replace("c_", "")
    context.user_data["currency"] = currency
    
    # Bank tugmalari
    keyboard = []
    
    # Eng yaxshi kurs tugmalari
    keyboard.append([
        InlineKeyboardButton("📈 Eng yuqori kurs", callback_data="b_best_high"),
        InlineKeyboardButton("📉 Eng past kurs", callback_data="b_best_low"),
    ])
    
    keyboard.append([InlineKeyboardButton("🏛️ Markaziy Bank", callback_data="b_cbu")])
    
    commercial = [(k, v) for k, v in BANKS.items() if v["type"] == "commercial"]
    row = []
    for code, info in commercial[:8]:
        row.append(InlineKeyboardButton(f"🏦 {info['name_uz'][:10]}", callback_data=f"b_{code}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel")])
    
    await query.edit_message_text(
        f"🔔 **Alert yaratish**\n\n"
        f"💱 Valyuta: **{currency}**\n\n"
        f"2️⃣ Bankni tanlang:\n\n"
        f"📈 **Eng yuqori** - barcha banklardan eng yuqori\n"
        f"📉 **Eng past** - barcha banklardan eng past",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return STEP_BANK


async def step_bank(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """3-qadam: Qachon xabar bersin"""
    query = update.callback_query
    await query.answer()
    
    bank_code = query.data.replace("b_", "")
    context.user_data["bank"] = bank_code
    
    currency = context.user_data["currency"]
    bank_info = BANKS.get(bank_code, {})
    bank_name = bank_info.get("name_uz", bank_code)
    
    # Joriy kursni olish
    rate_data = await get_rate(bank_code, currency)
    if rate_data:
        buy = rate_data.get("buy_rate") or rate_data.get("official_rate") or 0
        sell = rate_data.get("sell_rate") or rate_data.get("official_rate") or 0
    else:
        buy = sell = 0
    
    context.user_data["buy"] = buy
    context.user_data["sell"] = sell
    
    keyboard = [
        [InlineKeyboardButton(f"📥 Sotib olish ⬆️ {buy:,.0f} dan oshsa", callback_data="t_buy_up")],
        [InlineKeyboardButton(f"📥 Sotib olish ⬇️ {buy:,.0f} dan tushsa", callback_data="t_buy_down")],
        [InlineKeyboardButton(f"📤 Sotish ⬆️ {sell:,.0f} dan oshsa", callback_data="t_sell_up")],
        [InlineKeyboardButton(f"📤 Sotish ⬇️ {sell:,.0f} dan tushsa", callback_data="t_sell_down")],
        [InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel")]
    ]
    
    await query.edit_message_text(
        f"🔔 **Alert yaratish**\n\n"
        f"💱 Valyuta: **{currency}**\n"
        f"🏦 Bank: **{bank_name}**\n\n"
        f"📊 **Hozirgi kurslar:**\n"
        f"   📥 Sotib olish: {buy:,.0f} so'm\n"
        f"   📤 Sotish: {sell:,.0f} so'm\n\n"
        f"3️⃣ Qachon xabar bersin?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return STEP_ALERT_TYPE


async def step_alert_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """4-qadam: Narxni kiriting"""
    query = update.callback_query
    await query.answer()
    
    # t_buy_up, t_buy_down, t_sell_up, t_sell_down
    parts = query.data.replace("t_", "").split("_")
    rate_type = parts[0]  # buy or sell
    direction = "above" if parts[1] == "up" else "below"
    
    context.user_data["rate_type"] = rate_type
    context.user_data["direction"] = direction
    
    currency = context.user_data["currency"]
    bank_code = context.user_data["bank"]
    bank_info = BANKS.get(bank_code, {})
    bank_name = bank_info.get("name_uz", bank_code)
    
    current = context.user_data["buy"] if rate_type == "buy" else context.user_data["sell"]
    
    rate_text = "📥 Sotib olish" if rate_type == "buy" else "📤 Sotish"
    dir_text = "⬆️ oshganda" if direction == "above" else "⬇️ tushganda"
    
    # Maslahat narx
    if direction == "above":
        example = int(current * 1.01)  # 1% yuqori
    else:
        example = int(current * 0.99)  # 1% past
    
    keyboard = [[InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel")]]
    
    await query.edit_message_text(
        f"🔔 **Alert yaratish**\n\n"
        f"💱 Valyuta: **{currency}**\n"
        f"🏦 Bank: **{bank_name}**\n"
        f"📊 Kurs: **{rate_text}**\n"
        f"📈 Yo'nalish: **{dir_text}**\n\n"
        f"💰 Hozirgi kurs: **{current:,.0f}** so'm\n\n"
        f"4️⃣ Qaysi narxda xabar bersin?\n\n"
        f"Raqam yozing, masalan: `{example}`",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return STEP_PRICE


async def step_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Narxni tekshirish va takroriy so'rash"""
    try:
        price = float(update.message.text.replace(",", ".").replace(" ", ""))
    except ValueError:
        await update.message.reply_text("❌ Faqat raqam kiriting!\n\nMasalan: `12500`", parse_mode="Markdown")
        return STEP_PRICE
    
    context.user_data["price"] = price
    
    currency = context.user_data["currency"]
    bank_code = context.user_data["bank"]
    rate_type = context.user_data["rate_type"]
    direction = context.user_data["direction"]
    
    bank_info = BANKS.get(bank_code, {})
    bank_name = bank_info.get("name_uz", bank_code)
    
    rate_text = "📥 Sotib olish" if rate_type == "buy" else "📤 Sotish"
    dir_text = "oshganda" if direction == "above" else "tushganda"
    
    keyboard = [
        [InlineKeyboardButton("🔁 Ha, takrorlansin", callback_data="repeat_yes")],
        [InlineKeyboardButton("🔔 Yo'q, bir marta", callback_data="repeat_no")],
        [InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel")]
    ]
    
    await update.message.reply_text(
        f"🔔 **Alert yaratish**\n\n"
        f"💱 **{currency}** - {bank_name}\n"
        f"📊 {rate_text} {dir_text}\n"
        f"💰 Narx: **{price:,.0f}** so'm\n\n"
        f"5️⃣ Alert ishlagandan keyin qayta faollashsinmi?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return STEP_REPEAT


async def step_repeat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Takroriy so'rash va saqlash"""
    query = update.callback_query
    await query.answer()
    
    is_repeating = query.data == "repeat_yes"
    
    user_id = update.effective_user.id
    currency = context.user_data["currency"]
    bank_code = context.user_data["bank"]
    rate_type = context.user_data["rate_type"]
    direction = context.user_data["direction"]
    price = context.user_data["price"]
    
    bank_info = BANKS.get(bank_code, {})
    bank_name = bank_info.get("name_uz", bank_code)
    
    # Saqlash
    async with get_session() as session:
        alert = Alert(
            user_id=user_id,
            bank_code=bank_code,
            currency_code=currency,
            threshold=price,
            direction=direction,
            rate_type=rate_type,
            is_active=True,
            is_triggered=False,
            is_repeating=is_repeating
        )
        session.add(alert)
        await session.commit()
    
    rate_text = "📥 Sotib olish" if rate_type == "buy" else "📤 Sotish"
    dir_text = "oshganda" if direction == "above" else "tushganda"
    dir_emoji = "⬆️" if direction == "above" else "⬇️"
    repeat_text = "🔁 Takroriy" if is_repeating else "🔔 Bir martalik"
    
    context.user_data.clear()
    lang = await get_user_language(user_id)
    
    from handlers.start import get_main_menu_keyboard
    
    await query.edit_message_text(
        f"✅ **Alert yaratildi!**\n\n"
        f"💱 **{currency}**\n"
        f"🏦 {bank_name}\n"
        f"📊 {rate_text} kursi\n"
        f"{dir_emoji} {price:,.0f} so'mdan {dir_text}\n"
        f"{repeat_text}\n\n"
        f"Xabar beraman! ✨",
        reply_markup=get_main_menu_keyboard(lang),
        parse_mode="Markdown"
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Bekor qilish"""
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    
    lang = await get_user_language(update.effective_user.id)
    from handlers.start import get_main_menu_keyboard
    
    await query.edit_message_text(
        "❌ Bekor qilindi.",
        reply_markup=get_main_menu_keyboard(lang)
    )
    return ConversationHandler.END


# ========== Alertlarim ==========

async def my_alerts_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Alertlarim ro'yxati"""
    lang = await get_user_language(update.effective_user.id)
    user_id = update.effective_user.id
    
    message, keyboard = await build_alerts_list(user_id, lang)
    await update.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


async def my_alerts_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Alertlarim menyudan"""
    query = update.callback_query
    await query.answer()
    
    lang = await get_user_language(update.effective_user.id)
    user_id = update.effective_user.id
    
    message, keyboard = await build_alerts_list(user_id, lang)
    await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


async def build_alerts_list(user_id: int, lang: str) -> tuple:
    """Alertlar ro'yxatini yasash"""
    async with get_session() as session:
        result = await session.execute(
            select(Alert).where(Alert.user_id == user_id, Alert.is_active == True)
        )
        alerts = result.scalars().all()
    
    if not alerts:
        message = "📋 **Alertlarim**\n\n📭 Hali alertlar yo'q.\n\n/alert bilan yangi yarating!"
        keyboard = [[InlineKeyboardButton("⬅️ Orqaga", callback_data="main_menu")]]
        return message, keyboard
    
    message = "📋 **Alertlarim**\n\n"
    keyboard = []
    
    for a in alerts:
        bank = BANKS.get(a.bank_code, {}).get("name_uz", a.bank_code)
        rate = "📥" if a.rate_type == "buy" else "📤"
        dir_emoji = "⬆️" if a.direction == "above" else "⬇️"
        
        message += f"{rate} **{a.currency_code}** {dir_emoji} {a.threshold:,.0f}\n   🏦 {bank}\n\n"
        keyboard.append([InlineKeyboardButton(f"🗑️ O'chirish: {a.currency_code} {a.threshold:,.0f}", callback_data=f"del_{a.id}")])
    
    keyboard.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="main_menu")])
    return message, keyboard


async def delete_alert(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Alertni o'chirish"""
    query = update.callback_query
    await query.answer()
    
    alert_id = int(query.data.replace("del_", ""))
    user_id = update.effective_user.id
    lang = await get_user_language(user_id)
    
    async with get_session() as session:
        await session.execute(delete(Alert).where(Alert.id == alert_id, Alert.user_id == user_id))
        await session.commit()
    
    message, keyboard = await build_alerts_list(user_id, lang)
    message = "✅ O'chirildi!\n\n" + message
    await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


def get_alert_conversation_handler() -> ConversationHandler:
    """Conversation handler"""
    return ConversationHandler(
        entry_points=[
            CommandHandler("alert", alert_command),
            CallbackQueryHandler(new_alert_callback, pattern=r"^new_alert$"),
        ],
        states={
            STEP_CURRENCY: [
                CallbackQueryHandler(step_currency, pattern=r"^c_"),
                CallbackQueryHandler(cancel, pattern=r"^cancel$"),
            ],
            STEP_BANK: [
                CallbackQueryHandler(step_bank, pattern=r"^b_"),
                CallbackQueryHandler(cancel, pattern=r"^cancel$"),
            ],
            STEP_ALERT_TYPE: [
                CallbackQueryHandler(step_alert_type, pattern=r"^t_"),
                CallbackQueryHandler(cancel, pattern=r"^cancel$"),
            ],
            STEP_PRICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, step_price),
                CallbackQueryHandler(cancel, pattern=r"^cancel$"),
            ],
            STEP_REPEAT: [
                CallbackQueryHandler(step_repeat, pattern=r"^repeat_"),
                CallbackQueryHandler(cancel, pattern=r"^cancel$"),
            ],
        },
        fallbacks=[CallbackQueryHandler(cancel, pattern=r"^cancel$")],
        per_user=True,
        per_chat=True,
    )


def get_alerts_handlers() -> list:
    """Handlers"""
    return [
        CommandHandler("myalerts", my_alerts_command),
        CallbackQueryHandler(my_alerts_callback, pattern=r"^my_alerts$"),
        CallbackQueryHandler(delete_alert, pattern=r"^del_"),
    ]
