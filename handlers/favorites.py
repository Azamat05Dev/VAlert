"""
Favorites Handler - Sevimli banklar
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from sqlalchemy import select, delete

from handlers.common import get_user_language
from database.db import get_session
from database.models import FavoriteBank
from config import BANKS


async def favorites_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sevimli banklar"""
    user_id = update.effective_user.id
    message, keyboard = await build_favorites_view(user_id)
    
    await update.message.reply_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def favorites_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sevimli banklar menyudan"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    message, keyboard = await build_favorites_view(user_id)
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def build_favorites_view(user_id: int) -> tuple:
    """Sevimli banklar ro'yxati"""
    async with get_session() as session:
        result = await session.execute(
            select(FavoriteBank).where(FavoriteBank.user_id == user_id)
        )
        favorites = result.scalars().all()
    
    if not favorites:
        message = "⭐ **Sevimli Banklar**\n\n"
        message += "📭 Hali sevimli banklar yo'q.\n\n"
        message += "➕ Bank qo'shish uchun tugmani bosing."
    else:
        message = "⭐ **Sevimli Banklar**\n\n"
        for fav in favorites:
            bank_info = BANKS.get(fav.bank_code, {})
            bank_name = bank_info.get("name_uz", fav.bank_code)
            message += f"🏦 {bank_name}\n"
    
    keyboard = [
        [InlineKeyboardButton("➕ Bank qo'shish", callback_data="fav_add")],
        [InlineKeyboardButton("🗑️ Bank o'chirish", callback_data="fav_remove")],
        [InlineKeyboardButton("⬅️ Orqaga", callback_data="settings")]
    ]
    
    return message, keyboard


async def fav_add_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Bank qo'shish"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Get existing favorites
    async with get_session() as session:
        result = await session.execute(
            select(FavoriteBank.bank_code).where(FavoriteBank.user_id == user_id)
        )
        existing = [r[0] for r in result.fetchall()]
    
    keyboard = []
    for code, info in BANKS.items():
        if code not in existing:
            keyboard.append([
                InlineKeyboardButton(f"🏦 {info['name_uz']}", callback_data=f"fadd_{code}")
            ])
    
    if not keyboard:
        await query.answer("Barcha banklar qo'shilgan!", show_alert=True)
        return
    
    keyboard.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="favorites")])
    
    await query.edit_message_text(
        "➕ **Bank qo'shish**\n\nTanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def fav_add_bank(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Bankni qo'shish"""
    query = update.callback_query
    await query.answer()
    
    bank_code = query.data.replace("fadd_", "")
    user_id = update.effective_user.id
    
    async with get_session() as session:
        fav = FavoriteBank(user_id=user_id, bank_code=bank_code)
        session.add(fav)
        await session.commit()
    
    bank_name = BANKS.get(bank_code, {}).get("name_uz", bank_code)
    await query.answer(f"✅ {bank_name} qo'shildi!", show_alert=True)
    
    message, keyboard = await build_favorites_view(user_id)
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def fav_remove_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Bank o'chirish menyusi"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    async with get_session() as session:
        result = await session.execute(
            select(FavoriteBank).where(FavoriteBank.user_id == user_id)
        )
        favorites = result.scalars().all()
    
    if not favorites:
        await query.answer("Sevimli banklar yo'q!", show_alert=True)
        return
    
    keyboard = []
    for fav in favorites:
        bank_info = BANKS.get(fav.bank_code, {})
        bank_name = bank_info.get("name_uz", fav.bank_code)
        keyboard.append([
            InlineKeyboardButton(f"🗑️ {bank_name}", callback_data=f"frem_{fav.id}")
        ])
    
    keyboard.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="favorites")])
    
    await query.edit_message_text(
        "🗑️ **Bank o'chirish**\n\nTanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def fav_remove_bank(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Bankni o'chirish"""
    query = update.callback_query
    await query.answer()
    
    fav_id = int(query.data.replace("frem_", ""))
    user_id = update.effective_user.id
    
    async with get_session() as session:
        await session.execute(
            delete(FavoriteBank).where(FavoriteBank.id == fav_id, FavoriteBank.user_id == user_id)
        )
        await session.commit()
    
    await query.answer("✅ O'chirildi!", show_alert=True)
    
    message, keyboard = await build_favorites_view(user_id)
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


def get_favorites_handlers() -> list:
    """Favorites handlers"""
    return [
        CommandHandler("favorites", favorites_command),
        CallbackQueryHandler(favorites_callback, pattern=r"^favorites$"),
        CallbackQueryHandler(fav_add_menu, pattern=r"^fav_add$"),
        CallbackQueryHandler(fav_add_bank, pattern=r"^fadd_"),
        CallbackQueryHandler(fav_remove_menu, pattern=r"^fav_remove$"),
        CallbackQueryHandler(fav_remove_bank, pattern=r"^frem_"),
    ]
