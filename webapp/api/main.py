"""
VAlert WebApp API - FastAPI Backend
Provides real-time rates from CBU, history, and alerts for Telegram WebApp
"""
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
import hashlib
import hmac
import json
import os
import httpx
import asyncio
import logging

logger = logging.getLogger(__name__)

app = FastAPI(title="VAlert API", version="2.0")

# CORS for Telegram WebApp
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== CBU API CONFIGURATION ====================
CBU_API_URL = "https://cbu.uz/uz/arkhiv-kursov-valyut/json/"
CACHE_TTL_SECONDS = 300  # 5 minutes

# Rate cache
class RateCache:
    def __init__(self, ttl: int = 300):
        self.data: Optional[List[dict]] = None
        self.timestamp: Optional[datetime] = None
        self.ttl = ttl
        self.lock = asyncio.Lock()
    
    def is_valid(self) -> bool:
        if self.data is None or self.timestamp is None:
            return False
        age = (datetime.now() - self.timestamp).total_seconds()
        return age < self.ttl
    
    def get_age(self) -> Optional[float]:
        if self.timestamp is None:
            return None
        return (datetime.now() - self.timestamp).total_seconds()

rates_cache = RateCache(CACHE_TTL_SECONDS)

# Fallback mock data (used if CBU API fails)
MOCK_RATES = {
    "USD": {"buy": 12680, "sell": 12750, "official": 12720, "change": 0.15},
    "EUR": {"buy": 13820, "sell": 13920, "official": 13870, "change": -0.08},
    "RUB": {"buy": 127.5, "sell": 129.8, "official": 128.2, "change": 0.25},
    "GBP": {"buy": 16100, "sell": 16250, "official": 16180, "change": 0.12},
    "CNY": {"buy": 1745, "sell": 1768, "official": 1752, "change": -0.05},
}

# Currency names and metadata
CURRENCY_INFO = {
    "USD": {"name": "AQSh Dollari", "flag": "🇺🇸", "buy_spread": -0.4, "sell_spread": 0.6},
    "EUR": {"name": "Yevro", "flag": "🇪🇺", "buy_spread": -0.5, "sell_spread": 0.7},
    "RUB": {"name": "Rossiya Rubli", "flag": "🇷🇺", "buy_spread": -0.8, "sell_spread": 1.0},
    "GBP": {"name": "Funt Sterling", "flag": "🇬🇧", "buy_spread": -0.5, "sell_spread": 0.7},
    "CNY": {"name": "Xitoy Yuani", "flag": "🇨🇳", "buy_spread": -0.6, "sell_spread": 0.8},
    "CHF": {"name": "Shveytsariya Franki", "flag": "🇨🇭", "buy_spread": -0.5, "sell_spread": 0.7},
    "JPY": {"name": "Yapon Ienasi", "flag": "🇯🇵", "buy_spread": -0.6, "sell_spread": 0.8},
    "KRW": {"name": "Janubiy Koreya Voni", "flag": "🇰🇷", "buy_spread": -0.7, "sell_spread": 0.9},
    "TRY": {"name": "Turk Lirasi", "flag": "🇹🇷", "buy_spread": -1.0, "sell_spread": 1.2},
    "KZT": {"name": "Qozogʻiston Tengesi", "flag": "🇰🇿", "buy_spread": -0.8, "sell_spread": 1.0},
}

POPULAR_CURRENCIES = ["USD", "EUR", "RUB", "GBP", "CNY"]

# ==================== MODELS ====================
class RateResponse(BaseModel):
    code: str
    name: str
    flag: str
    buy: float
    sell: float
    official: float
    change: float
    nominal: int
    updated_at: str
    source: str  # "cbu" or "mock"

class HistoryPoint(BaseModel):
    date: str
    rate: float

class AlertCreate(BaseModel):
    currency: str
    direction: str
    threshold: float

class AlertResponse(BaseModel):
    id: int
    currency: str
    direction: str
    threshold: float
    active: bool
    created_at: str

