"""
Rates Handler - Display current exchange rates (All Banks)
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from sqlalchemy import select

from handlers.common import get_user_language
from locales.helpers import t
from services.rate_manager import get_rates_by_bank, get_rates_by_currency, get_last_update_time, update_all_rates
from database.db import get_session
from database.models import FavoriteBank
from config import BANKS, POPULAR_CURRENCIES


async def rates_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /rates command - show bank selection"""
    lang = await get_user_language(update.effective_user.id)
    
    keyboard = await build_bank_keyboard(lang, update.effective_user.id)
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    last_update = await get_last_update_time()
    update_text = f"\n🕐 Yangilangan: {last_update}" if last_update else ""
    
    await update.message.reply_text(
        f"📊 **Valyuta kurslari**{update_text}\n\n🏦 Bankni tanlang:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def rates_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show rates menu - bank selection"""
    query = update.callback_query
    await query.answer()
    
    lang = await get_user_language(update.effective_user.id)
    
    keyboard = await build_bank_keyboard(lang, update.effective_user.id)
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    last_update = await get_last_update_time()
    update_text = f"\n🕐 Yangilangan: {last_update}" if last_update else ""
    
    await query.edit_message_text(
        f"📊 **Valyuta kurslari**{update_text}\n\n🏦 Bankni tanlang:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def refresh_rates(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manual rate refresh"""
    query = update.callback_query
    await query.answer("🔄 Kurslar yangilanmoqda...", show_alert=False)
    
    # Update rates
    await update_all_rates()
    
    # Refresh the view
    lang = await get_user_language(update.effective_user.id)
    keyboard = await build_bank_keyboard(lang, update.effective_user.id)
    
    last_update = await get_last_update_time()
    update_text = f"\n🕐 Yangilangan: {last_update}" if last_update else ""
    
    await query.edit_message_text(
        f"📊 **Valyuta kurslari**{update_text}\n\n✅ Kurslar yangilandi!\n\n🏦 Bankni tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def favorites_rates(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show rates for favorite banks"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang = await get_user_language(user_id)
    
    # Get user's favorite banks
    async with get_session() as session:
        result = await session.execute(
            select(FavoriteBank.bank_code).where(FavoriteBank.user_id == user_id)
        )
        favorite_codes = [r[0] for r in result.fetchall()]
    
    if not favorite_codes:
        keyboard = [
            [InlineKeyboardButton("➕ Sevimli qo'shish", callback_data="favorites")],
            [InlineKeyboardButton("⬅️ Orqaga", callback_data="rates")],
            [InlineKeyboardButton("🏠 Menyu", callback_data="main_menu")]
        ]
        await query.edit_message_text(
            "⭐ **Sevimli Banklar**\n\n📭 Hali sevimli bank yo'q.\n\n"
            "Sozlamalar → Sevimli banklar bo'limidan qo'shing.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return
    
    message = "⭐ **Sevimli Banklar Kurslari**\n\n"
    
    for bank_code in favorite_codes:
        bank_info = BANKS.get(bank_code)
        if not bank_info:
            continue
        
        rates = await get_rates_by_bank(bank_code)
        
        emoji = "🏛️" if bank_info["type"] == "official" else "🏦"
        message += f"{emoji} **{bank_info['name_uz']}**\n"
        
        # Show USD, EUR, RUB
        for currency in ["USD", "EUR", "RUB"]:
            for rate in rates:
                if rate["currency_code"] == currency:
                    if bank_info["type"] == "official":
                        official = rate.get("official_rate", 0)
                        message += f"  {currency}: {official:,.0f}\n"
                    else:
                        buy = rate.get("buy_rate", 0)
                        sell = rate.get("sell_rate", 0)
                        message += f"  {currency}: 📥{buy:,.0f} 📤{sell:,.0f}\n"
                    break
        message += "\n"
    
    keyboard = [
        [InlineKeyboardButton("🔄 Yangilash", callback_data="fav_rates")],
        [InlineKeyboardButton("⬅️ Orqaga", callback_data="rates")],
        [InlineKeyboardButton("🏠 Menyu", callback_data="main_menu")]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def build_bank_keyboard(lang: str, user_id: int = None) -> list:
    """Build bank selection keyboard with favorites"""
    keyboard = []
    
    # Check if user has favorites
    has_favorites = False
    if user_id:
        async with get_session() as session:
            result = await session.execute(
                select(FavoriteBank).where(FavoriteBank.user_id == user_id).limit(1)
            )
            has_favorites = result.scalar_one_or_none() is not None
    
    # Favorites button (if user has any)
    if has_favorites:
        keyboard.append([
            InlineKeyboardButton("⭐ Sevimlilar", callback_data="fav_rates")
        ])
    
    # Official bank first
    keyboard.append([
        InlineKeyboardButton("🏛️ Markaziy Bank (CBU)", callback_data="bank_cbu")
    ])
    
    # Commercial banks in pairs
    commercial_banks = [(k, v) for k, v in BANKS.items() if v["type"] == "commercial"]
    row = []
    for bank_code, bank_info in commercial_banks:
        row.append(InlineKeyboardButton(
            f"🏦 {bank_info['name_uz']}", 
            callback_data=f"bank_{bank_code}"
        ))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    # Action buttons
    keyboard.append([
        InlineKeyboardButton("📈 Taqqoslash", callback_data="compare_USD"),
        InlineKeyboardButton("🔄 Yangilash", callback_data="refresh_rates"),
    ])
    
    keyboard.append([
        InlineKeyboardButton("🏠 Menyu", callback_data="main_menu")
    ])
    
    return keyboard


async def view_bank_rates(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show rates for selected bank"""
    query = update.callback_query
    await query.answer()
    
    bank_code = query.data.replace("bank_", "")
    lang = await get_user_language(update.effective_user.id)
    
    bank_info = BANKS.get(bank_code)
    if not bank_info:
        await query.edit_message_text("❌ Bank topilmadi")
        return
    
    rates = await get_rates_by_bank(bank_code)
    
    if not rates:
        message = f"🏦 **{bank_info['name_uz']}**\n\n⏳ Kurslar yuklanmoqda..."
    else:
        emoji = "🏛️" if bank_info["type"] == "official" else "🏦"
        message = f"{emoji} **{bank_info['name_uz']}**\n\n"
        
        # Show popular currencies
        for currency in POPULAR_CURRENCIES:
            for rate in rates:
                if rate["currency_code"] == currency:
                    nominal = rate.get("nominal", 1)
                    
                    if bank_info["type"] == "official":
                        # CBU - show official rate
                        official = rate.get("official_rate", 0)
                        diff = rate.get("diff", 0)
                        diff_emoji = "📈" if diff > 0 else "📉" if diff < 0 else "➖"
                        if nominal == 1:
                            message += f"💱 **{currency}**: {official:,.2f} {diff_emoji}\n"
                        else:
                            message += f"💱 **{nominal} {currency}**: {official:,.2f} {diff_emoji}\n"
                    else:
                        # Commercial - show buy/sell
                        buy = rate.get("buy_rate", 0)
                        sell = rate.get("sell_rate", 0)
                        if nominal == 1:
                            message += f"💱 **{currency}**: 📥{buy:,.0f} | 📤{sell:,.0f}\n"
                        else:
                            message += f"💱 **{nominal} {currency}**: 📥{buy:,.0f} | 📤{sell:,.0f}\n"
                    break
        
        if bank_info["type"] == "commercial":
            message += "\n📥 Sotib olish | 📤 Sotish"
            message += "\n\n_⚠️ Taxminiy kurs (CBU asosida)_"
    
    keyboard = [
        [InlineKeyboardButton("🌍 Barcha valyutalar", callback_data=f"allrates_{bank_code}")],
        [InlineKeyboardButton("⬅️ Orqaga", callback_data="rates")],
        [InlineKeyboardButton("🏠 Menyu", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def view_all_rates(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show all currencies for a bank"""
    query = update.callback_query
    await query.answer()
    
    bank_code = query.data.replace("allrates_", "")
    lang = await get_user_language(update.effective_user.id)
    
    bank_info = BANKS.get(bank_code)
    rates = await get_rates_by_bank(bank_code)
    
    message = f"🌍 **{bank_info['name_uz']}** - Barcha\n\n"
    
    if rates:
        for rate in rates[:25]:  # Limit for message length
            currency = rate["currency_code"]
            nominal = rate.get("nominal", 1)
            
            if bank_info["type"] == "official":
                official = rate.get("official_rate", 0)
                message += f"• {nominal} {currency}: {official:,.2f}\n"
            else:
                buy = rate.get("buy_rate", 0)
                message += f"• {nominal} {currency}: {buy:,.0f}\n"
    
    keyboard = [
        [InlineKeyboardButton("⬅️ Orqaga", callback_data=f"bank_{bank_code}")],
        [InlineKeyboardButton("🏠 Menyu", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def compare_rates(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Compare USD rates across all banks"""
    query = update.callback_query
    await query.answer()
    
    currency = query.data.replace("compare_", "")
    lang = await get_user_language(update.effective_user.id)
    
    rates = await get_rates_by_currency(currency)
    
    message = f"📈 **{currency} taqqoslash**\n\n"
    
    if rates:
        # Sort by buy rate (highest first for selling USD)
        sorted_rates = sorted(rates, key=lambda x: x.get("buy_rate") or x.get("official_rate") or 0, reverse=True)
        
        for rate in sorted_rates:
            bank_code = rate["bank_code"]
            bank_info = BANKS.get(bank_code, {})
            bank_name = bank_info.get("name_uz", bank_code)
            
            if rate.get("official_rate"):
                message += f"🏛️ **{bank_name}**: {rate['official_rate']:,.2f}\n"
            else:
                buy = rate.get("buy_rate", 0)
                sell = rate.get("sell_rate", 0)
                message += f"🏦 **{bank_name}**\n   📥 {buy:,.0f} | 📤 {sell:,.0f}\n"
        
        message += "\n_🏦 Tijorat bank kurslari taxminiy (CBU asosida)_"
    
    keyboard = [
        [InlineKeyboardButton("🔄 Yangilash", callback_data=f"compare_{currency}")],
        [InlineKeyboardButton("⬅️ Orqaga", callback_data="rates")],
        [InlineKeyboardButton("🏠 Menyu", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


def get_rates_handlers() -> list:
    """Get all handlers for rates module"""
    return [
        CommandHandler("rates", rates_command),
        CallbackQueryHandler(rates_callback, pattern=r"^rates$"),
        CallbackQueryHandler(refresh_rates, pattern=r"^refresh_rates$"),
        CallbackQueryHandler(favorites_rates, pattern=r"^fav_rates$"),
        CallbackQueryHandler(view_bank_rates, pattern=r"^bank_"),
        CallbackQueryHandler(view_all_rates, pattern=r"^allrates_"),
        CallbackQueryHandler(compare_rates, pattern=r"^compare_"),
    ]
