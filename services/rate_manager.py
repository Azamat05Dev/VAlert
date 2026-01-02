"""
Rate Manager Service (All Banks)

Uses CBU official rate as base and calculates commercial bank rates
with buy/sell spreads.
"""
import logging
from datetime import datetime
from typing import Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_session
from database.models import Rate
from services.cbu_fetcher import get_cbu_rates
from config import BANKS, POPULAR_CURRENCIES

logger = logging.getLogger(__name__)


async def update_all_rates() -> bool:
    """Fetch CBU rates and calculate all bank rates"""
    try:
        # Fetch CBU rates (official)
        cbu_rates = await get_cbu_rates()
        
        if not cbu_rates:
            logger.warning("No rates fetched from CBU")
            return False
        
        async with get_session() as session:
            # Clear old rates
            await session.execute(delete(Rate))
            
            # For each bank
            for bank_code, bank_info in BANKS.items():
                spread_buy = bank_info.get("spread_buy", 0)
                spread_sell = bank_info.get("spread_sell", 0)
                
                # For each currency from CBU
                for rate_data in cbu_rates:
                    official_rate = rate_data.get("official_rate", 0)
                    
                    # Calculate buy/sell for commercial banks
                    if bank_info["type"] == "commercial":
                        buy_rate = round(official_rate * (1 + spread_buy), 2)
                        sell_rate = round(official_rate * (1 + spread_sell), 2)
                    else:
                        buy_rate = None
                        sell_rate = None
                    
                    rate = Rate(
                        bank_code=bank_code,
                        currency_code=rate_data["currency_code"],
                        currency_name=rate_data.get("currency_name", ""),
                        official_rate=official_rate if bank_info["type"] == "official" else None,
                        buy_rate=buy_rate,
                        sell_rate=sell_rate,
                        nominal=rate_data.get("nominal", 1),
                        diff=rate_data.get("diff") if bank_info["type"] == "official" else None,
                        fetched_at=datetime.utcnow()
                    )
                    session.add(rate)
            
            await session.commit()
        
        total_rates = len(cbu_rates) * len(BANKS)
        logger.info(f"Updated {total_rates} rates ({len(BANKS)} banks x {len(cbu_rates)} currencies)")
        return True
        
    except Exception as e:
        logger.error(f"Error updating rates: {e}")
        return False


async def get_rate(bank_code: str, currency_code: str) -> Optional[dict]:
    """Get rate for specific bank and currency"""
    async with get_session() as session:
        result = await session.execute(
            select(Rate).where(
                Rate.bank_code == bank_code,
                Rate.currency_code == currency_code
            )
        )
        rate = result.scalar_one_or_none()
        
        if rate:
            return {
                "currency_code": rate.currency_code,
                "currency_name": rate.currency_name,
                "official_rate": rate.official_rate,
                "buy_rate": rate.buy_rate,
                "sell_rate": rate.sell_rate,
                "nominal": rate.nominal,
                "diff": rate.diff,
                "fetched_at": rate.fetched_at
            }
        return None


async def get_rates_by_bank(bank_code: str) -> list[dict]:
    """Get all rates for a specific bank"""
    async with get_session() as session:
        result = await session.execute(
            select(Rate).where(Rate.bank_code == bank_code)
        )
        rates = result.scalars().all()
        
        return [
            {
                "currency_code": r.currency_code,
                "currency_name": r.currency_name,
                "buy_rate": r.buy_rate,
                "sell_rate": r.sell_rate,
                "official_rate": r.official_rate,
                "nominal": r.nominal,
                "diff": r.diff,
                "fetched_at": r.fetched_at
            }
            for r in rates
        ]


async def get_rates_by_currency(currency_code: str) -> list[dict]:
    """Get rates from all banks for a specific currency"""
    async with get_session() as session:
        result = await session.execute(
            select(Rate).where(Rate.currency_code == currency_code)
        )
        rates = result.scalars().all()
        
        return [
            {
                "bank_code": r.bank_code,
                "bank_name": BANKS.get(r.bank_code, {}).get("name", r.bank_code),
                "buy_rate": r.buy_rate,
                "sell_rate": r.sell_rate,
                "official_rate": r.official_rate,
                "nominal": r.nominal,
                "fetched_at": r.fetched_at
            }
            for r in rates
        ]
