"""
CBU (Central Bank of Uzbekistan) Rate Fetcher

Fetches official exchange rates from CBU API.
API Documentation: https://cbu.uz/uz/arkhiv-kursov-valyut/
"""
import httpx
import logging
from typing import Optional
from datetime import datetime

from config import CBU_API_URL

logger = logging.getLogger(__name__)


async def fetch_cbu_rates() -> Optional[list[dict]]:
    """
    Fetch current exchange rates from CBU API
    
    Returns:
        List of rate dictionaries or None if error
        
    Example response item:
    {
        "id": 69,
        "Code": "840",
        "Ccy": "USD",
        "CcyNm_RU": "Доллар США",
        "CcyNm_UZ": "AQSH dollari",
        "CcyNm_UZC": "АҚШ доллари",
        "CcyNm_EN": "US Dollar",
        "Nominal": "1",
        "Rate": "12025.33",
        "Diff": "-31.99",
        "Date": "30.12.2025"
    }
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(CBU_API_URL)
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"Successfully fetched {len(data)} rates from CBU")
            return data
            
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error fetching CBU rates: {e}")
        return None
    except httpx.RequestError as e:
        logger.error(f"Request error fetching CBU rates: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching CBU rates: {e}")
        return None


def parse_cbu_rates(raw_data: list[dict]) -> list[dict]:
    """
    Parse CBU API response into standardized rate format
    
    Args:
        raw_data: Raw response from CBU API
        
    Returns:
        List of standardized rate dictionaries
    """
    rates = []
    
    for item in raw_data:
        try:
            rate = {
                "bank_code": "cbu",
                "currency_code": item.get("Ccy", ""),
                "currency_name": item.get("CcyNm_UZ", ""),
                "currency_name_ru": item.get("CcyNm_RU", ""),
                "currency_name_en": item.get("CcyNm_EN", ""),
                "official_rate": float(item.get("Rate", 0)),
                "buy_rate": None,  # CBU doesn't have buy/sell
                "sell_rate": None,
                "nominal": int(item.get("Nominal", 1)),
                "diff": float(item.get("Diff", 0)) if item.get("Diff") else 0,
                "date": item.get("Date", ""),
                "fetched_at": datetime.utcnow().isoformat()
            }
            rates.append(rate)
        except (ValueError, TypeError) as e:
            logger.warning(f"Error parsing rate for {item.get('Ccy')}: {e}")
            continue
    
    return rates


async def get_cbu_rates() -> list[dict]:
    """
    Get parsed CBU rates
    
    Returns:
        List of standardized rate dictionaries
    """
    raw_data = await fetch_cbu_rates()
    if raw_data:
        return parse_cbu_rates(raw_data)
    return []


async def get_cbu_rate_by_currency(currency_code: str) -> Optional[dict]:
    """
    Get CBU rate for specific currency
    
    Args:
        currency_code: Currency code (e.g., "USD", "EUR")
        
    Returns:
        Rate dictionary or None
    """
    rates = await get_cbu_rates()
    for rate in rates:
        if rate["currency_code"].upper() == currency_code.upper():
            return rate
    return None
