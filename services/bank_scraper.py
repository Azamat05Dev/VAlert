"""
Bank Scraper - Real rates from Uzbekistan banks
Working URLs verified as of January 2026
"""
import logging
import httpx
import re
from bs4 import BeautifulSoup
from typing import Optional, List, Dict
from config import POPULAR_CURRENCIES

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0",
    "Accept": "text/html,application/xhtml+xml,application/json",
    "Accept-Language": "uz,ru;q=0.9,en;q=0.8"
}


async def scrape_nbu() -> List[Dict]:
    """NBU (Milliy Bank) - https://nbu.uz/uz/exchange-rates/"""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                "https://nbu.uz/uz/exchange-rates/",
                headers=HEADERS,
                follow_redirects=True
            )
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'lxml')
            rates = []
            
            # Find table with rates
            table = soup.find('table')
            if table:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    text = row.get_text()
                    
                    for currency in ['USD', 'EUR', 'RUB', 'GBP']:
                        if currency in text:
                            numbers = extract_rates(text)
                            if len(numbers) >= 2:
                                rates.append({
                                    "currency_code": currency,
                                    "buy_rate": numbers[0],
                                    "sell_rate": numbers[1]
                                })
                                break
            
            if rates:
                logger.info(f"NBU: scraped {len(rates)} rates")
            return rates
    except Exception as e:
        logger.debug(f"NBU scrape error: {e}")
        return []


async def scrape_kapitalbank() -> List[Dict]:
    """Kapitalbank - https://kapitalbank.uz/uz/services/exchange-rates/"""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                "https://kapitalbank.uz/uz/services/exchange-rates/",
                headers=HEADERS,
                follow_redirects=True
            )
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'lxml')
            rates = []
            
            # Find rate containers
            for currency in ['USD', 'EUR', 'RUB', 'GBP']:
                text = soup.get_text()
                if currency in text:
                    # Find currency section
                    pattern = rf'{currency}[^\d]*(\d[\d\s,.]+)[^\d]*(\d[\d\s,.]+)'
                    match = re.search(pattern, text)
                    if match:
                        buy = parse_number(match.group(1))
                        sell = parse_number(match.group(2))
                        if buy and sell:
                            rates.append({
                                "currency_code": currency,
                                "buy_rate": buy,
                                "sell_rate": sell
                            })
            
            if rates:
                logger.info(f"Kapitalbank: scraped {len(rates)} rates")
            return rates
    except Exception as e:
        logger.debug(f"Kapitalbank scrape error: {e}")
        return []


async def scrape_asakabank() -> List[Dict]:
    """Asakabank - homepage widget https://asakabank.uz/uz/"""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                "https://asakabank.uz/uz/",
                headers=HEADERS,
                follow_redirects=True
            )
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'lxml')
            rates = []
            
            # Find currency widget
            text = soup.get_text()
            
            for currency in ['USD', 'EUR', 'RUB']:
                pattern = rf'{currency}[^\d]*(\d[\d\s,.]+)[^\d]*(\d[\d\s,.]+)'
                match = re.search(pattern, text)
                if match:
                    buy = parse_number(match.group(1))
                    sell = parse_number(match.group(2))
                    if buy and sell and 1000 < buy < 100000:
                        rates.append({
                            "currency_code": currency,
                            "buy_rate": buy,
                            "sell_rate": sell
                        })
            
            if rates:
                logger.info(f"Asakabank: scraped {len(rates)} rates")
            return rates
    except Exception as e:
        logger.debug(f"Asakabank scrape error: {e}")
        return []


async def scrape_xalqbank() -> List[Dict]:
    """Xalq Banki - header widget https://xb.uz/"""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                "https://xb.uz/",
                headers=HEADERS,
                follow_redirects=True
            )
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'lxml')
            rates = []
            
            text = soup.get_text()
            
            for currency in ['USD', 'EUR', 'RUB']:
                pattern = rf'{currency}[^\d]*(\d[\d\s,.]+)[^\d]*(\d[\d\s,.]+)'
                match = re.search(pattern, text)
                if match:
                    buy = parse_number(match.group(1))
                    sell = parse_number(match.group(2))
                    if buy and sell and 1000 < buy < 100000:
                        rates.append({
                            "currency_code": currency,
                            "buy_rate": buy,
                            "sell_rate": sell
                        })
            
            if rates:
                logger.info(f"Xalq Banki: scraped {len(rates)} rates")
            return rates
    except Exception as e:
        logger.debug(f"Xalq Banki scrape error: {e}")
        return []


async def scrape_ipotekabank() -> List[Dict]:
    """Ipoteka Bank - https://ipotekabank.uz/"""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                "https://ipotekabank.uz/uz/",
                headers=HEADERS,
                follow_redirects=True
            )
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'lxml')
            rates = []
            text = soup.get_text()
            
            for currency in ['USD', 'EUR', 'RUB']:
                pattern = rf'{currency}[^\d]*(\d[\d\s,.]+)[^\d]*(\d[\d\s,.]+)'
                match = re.search(pattern, text)
                if match:
                    buy = parse_number(match.group(1))
                    sell = parse_number(match.group(2))
                    if buy and sell and 1000 < buy < 100000:
                        rates.append({
                            "currency_code": currency,
                            "buy_rate": buy,
                            "sell_rate": sell
                        })
            
            if rates:
                logger.info(f"Ipoteka Bank: scraped {len(rates)} rates")
            return rates
    except Exception as e:
        logger.debug(f"Ipoteka Bank scrape error: {e}")
        return []


