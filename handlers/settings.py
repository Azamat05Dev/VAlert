"""
Settings Handler - Complete with time selection
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, ConversationHandler, MessageHandler, filters
from sqlalchemy import select

from handlers.common import get_user_language
from database.db import get_session
from database.models import User

# States
SET_TIME = 0


async def settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Settings menu with current status"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    async with get_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
    
    daily = "✅" if user and user.daily_notify else "❌"
    weekly = "✅" if user and user.weekly_report else "❌"
    bigchange = "✅" if user and user.big_change_notify else "❌"
    time_text = user.daily_notify_time if user and user.daily_notify_time else "09:00"
    
    keyboard = [
        [InlineKeyboardButton("🌐 Til o'zgartirish", callback_data="language")],
        [InlineKeyboardButton(f"🔔 Kunlik xabarnoma {daily}", callback_data="toggle_daily")],
        [InlineKeyboardButton(f"⏰ Vaqt: {time_text}", callback_data="set_notify_time")],
        [InlineKeyboardButton(f"📊 Haftalik hisobot {weekly}", callback_data="toggle_weekly")],
        [InlineKeyboardButton(f"📈 Katta o'zgarish (>1%) {bigchange}", callback_data="toggle_bigchange")],
        [InlineKeyboardButton("⭐ Sevimli banklar", callback_data="favorites")],
        [InlineKeyboardButton("⬅️ Orqaga", callback_data="main_menu")]
    ]
    
    await query.edit_message_text(
        "⚙️ **Sozlamalar**\n\n"
        f"🔔 Kunlik xabarnoma: {daily}\n"
        f"⏰ Xabar vaqti: **{time_text}**\n"
        f"📊 Haftalik hisobot: {weekly} (Dushanba 10:00)\n"
        f"📈 Katta o'zgarish: {bigchange} (>1% o'zgarganda)",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def toggle_daily(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Toggle daily notification"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    async with get_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if user:
            user.daily_notify = not user.daily_notify
            status = "✅ Yoqildi" if user.daily_notify else "❌ O'chirildi"
            await session.commit()
            await query.answer(f"🔔 Kunlik xabarnoma: {status}", show_alert=True)
    
    await settings_callback(update, context)


async def toggle_weekly(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Toggle weekly report"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    async with get_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if user:
            user.weekly_report = not user.weekly_report
            status = "✅ Yoqildi" if user.weekly_report else "❌ O'chirildi"
            await session.commit()
            await query.answer(f"📊 Haftalik hisobot: {status}", show_alert=True)
    
    await settings_callback(update, context)


async def toggle_bigchange(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Toggle big change notification"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    async with get_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if user:
            user.big_change_notify = not user.big_change_notify
            status = "✅ Yoqildi" if user.big_change_notify else "❌ O'chirildi"
            await session.commit()
            await query.answer(f"📈 Katta o'zgarish: {status}", show_alert=True)
    
    await settings_callback(update, context)


async def set_time_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show time selection"""
    query = update.callback_query
    await query.answer()
    
    # Common times
    times = ["06:00", "07:00", "08:00", "09:00", "10:00", "12:00", "18:00", "20:00"]
    keyboard = []
    row = []
    for t in times:
        row.append(InlineKeyboardButton(f"⏰ {t}", callback_data=f"time_{t}"))
        if len(row) == 4:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("⬅️ Bekor", callback_data="settings")])
    
    await query.edit_message_text(
        "⏰ **Xabar vaqtini tanlang**\n\n"
        "Har kuni qaysi vaqtda kurs xabari kelsin?\n\n"
        "_Yoki o'zingiz yozing (masalan: 07:30)_",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return SET_TIME


async def set_time_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Set time from button"""
    query = update.callback_query
    await query.answer()
    
    time_str = query.data.replace("time_", "")
    user_id = update.effective_user.id
    
    async with get_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user.daily_notify_time = time_str
            user.daily_notify = True  # Auto-enable
            await session.commit()
    
    await query.answer(f"✅ Vaqt o'rnatildi: {time_str}", show_alert=True)
    await settings_callback(update, context)
    return ConversationHandler.END


async def set_time_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Set time from text input"""
    time_str = update.message.text.strip()
    
    # Validate time format
    try:
        parts = time_str.split(":")
        hour = int(parts[0])
        minute = int(parts[1]) if len(parts) > 1 else 0
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError()
        time_str = f"{hour:02d}:{minute:02d}"
    except:
        await update.message.reply_text("❌ Noto'g'ri format. Masalan: 09:00 yoki 18:30")
        return SET_TIME
    
    user_id = update.effective_user.id
    
    async with get_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user.daily_notify_time = time_str
            user.daily_notify = True
            await session.commit()
    
    from handlers.start import get_main_menu_keyboard
    lang = await get_user_language(user_id)
    
    await update.message.reply_text(
        f"✅ Vaqt o'rnatildi: **{time_str}**\n\n"
        f"Har kuni shu vaqtda kurs xabari keladi.",
        reply_markup=get_main_menu_keyboard(lang),
        parse_mode="Markdown"
    )
    return ConversationHandler.END


async def cancel_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel time setting"""
    query = update.callback_query
    await query.answer()
    await settings_callback(update, context)
    return ConversationHandler.END


def get_time_conversation_handler() -> ConversationHandler:
    """Time setting conversation"""
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(set_time_start, pattern=r"^set_notify_time$"),
        ],
        states={
            SET_TIME: [
                CallbackQueryHandler(set_time_button, pattern=r"^time_"),
                CallbackQueryHandler(cancel_time, pattern=r"^settings$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, set_time_text),
            ],
        },
        fallbacks=[CallbackQueryHandler(cancel_time, pattern=r"^settings$")],
        per_user=True,
        per_chat=True,
    )


def get_settings_handlers() -> list:
    """Settings handlers"""
    return [
        CallbackQueryHandler(settings_callback, pattern=r"^settings$"),
        CallbackQueryHandler(toggle_daily, pattern=r"^toggle_daily$"),
        CallbackQueryHandler(toggle_weekly, pattern=r"^toggle_weekly$"),
        CallbackQueryHandler(toggle_bigchange, pattern=r"^toggle_bigchange$"),
    ]
