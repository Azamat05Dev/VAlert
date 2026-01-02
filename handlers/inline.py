"""
Inline Handler - Telegram inline mode for quick rate checks
Usage: @botname USD or @botname EUR
"""
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import ContextTypes, InlineQueryHandler
from uuid import uuid4

from services.rate_manager import get_rate, get_rates_by_currency
from config import POPULAR_CURRENCIES, BANKS


async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline queries"""
    query = update.inline_query.query.upper().strip()
    
    results = []
    
    if not query:
        # Show popular currencies
        for currency in POPULAR_CURRENCIES[:5]:
            rate = await get_rate("cbu", currency)
            if rate:
                official = rate.get("official_rate", 0)
                diff = rate.get("diff", 0)
                change = f"+{diff:.0f}" if diff > 0 else f"{diff:.0f}" if diff < 0 else "0"
                
                results.append(
                    InlineQueryResultArticle(
                        id=str(uuid4()),
                        title=f"💱 {currency}: {official:,.0f} so'm",
                        description=f"O'zgarish: {change} | Markaziy Bank",
                        input_message_content=InputTextMessageContent(
                            message_text=(
                                f"💱 **{currency}** kursi\n\n"
                                f"🏛️ Markaziy Bank: **{official:,.0f}** so'm\n"
                                f"📈 O'zgarish: {change}"
                            ),
                            parse_mode="Markdown"
                        )
                    )
                )
    else:
        # Search for specific currency
        if query in POPULAR_CURRENCIES:
            # Get all bank rates
            rates = await get_rates_by_currency(query)
            
            if rates:
                # Official CBU rate
                cbu_rate = next((r for r in rates if r["bank_code"] == "cbu"), None)
                if cbu_rate:
                    official = cbu_rate.get("official_rate", 0)
                    results.append(
                        InlineQueryResultArticle(
                            id=str(uuid4()),
                            title=f"🏛️ {query} - Markaziy Bank",
                            description=f"Rasmiy kurs: {official:,.0f} so'm",
                            input_message_content=InputTextMessageContent(
                                message_text=(
                                    f"🏛️ **{query}** - Markaziy Bank\n\n"
                                    f"💰 Rasmiy kurs: **{official:,.0f}** so'm"
                                ),
                                parse_mode="Markdown"
                            )
                        )
                    )
                
                # Best buy/sell rates
                buy_rates = [(r, r.get("buy_rate") or r.get("official_rate") or 0) for r in rates]
                sell_rates = [(r, r.get("sell_rate") or r.get("official_rate") or 0) for r in rates]
                
                best_buy = max(buy_rates, key=lambda x: x[1])
                best_sell = min(sell_rates, key=lambda x: x[1])
                
                best_buy_bank = BANKS.get(best_buy[0]["bank_code"], {}).get("name_uz", "")
                best_sell_bank = BANKS.get(best_sell[0]["bank_code"], {}).get("name_uz", "")
                
                results.append(
                    InlineQueryResultArticle(
                        id=str(uuid4()),
                        title=f"🏆 {query} - Eng yaxshi kurslar",
                        description=f"Sotib olish: {best_buy[1]:,.0f} | Sotish: {best_sell[1]:,.0f}",
                        input_message_content=InputTextMessageContent(
                            message_text=(
                                f"🏆 **{query}** - Eng yaxshi kurslar\n\n"
                                f"📥 Sotib olish: **{best_buy[1]:,.0f}** so'm\n"
                                f"   🏦 {best_buy_bank}\n\n"
                                f"📤 Sotish: **{best_sell[1]:,.0f}** so'm\n"
                                f"   🏦 {best_sell_bank}"
                            ),
                            parse_mode="Markdown"
                        )
                    )
                )
                
                # Compare top 3 banks
                sorted_buy = sorted(buy_rates, key=lambda x: x[1], reverse=True)[:3]
                compare_text = f"📊 **{query}** - Top 3 bank\n\n"
                for i, (r, rate) in enumerate(sorted_buy, 1):
                    bank = BANKS.get(r["bank_code"], {}).get("name_uz", "")[:15]
                    compare_text += f"{i}. {bank}: {rate:,.0f}\n"
                
                results.append(
                    InlineQueryResultArticle(
                        id=str(uuid4()),
                        title=f"📊 {query} - Taqqoslash",
                        description="Top 3 bank kurslari",
                        input_message_content=InputTextMessageContent(
                            message_text=compare_text,
                            parse_mode="Markdown"
                        )
                    )
                )
        else:
            # No results
            results.append(
                InlineQueryResultArticle(
                    id=str(uuid4()),
                    title="❌ Valyuta topilmadi",
                    description="USD, EUR, RUB, GBP yozing",
                    input_message_content=InputTextMessageContent(
                        message_text="❌ Valyuta topilmadi. USD, EUR, RUB, GBP yozing."
                    )
                )
            )
    
    await update.inline_query.answer(results, cache_time=60)


def get_inline_handler() -> InlineQueryHandler:
    """Get inline handler"""
    return InlineQueryHandler(inline_query)