async def scrape_agrobank() -> List[Dict]:
    """Agrobank - https://agrobank.uz/"""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                "https://agrobank.uz/uz/",
                headers=HEADERS,
                follow_redirects=True
            )
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'lxml')
            rates = []
            text = soup.get_text()
            
            for currency in ['USD', 'EUR', 'RUB']:
                pattern = rf'{currency}[^\d]*(\d[\d\s,.]+)[^\d]*(\d[\d\s,.]+)'
                match = re.search(pattern, text)
                if match:
                    buy = parse_number(match.group(1))
                    sell = parse_number(match.group(2))
                    if buy and sell and 1000 < buy < 100000:
                        rates.append({
                            "currency_code": currency,
                            "buy_rate": buy,
                            "sell_rate": sell
                        })
            
            if rates:
                logger.info(f"Agrobank: scraped {len(rates)} rates")
            return rates
    except Exception as e:
        logger.debug(f"Agrobank scrape error: {e}")
        return []


async def scrape_aloqabank() -> List[Dict]:
    """Aloqabank - https://aloqabank.uz/"""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                "https://aloqabank.uz/uz/",
                headers=HEADERS,
                follow_redirects=True
            )
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'lxml')
            rates = []
            text = soup.get_text()
            
            for currency in ['USD', 'EUR', 'RUB']:
                pattern = rf'{currency}[^\d]*(\d[\d\s,.]+)[^\d]*(\d[\d\s,.]+)'
                match = re.search(pattern, text)
                if match:
                    buy = parse_number(match.group(1))
                    sell = parse_number(match.group(2))
                    if buy and sell and 1000 < buy < 100000:
                        rates.append({
                            "currency_code": currency,
                            "buy_rate": buy,
                            "sell_rate": sell
                        })
            
            if rates:
                logger.info(f"Aloqabank: scraped {len(rates)} rates")
            return rates
    except Exception as e:
        logger.debug(f"Aloqabank scrape error: {e}")
        return []


async def scrape_hamkorbank() -> List[Dict]:
    """Hamkorbank - https://hamkorbank.uz/"""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                "https://hamkorbank.uz/uz/",
                headers=HEADERS,
                follow_redirects=True
            )
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'lxml')
            rates = []
            text = soup.get_text()
            
            for currency in ['USD', 'EUR', 'RUB']:
                pattern = rf'{currency}[^\d]*(\d[\d\s,.]+)[^\d]*(\d[\d\s,.]+)'
                match = re.search(pattern, text)
                if match:
                    buy = parse_number(match.group(1))
                    sell = parse_number(match.group(2))
                    if buy and sell and 1000 < buy < 100000:
                        rates.append({
                            "currency_code": currency,
                            "buy_rate": buy,
                            "sell_rate": sell
                        })
            
            if rates:
                logger.info(f"Hamkorbank: scraped {len(rates)} rates")
            return rates
    except Exception as e:
        logger.debug(f"Hamkorbank scrape error: {e}")
        return []


def parse_number(text: str) -> Optional[float]:
    """Parse number from text like '12 850' or '12,850' or '12850'"""
    try:
        clean = text.replace(' ', '').replace(',', '.')
        # Handle multiple dots
        if clean.count('.') > 1:
            parts = clean.split('.')
            clean = ''.join(parts[:-1]) + '.' + parts[-1]
        return float(clean)
    except:
        return None


def extract_rates(text: str) -> List[float]:
    """Extract rate numbers from text"""
    pattern = r'\d[\d\s,\.]*\d'
    matches = re.findall(pattern, text)
    
    numbers = []
    for m in matches:
        num = parse_number(m)
        if num and 1000 < num < 100000:  # Valid UZS rate range
            numbers.append(num)
    
    return numbers


# Bank scraper mapping
BANK_SCRAPERS = {
    "nbu": scrape_nbu,
    "kapitalbank": scrape_kapitalbank,
    "asakabank": scrape_asakabank,
    "xalqbank": scrape_xalqbank,
    "ipotekabank": scrape_ipotekabank,
    "agrobank": scrape_agrobank,
    "aloqabank": scrape_aloqabank,
    "hamkorbank": scrape_hamkorbank,
}


async def get_all_bank_rates() -> Dict[str, List[Dict]]:
    """Fetch rates from all available banks"""
    results = {}
    
    for bank_code, scraper in BANK_SCRAPERS.items():
        try:
            rates = await scraper()
            if rates:
                results[bank_code] = rates
        except Exception as e:
            logger.debug(f"{bank_code} failed: {e}")
    
    logger.info(f"Scraped real rates from {len(results)} banks: {list(results.keys())}")
    return results
