"""
Admin Handler - Complete with broadcast
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, CommandHandler, CallbackQueryHandler,
    ConversationHandler, MessageHandler, filters
)
from sqlalchemy import select, func

from database.db import get_session
from database.models import User, Alert, Rate
from config import ADMIN_IDS

logger = logging.getLogger(__name__)

# Conversation states
BROADCAST_MESSAGE = 0


def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in ADMIN_IDS


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin panel"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Sizda admin huquqi yo'q.")
        return
    
    keyboard = [
        [InlineKeyboardButton("📊 Statistika", callback_data="admin_stats")],
        [InlineKeyboardButton("👥 Foydalanuvchilar", callback_data="admin_users")],
        [InlineKeyboardButton("🔔 Alertlar", callback_data="admin_alerts")],
        [InlineKeyboardButton("📡 Broadcast", callback_data="admin_broadcast")],
        [InlineKeyboardButton("⬅️ Orqaga", callback_data="main_menu")]
    ]
    
    await update.message.reply_text(
        "🔐 **Admin Panel**\n\n"
        "Buyruqlarni tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin panel from menu"""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(update.effective_user.id):
        await query.answer("❌ Admin emas", show_alert=True)
        return
    
    keyboard = [
        [InlineKeyboardButton("📊 Statistika", callback_data="admin_stats")],
        [InlineKeyboardButton("👥 Foydalanuvchilar", callback_data="admin_users")],
        [InlineKeyboardButton("🔔 Alertlar", callback_data="admin_alerts")],
        [InlineKeyboardButton("📡 Broadcast", callback_data="admin_broadcast")],
        [InlineKeyboardButton("⬅️ Orqaga", callback_data="main_menu")]
    ]
    
    await query.edit_message_text(
        "🔐 **Admin Panel**\n\n"
        "Buyruqlarni tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show statistics"""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(update.effective_user.id):
        return
    
    async with get_session() as session:
        users_result = await session.execute(select(func.count(User.id)))
        total_users = users_result.scalar() or 0
        
        active_result = await session.execute(
            select(func.count(func.distinct(Alert.user_id)))
        )
        active_users = active_result.scalar() or 0
        
        alerts_result = await session.execute(select(func.count(Alert.id)))
        total_alerts = alerts_result.scalar() or 0
        
        active_alerts_result = await session.execute(
            select(func.count(Alert.id)).where(Alert.is_active == True)
        )
        active_alerts = active_alerts_result.scalar() or 0
        
        daily_result = await session.execute(
            select(func.count(User.id)).where(User.daily_notify == True)
        )
        daily_users = daily_result.scalar() or 0
    
    message = (
        "📊 **Bot Statistikasi**\n\n"
        f"👥 **Foydalanuvchilar**\n"
        f"   Jami: {total_users}\n"
        f"   Faol: {active_users}\n"
        f"   Kunlik xabar: {daily_users}\n\n"
        f"🔔 **Alertlar**\n"
        f"   Jami: {total_alerts}\n"
        f"   Faol: {active_alerts}"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔄 Yangilash", callback_data="admin_stats")],
        [InlineKeyboardButton("⬅️ Admin", callback_data="admin")]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show recent users"""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(update.effective_user.id):
        return
    
    async with get_session() as session:
        result = await session.execute(
            select(User).order_by(User.created_at.desc()).limit(10)
        )
        users = result.scalars().all()
    
    message = "👥 **Oxirgi 10 foydalanuvchi**\n\n"
    
    for i, user in enumerate(users, 1):
        name = user.first_name or user.username or str(user.id)
        lang = "🇺🇿" if user.language == "uz" else "🇷🇺"
        message += f"{i}. {lang} {name[:15]}\n"
    
    keyboard = [
        [InlineKeyboardButton("🔄 Yangilash", callback_data="admin_users")],
        [InlineKeyboardButton("⬅️ Admin", callback_data="admin")]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def admin_alerts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show alert stats"""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(update.effective_user.id):
        return
    
    async with get_session() as session:
        result = await session.execute(
            select(Alert.currency_code, func.count(Alert.id))
            .group_by(Alert.currency_code)
            .order_by(func.count(Alert.id).desc())
        )
        currency_stats = result.fetchall()
        
        above_result = await session.execute(
            select(func.count(Alert.id)).where(Alert.direction == "above")
        )
        above_count = above_result.scalar() or 0
        
        below_result = await session.execute(
            select(func.count(Alert.id)).where(Alert.direction == "below")
        )
        below_count = below_result.scalar() or 0
    
    message = "🔔 **Alert Statistikasi**\n\n"
    message += "📊 **Valyutalar bo'yicha:**\n"
    for currency, count in currency_stats[:5]:
        message += f"   {currency}: {count}\n"
    
    message += f"\n📈 **Yo'nalish:**\n"
    message += f"   ⬆️ Oshganda: {above_count}\n"
    message += f"   ⬇️ Tushganda: {below_count}"
    
    keyboard = [
        [InlineKeyboardButton("🔄 Yangilash", callback_data="admin_alerts")],
        [InlineKeyboardButton("⬅️ Admin", callback_data="admin")]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start broadcast conversation"""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    
    keyboard = [[InlineKeyboardButton("❌ Bekor qilish", callback_data="broadcast_cancel")]]
    
    await query.edit_message_text(
        "📡 **Broadcast**\n\n"
        "Barcha foydalanuvchilarga yuborish uchun xabar yozing:\n\n"
        "_Markdown formatida yozishingiz mumkin_",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return BROADCAST_MESSAGE


async def broadcast_send(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send broadcast message to all users"""
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    
    message_text = update.message.text
    
    # Get all active users
    async with get_session() as session:
        result = await session.execute(
            select(User).where(User.is_active == True)
        )
        users = result.scalars().all()
    
    success = 0
    failed = 0
    
    status_msg = await update.message.reply_text(
        f"📡 Yuborilmoqda... 0/{len(users)}"
    )
    
    for i, user in enumerate(users):
        try:
            await context.bot.send_message(
                chat_id=user.id,
                text=message_text,
                parse_mode="Markdown"
            )
            success += 1
        except Exception as e:
            logger.warning(f"Broadcast failed for {user.id}: {e}")
            failed += 1
        
        # Update status every 10 users
        if (i + 1) % 10 == 0:
            try:
                await status_msg.edit_text(
                    f"📡 Yuborilmoqda... {i+1}/{len(users)}"
                )
            except:
                pass
    
    from handlers.start import get_main_menu_keyboard
    
    await status_msg.edit_text(
        f"✅ **Broadcast tugadi!**\n\n"
        f"📤 Yuborildi: {success}\n"
        f"❌ Xato: {failed}\n"
        f"👥 Jami: {len(users)}",
        parse_mode="Markdown"
    )
    
    await update.message.reply_text(
        "🏠 Asosiy menyu",
        reply_markup=get_main_menu_keyboard()
    )
    
    return ConversationHandler.END


async def broadcast_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel broadcast"""
    query = update.callback_query
    await query.answer()
    
    await admin_callback(update, context)
    return ConversationHandler.END


def get_broadcast_conversation_handler() -> ConversationHandler:
    """Broadcast conversation handler"""
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(broadcast_start, pattern=r"^admin_broadcast$")
        ],
        states={
            BROADCAST_MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_send),
                CallbackQueryHandler(broadcast_cancel, pattern=r"^broadcast_cancel$"),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(broadcast_cancel, pattern=r"^broadcast_cancel$"),
        ],
        per_user=True,
        per_chat=True,
    )


def get_admin_handlers() -> list:
    """Admin handlers"""
    return [
        CommandHandler("admin", admin_command),
        CallbackQueryHandler(admin_callback, pattern=r"^admin$"),
        CallbackQueryHandler(admin_stats, pattern=r"^admin_stats$"),
        CallbackQueryHandler(admin_users, pattern=r"^admin_users$"),
        CallbackQueryHandler(admin_alerts, pattern=r"^admin_alerts$"),
    ]
