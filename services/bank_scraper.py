"""
Bank Scraper - Real rates from all Uzbekistan bank websites
Supports both API and HTML scraping methods
"""
import logging
import httpx
from bs4 import BeautifulSoup
from typing import Optional
from config import POPULAR_CURRENCIES

logger = logging.getLogger(__name__)

# Headers to mimic browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0",
    "Accept": "text/html,application/xhtml+xml,application/json",
    "Accept-Language": "uz,ru;q=0.9,en;q=0.8"
}

# Bank scraper configurations
BANK_CONFIGS = {
    "nbu": {
        "name": "Milliy Bank",
        "url": "https://nbu.uz/exchange-rates/",
        "method": "html",
    },
    "kapitalbank": {
        "name": "Kapitalbank", 
        "url": "https://kapitalbank.uz/uz/exchange-rates/",
        "method": "html",
    },
    "uzumbank": {
        "name": "Uzum Bank",
        "url": "https://uzumbank.uz/api/v1/rates",
        "method": "api",
    },
    "aloqabank": {
        "name": "Aloqabank",
        "url": "https://aloqabank.uz/uz/exchange-rates",
        "method": "html",
    },
    "asakabank": {
        "name": "Asakabank",
        "url": "https://asakabank.uz/uz/currency",
        "method": "html",
    },
    "xalqbank": {
        "name": "Xalq Banki",
        "url": "https://xb.uz/uz/kurs-obmena-valyut",
        "method": "html",
    },
    "ipotekabank": {
        "name": "Ipoteka Bank",
        "url": "https://ipotekabank.uz/uz/exchange-rates",
        "method": "html",
    },
    "agrobank": {
        "name": "Agrobank",
        "url": "https://agrobank.uz/uz/exchange-rates",
        "method": "html",
    },
    "hamkorbank": {
        "name": "Hamkorbank",
        "url": "https://hamkorbank.uz/uz/exchange-rates",
        "method": "html",
    },
    "infinbank": {
        "name": "Infinbank",
        "url": "https://infinbank.com/uz/exchange-rates",
        "method": "html",
    },
    "davr": {
        "name": "Davr Bank",
        "url": "https://davrbank.uz/uz/exchange-rates",
        "method": "html",
    },
    "orientfinans": {
        "name": "Orient Finans",
        "url": "https://orientfinance.uz/uz/valyuta-kurslari",
        "method": "html",
    },
    "anorbank": {
        "name": "Anorbank",
        "url": "https://anorbank.uz/uz/exchange",
        "method": "html",
    },
    "tbc": {
        "name": "TBC Bank",
        "url": "https://tbcbank.uz/uz/exchange-rates",
        "method": "html",
    },
    "ipak": {
        "name": "Ipak Yo'li Bank",
        "url": "https://ipakyulibank.uz/uz/exchange-rates",
        "method": "html",
    },
}


async def scrape_bank(bank_code: str) -> list[dict]:
    """Scrape rates from a single bank"""
    config = BANK_CONFIGS.get(bank_code)
    if not config:
        return []
    
    try:
        if config["method"] == "api":
            return await scrape_api(config["url"], bank_code)
        else:
            return await scrape_html(config["url"], bank_code)
    except Exception as e:
        logger.debug(f"{bank_code} scrape failed: {e}")
        return []


async def scrape_api(url: str, bank_code: str) -> list[dict]:
    """Scrape from JSON API"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=HEADERS)
            if response.status_code != 200:
                return []
            
            data = response.json()
            rates = []
            
            # Handle different API response formats
            items = data if isinstance(data, list) else data.get('rates', data.get('data', []))
            
            for item in items:
                currency = item.get('currency', item.get('code', item.get('Ccy', '')))
                if currency in POPULAR_CURRENCIES:
                    rates.append({
                        "currency_code": currency,
                        "buy_rate": float(item.get('buy', item.get('Rate', 0))),
                        "sell_rate": float(item.get('sell', item.get('Rate', 0)))
                    })
            
            return rates
    except Exception as e:
        logger.debug(f"API scrape error: {e}")
        return []


async def scrape_html(url: str, bank_code: str) -> list[dict]:
    """Scrape from HTML page - universal parser"""
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            response = await client.get(url, headers=HEADERS)
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'lxml')
            rates = []
            
            # Try to find exchange rate table
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 3:
                        text = row.get_text()
                        for currency in POPULAR_CURRENCIES:
                            if currency in text:
                                numbers = extract_numbers(text)
                                if len(numbers) >= 2:
                                    rates.append({
                                        "currency_code": currency,
                                        "buy_rate": numbers[0],
                                        "sell_rate": numbers[1] if len(numbers) > 1 else numbers[0]
                                    })
                                    break
            
            # Also try div-based layouts
            if not rates:
                rate_divs = soup.find_all(['div', 'li'], class_=lambda x: x and ('currency' in str(x).lower() or 'rate' in str(x).lower()))
                for div in rate_divs:
                    text = div.get_text()
                    for currency in POPULAR_CURRENCIES:
                        if currency in text:
                            numbers = extract_numbers(text)
                            if len(numbers) >= 2:
                                rates.append({
                                    "currency_code": currency,
                                    "buy_rate": numbers[0],
                                    "sell_rate": numbers[1]
                                })
                                break
            
            # Remove duplicates
            seen = set()
            unique_rates = []
            for r in rates:
                if r["currency_code"] not in seen:
                    seen.add(r["currency_code"])
                    unique_rates.append(r)
            
            if unique_rates:
                logger.info(f"{bank_code}: scraped {len(unique_rates)} rates")
            
            return unique_rates
            
    except Exception as e:
        logger.debug(f"HTML scrape error for {bank_code}: {e}")
        return []


def extract_numbers(text: str) -> list[float]:
    """Extract numbers from text that look like exchange rates"""
    import re
    # Match numbers like 12 850, 12850, 12,850, 12850.00
    pattern = r'\d[\d\s,\.]*\d'
    matches = re.findall(pattern, text)
    
    numbers = []
    for m in matches:
        try:
            # Clean and convert
            clean = m.replace(' ', '').replace(',', '.')
            # Handle multiple dots (e.g., 12.850.00)
            parts = clean.split('.')
            if len(parts) > 2:
                clean = ''.join(parts[:-1]) + '.' + parts[-1]
            num = float(clean)
            # Exchange rates should be reasonable (100-100000 for UZS)
            if 100 < num < 500000:
                numbers.append(num)
        except:
            continue
    
    return numbers


async def get_all_bank_rates() -> dict[str, list[dict]]:
    """Fetch rates from all configured banks"""
    results = {}
    
    for bank_code in BANK_CONFIGS:
        rates = await scrape_bank(bank_code)
        if rates:
            results[bank_code] = rates
    
    logger.info(f"Scraped rates from {len(results)} banks: {list(results.keys())}")
    return results


async def get_bank_rate(bank_code: str, currency: str) -> Optional[dict]:
    """Get specific currency rate from a bank"""
    rates = await scrape_bank(bank_code)
    for rate in rates:
        if rate["currency_code"] == currency:
            return rate
    return None
