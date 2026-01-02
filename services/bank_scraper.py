"""
Bank Scraper - Real rates from bank websites
"""
import logging
import httpx
from bs4 import BeautifulSoup
from typing import Optional
from config import POPULAR_CURRENCIES

logger = logging.getLogger(__name__)

# Headers to mimic browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "uz,ru;q=0.9,en;q=0.8"
}


async def scrape_nbu() -> list[dict]:
    """NBU (Milliy Bank) kurslarini olish"""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                "https://nbu.uz/exchange-rates/",
                headers=HEADERS
            )
            
            if response.status_code != 200:
                logger.warning(f"NBU scrape failed: {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, 'lxml')
            rates = []
            
            # Find rate table
            table = soup.find('table', class_='exchange-rates')
            if not table:
                # Try alternative selectors
                table = soup.find('table')
            
            if table:
                rows = table.find_all('tr')[1:]  # Skip header
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 3:
                        currency = cols[0].get_text(strip=True).upper()
                        if currency in POPULAR_CURRENCIES:
                            try:
                                buy = float(cols[1].get_text(strip=True).replace(' ', '').replace(',', '.'))
                                sell = float(cols[2].get_text(strip=True).replace(' ', '').replace(',', '.'))
                                rates.append({
                                    "currency_code": currency,
                                    "buy_rate": buy,
                                    "sell_rate": sell
                                })
                            except (ValueError, IndexError):
                                continue
            
            logger.info(f"NBU: fetched {len(rates)} rates")
            return rates
            
    except Exception as e:
        logger.error(f"NBU scrape error: {e}")
        return []


async def scrape_kapitalbank() -> list[dict]:
    """Kapitalbank kurslarini olish"""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                "https://kapitalbank.uz/uz/exchange-rates/",
                headers=HEADERS
            )
            
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'lxml')
            rates = []
            
            # Find exchange rate elements
            items = soup.find_all('div', class_='currency-item') or soup.find_all('tr')
            
            for item in items:
                text = item.get_text()
                for currency in ['USD', 'EUR', 'RUB', 'GBP']:
                    if currency in text:
                        numbers = [s for s in text.split() if s.replace('.', '').replace(',', '').isdigit()]
                        if len(numbers) >= 2:
                            try:
                                rates.append({
                                    "currency_code": currency,
                                    "buy_rate": float(numbers[0].replace(',', '.')),
                                    "sell_rate": float(numbers[1].replace(',', '.'))
                                })
                            except ValueError:
                                continue
            
            logger.info(f"Kapitalbank: fetched {len(rates)} rates")
            return rates
            
    except Exception as e:
        logger.error(f"Kapitalbank scrape error: {e}")
        return []


async def scrape_uzumbank() -> list[dict]:
    """Uzum Bank kurslarini olish"""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Uzum bank API
            response = await client.get(
                "https://uzumbank.uz/api/v1/rates",
                headers=HEADERS
            )
            
            if response.status_code == 200:
                data = response.json()
                rates = []
                for item in data.get('rates', []):
                    if item.get('currency') in POPULAR_CURRENCIES:
                        rates.append({
                            "currency_code": item['currency'],
                            "buy_rate": float(item.get('buy', 0)),
                            "sell_rate": float(item.get('sell', 0))
                        })
                return rates
                
    except Exception as e:
        logger.error(f"Uzum bank error: {e}")
    
    return []


async def get_all_bank_rates() -> dict[str, list[dict]]:
    """Barcha banklardan kurslarni olish"""
    results = {}
    
    # NBU
    nbu_rates = await scrape_nbu()
    if nbu_rates:
        results['nbu'] = nbu_rates
    
    # Kapitalbank
    kapital_rates = await scrape_kapitalbank()
    if kapital_rates:
        results['kapitalbank'] = kapital_rates
    
    # Uzum Bank
    uzum_rates = await scrape_uzumbank()
    if uzum_rates:
        results['uzumbank'] = uzum_rates
    
    return results