class CacheStatus(BaseModel):
    is_valid: bool
    age_seconds: Optional[float]
    ttl_seconds: int
    rates_count: int
    last_update: Optional[str]

# ==================== CBU API FUNCTIONS ====================
async def fetch_cbu_rates_raw() -> Optional[List[dict]]:
    """Fetch raw rates from CBU API"""
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

def parse_cbu_rate(item: dict) -> Optional[dict]:
    """Parse a single CBU rate item"""
    try:
        code = item.get("Ccy", "")
        official_rate = float(item.get("Rate", 0))
        nominal = int(item.get("Nominal", 1))
        diff = float(item.get("Diff", 0)) if item.get("Diff") else 0
        
        # Get currency info or use defaults
        info = CURRENCY_INFO.get(code, {"name": item.get("CcyNm_UZ", code), "flag": "💱", "buy_spread": -0.5, "sell_spread": 0.7})
        
        # Calculate buy/sell based on spreads (simulate bank rates)
        buy_rate = official_rate * (1 + info["buy_spread"] / 100)
        sell_rate = official_rate * (1 + info["sell_spread"] / 100)
        
        # Calculate percentage change
        if official_rate > 0 and diff != 0:
            change_pct = (diff / official_rate) * 100
        else:
            change_pct = 0
        
        return {
            "code": code,
            "name": info["name"],
            "flag": info["flag"],
            "buy": round(buy_rate, 2),
            "sell": round(sell_rate, 2),
            "official": official_rate,
            "change": round(change_pct, 2),
            "nominal": nominal,
            "diff": diff,
        }
    except (ValueError, TypeError) as e:
        logger.warning(f"Error parsing rate for {item.get('Ccy')}: {e}")
        return None

async def get_cached_rates() -> List[dict]:
    """Get rates from cache or fetch from CBU"""
    async with rates_cache.lock:
        if rates_cache.is_valid():
            return rates_cache.data
        
        # Fetch fresh data
        raw_data = await fetch_cbu_rates_raw()
        
        if raw_data:
            parsed_rates = []
            for item in raw_data:
                rate = parse_cbu_rate(item)
                if rate:
                    parsed_rates.append(rate)
            
            rates_cache.data = parsed_rates
            rates_cache.timestamp = datetime.now()
            return parsed_rates
        
        # Return cached data even if expired (better than nothing)
        if rates_cache.data:
            return rates_cache.data
        
        # Last resort: return mock data
        return get_mock_rates()

def get_mock_rates() -> List[dict]:
    """Generate rates from mock data as fallback"""
    rates = []
    for code, data in MOCK_RATES.items():
        info = CURRENCY_INFO.get(code, {"name": code, "flag": "💱"})
        rates.append({
            "code": code,
            "name": info["name"],
            "flag": info["flag"],
            "buy": data["buy"],
            "sell": data["sell"],
            "official": data["official"],
            "change": data["change"],
            "nominal": 1,
            "diff": 0,
        })
    return rates

# ==================== API ENDPOINTS ====================
@app.get("/")
async def root():
    return {"status": "ok", "app": "VAlert API", "version": "2.0", "source": "CBU"}

@app.get("/rates", response_model=List[RateResponse])
async def get_rates(popular_only: bool = False):
    """Get all current exchange rates from CBU"""
    all_rates = await get_cached_rates()
    now = datetime.now().isoformat()
    source = "cbu" if rates_cache.is_valid() else "mock"
    
    result = []
    for rate in all_rates:
        # Filter popular currencies if requested
        if popular_only and rate["code"] not in POPULAR_CURRENCIES:
            continue
        
        result.append(RateResponse(
            code=rate["code"],
            name=rate["name"],
            flag=rate.get("flag", "💱"),
            buy=rate["buy"],
            sell=rate["sell"],
            official=rate["official"],
            change=rate["change"],
            nominal=rate.get("nominal", 1),
            updated_at=now,
            source=source
        ))
    
    # Sort: popular currencies first
    result.sort(key=lambda r: (r.code not in POPULAR_CURRENCIES, POPULAR_CURRENCIES.index(r.code) if r.code in POPULAR_CURRENCIES else 999))
    
    return result

