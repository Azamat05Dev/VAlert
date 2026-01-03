"""
Rate Manager Service (All Banks)

Uses REAL bank rates when available from scraper.
Falls back to CBU + spread estimation if scraper fails.
"""
import logging
from datetime import datetime
from typing import Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_session
from database.models import Rate
from services.cbu_fetcher import get_cbu_rates
from services.bank_scraper import get_all_bank_rates
from config import BANKS, POPULAR_CURRENCIES

logger = logging.getLogger(__name__)


async def update_all_rates() -> bool:
    """Fetch rates: REAL from banks when possible, fallback to CBU + spread"""
    try:
        # 1. Fetch CBU rates (always needed as base)
        cbu_rates = await get_cbu_rates()
        
        if not cbu_rates:
            logger.warning("No rates fetched from CBU")
            return False
        
        # Create lookup for CBU rates by currency
        cbu_lookup = {r["currency_code"]: r for r in cbu_rates}
        
        # 2. Try to fetch REAL bank rates from scraper
        real_bank_rates = await get_all_bank_rates()
        real_banks_count = len(real_bank_rates)
        logger.info(f"Fetched real rates from {real_banks_count} banks: {list(real_bank_rates.keys())}")
        
        async with get_session() as session:
            # Clear old rates
            await session.execute(delete(Rate))
            
            # 3. For each bank in config
            for bank_code, bank_info in BANKS.items():
                
                # For each currency from CBU
                for rate_data in cbu_rates:
                    currency_code = rate_data["currency_code"]
                    official_rate = rate_data.get("official_rate", 0)
                    
                    buy_rate = None
                    sell_rate = None
                    is_real = False
                    
                    if bank_info["type"] == "official":
                        # CBU - official rate only
                        pass
                    elif bank_code in real_bank_rates:
                        # REAL bank rate available!
                        bank_rates = real_bank_rates[bank_code]
                        for br in bank_rates:
                            if br["currency_code"] == currency_code:
                                buy_rate = br.get("buy_rate")
                                sell_rate = br.get("sell_rate")
                                is_real = True
                                break
                        
                        # If currency not found in real rates, fallback to spread
                        if buy_rate is None:
                            buy_spread = bank_info.get("buy_spread", 0)
                            sell_spread = bank_info.get("sell_spread", 0)
                            buy_rate = round(official_rate * (1 + buy_spread / 100), 2)
                            sell_rate = round(official_rate * (1 + sell_spread / 100), 2)
                    else:
                        # No real rates - use spread estimation
                        buy_spread = bank_info.get("buy_spread", 0)
                        sell_spread = bank_info.get("sell_spread", 0)
                        buy_rate = round(official_rate * (1 + buy_spread / 100), 2)
                        sell_rate = round(official_rate * (1 + sell_spread / 100), 2)
                    
                    rate = Rate(
                        bank_code=bank_code,
                        currency_code=currency_code,
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
        logger.info(f"Updated {total_rates} rates ({real_banks_count} real, {len(BANKS) - real_banks_count - 1} estimated)")
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
                "bank_name": BANKS.get(r.bank_code, {}).get("name_uz", r.bank_code),
                "buy_rate": r.buy_rate,
                "sell_rate": r.sell_rate,
                "official_rate": r.official_rate,
                "nominal": r.nominal,
                "fetched_at": r.fetched_at
            }
            for r in rates
        ]


async def get_last_update_time() -> Optional[str]:
    """Get the last time rates were updated"""
    from zoneinfo import ZoneInfo
    UZ_TZ = ZoneInfo("Asia/Tashkent")
    
    async with get_session() as session:
        result = await session.execute(
            select(Rate.fetched_at).order_by(Rate.fetched_at.desc()).limit(1)
        )
        fetched_at = result.scalar_one_or_none()
        
        if fetched_at:
            # Convert to Tashkent time
            local_time = fetched_at.replace(tzinfo=ZoneInfo("UTC")).astimezone(UZ_TZ)
            return local_time.strftime("%H:%M")
        return None
