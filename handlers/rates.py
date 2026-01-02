"""
Rates Handler - Display current exchange rates (All Banks)
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

from handlers.common import get_user_language
from locales.helpers import t
from services.rate_manager import get_rates_by_bank, get_rates_by_currency
from config import BANKS, POPULAR_CURRENCIES


async def rates_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /rates command - show bank selection"""
    lang = await get_user_language(update.effective_user.id)
    
    keyboard = build_bank_keyboard(lang)
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "📊 **Valyuta kurslari**\n\n🏦 Bankni tanlang:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def rates_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show rates menu - bank selection"""
    query = update.callback_query
    await query.answer()
    
    lang = await get_user_language(update.effective_user.id)
    
    keyboard = build_bank_keyboard(lang)
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📊 **Valyuta kurslari**\n\n🏦 Bankni tanlang:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


def build_bank_keyboard(lang: str) -> list:
    """Build bank selection keyboard"""
    keyboard = []
    
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
    
    # Compare button
    keyboard.append([
        InlineKeyboardButton("📈 Taqqoslash (USD)", callback_data="compare_USD")
    ])
    
    keyboard.append([InlineKeyboardButton("⬅️ " + t("back", lang), callback_data="main_menu")])
    
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
        message = f"🏦 **{bank_info['name']}**\n\n⏳ Kurslar yuklanmoqda..."
    else:
        emoji = "🏛️" if bank_info["type"] == "official" else "🏦"
        message = f"{emoji} **{bank_info['name']}**\n\n"
        
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
    
    keyboard = [
        [InlineKeyboardButton("🌍 Barcha valyutalar", callback_data=f"allrates_{bank_code}")],
        [InlineKeyboardButton("⬅️ " + t("back", lang), callback_data="rates")]
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
    
    message = f"🌍 **{bank_info['name']}** - Barcha\n\n"
    
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
    
    keyboard = [[InlineKeyboardButton("⬅️ " + t("back", lang), callback_data=f"bank_{bank_code}")]]
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
    
    keyboard = [[InlineKeyboardButton("⬅️ " + t("back", lang), callback_data="rates")]]
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
        CallbackQueryHandler(view_bank_rates, pattern=r"^bank_"),
        CallbackQueryHandler(view_all_rates, pattern=r"^allrates_"),
        CallbackQueryHandler(compare_rates, pattern=r"^compare_"),
    ]