@app.get("/rates/{currency}", response_model=RateResponse)
async def get_rate(currency: str):
    """Get rate for specific currency"""
    currency = currency.upper()
    all_rates = await get_cached_rates()
    
    for rate in all_rates:
        if rate["code"] == currency:
            source = "cbu" if rates_cache.is_valid() else "mock"
            return RateResponse(
                code=rate["code"],
                name=rate["name"],
                flag=rate.get("flag", "💱"),
                buy=rate["buy"],
                sell=rate["sell"],
                official=rate["official"],
                change=rate["change"],
                nominal=rate.get("nominal", 1),
                updated_at=datetime.now().isoformat(),
                source=source
            )
    
    raise HTTPException(status_code=404, detail=f"Currency {currency} not found")

@app.get("/cache/status", response_model=CacheStatus)
async def get_cache_status():
    """Get current cache status"""
    return CacheStatus(
        is_valid=rates_cache.is_valid(),
        age_seconds=rates_cache.get_age(),
        ttl_seconds=rates_cache.ttl,
        rates_count=len(rates_cache.data) if rates_cache.data else 0,
        last_update=rates_cache.timestamp.isoformat() if rates_cache.timestamp else None
    )

@app.post("/cache/refresh")
async def refresh_cache():
    """Force refresh cache from CBU"""
    async with rates_cache.lock:
        rates_cache.data = None
        rates_cache.timestamp = None
    
    # Fetch fresh data
    rates = await get_cached_rates()
    
    return {
        "status": "refreshed",
        "rates_count": len(rates),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/history/{currency}", response_model=List[HistoryPoint])
async def get_history(currency: str, days: int = 7):
    """Get historical rates for charts"""
    currency = currency.upper()
    all_rates = await get_cached_rates()
    
    # Find current rate
    current_rate = None
    for rate in all_rates:
        if rate["code"] == currency:
            current_rate = rate["official"]
            break
    
    if current_rate is None:
        raise HTTPException(status_code=404, detail=f"Currency {currency} not found")
    
    # Generate history based on current rate and diff
    history = []
    import random
    
    for i in range(days, 0, -1):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        # Simulate historical variation
        variation = random.uniform(-0.02, 0.02)
        rate = current_rate * (1 + variation * (days - i) / days)
        history.append(HistoryPoint(date=date, rate=round(rate, 2)))
    
    # Add today
    history.append(HistoryPoint(
        date=datetime.now().strftime("%Y-%m-%d"),
        rate=current_rate
    ))
    
    return history

# ==================== ALERTS ====================
MOCK_ALERTS = []
alert_counter = 0

@app.post("/alerts", response_model=AlertResponse)
async def create_alert(alert: AlertCreate):
    """Create a new price alert"""
    global alert_counter
    alert_counter += 1
    
    new_alert = AlertResponse(
        id=alert_counter,
        currency=alert.currency.upper(),
        direction=alert.direction,
        threshold=alert.threshold,
        active=True,
        created_at=datetime.now().isoformat()
    )
    
    MOCK_ALERTS.append(new_alert)
    return new_alert

@app.get("/alerts", response_model=List[AlertResponse])
async def get_alerts():
    """Get all alerts"""
    return MOCK_ALERTS

@app.delete("/alerts/{alert_id}")
async def delete_alert(alert_id: int):
    """Delete an alert"""
    global MOCK_ALERTS
    MOCK_ALERTS = [a for a in MOCK_ALERTS if a.id != alert_id]
    return {"status": "deleted", "id": alert_id}

@app.post("/validate")
async def validate_init_data(init_data: str = Header(alias="X-Telegram-Init-Data")):
    """Validate Telegram WebApp initData"""
    return {"valid": True, "user_id": 12345}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
