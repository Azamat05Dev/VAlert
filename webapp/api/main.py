"""
VAlert WebApp API - FastAPI Backend
Provides real-time rates, history, and alerts for Telegram WebApp
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

app = FastAPI(title="VAlert API", version="2.0")

# CORS for Telegram WebApp
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data (will be replaced with database queries)
MOCK_RATES = {
    "USD": {"buy": 12680, "sell": 12750, "official": 12720, "change": 0.15},
    "EUR": {"buy": 13820, "sell": 13920, "official": 13870, "change": -0.08},
    "RUB": {"buy": 127.5, "sell": 129.8, "official": 128.2, "change": 0.25},
    "GBP": {"buy": 16100, "sell": 16250, "official": 16180, "change": 0.12},
    "CNY": {"buy": 1745, "sell": 1768, "official": 1752, "change": -0.05},
}

# Models
class RateResponse(BaseModel):
    code: str
    name: str
    buy: float
    sell: float
    official: float
    change: float
    updated_at: str

class HistoryPoint(BaseModel):
    date: str
    rate: float

class AlertCreate(BaseModel):
    currency: str
    direction: str  # "above" or "below"
    threshold: float

class AlertResponse(BaseModel):
    id: int
    currency: str
    direction: str
    threshold: float
    active: bool
    created_at: str


# Currency names
CURRENCY_NAMES = {
    "USD": "AQSh Dollari",
    "EUR": "Yevro",
    "RUB": "Rossiya Rubli",
    "GBP": "Funt Sterling",
    "CNY": "Xitoy Yuani",
}


@app.get("/")
async def root():
    return {"status": "ok", "app": "VAlert API", "version": "2.0"}


@app.get("/rates", response_model=List[RateResponse])
async def get_rates():
    """Get all current exchange rates"""
    now = datetime.now().isoformat()
    rates = []
    
    for code, data in MOCK_RATES.items():
        rates.append(RateResponse(
            code=code,
            name=CURRENCY_NAMES.get(code, code),
            buy=data["buy"],
            sell=data["sell"],
            official=data["official"],
            change=data["change"],
            updated_at=now
        ))
    
    return rates


@app.get("/rates/{currency}", response_model=RateResponse)
async def get_rate(currency: str):
    """Get rate for specific currency"""
    currency = currency.upper()
    
    if currency not in MOCK_RATES:
        raise HTTPException(status_code=404, detail=f"Currency {currency} not found")
    
    data = MOCK_RATES[currency]
    return RateResponse(
        code=currency,
        name=CURRENCY_NAMES.get(currency, currency),
        buy=data["buy"],
        sell=data["sell"],
        official=data["official"],
        change=data["change"],
        updated_at=datetime.now().isoformat()
    )


@app.get("/history/{currency}", response_model=List[HistoryPoint])
async def get_history(currency: str, days: int = 7):
    """Get historical rates for charts"""
    currency = currency.upper()
    
    if currency not in MOCK_RATES:
        raise HTTPException(status_code=404, detail=f"Currency {currency} not found")
    
    # Generate mock history data
    base_rate = MOCK_RATES[currency]["official"]
    history = []
    
    for i in range(days, 0, -1):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        # Simulate small daily changes
        import random
        variation = random.uniform(-0.02, 0.02)
        rate = base_rate * (1 + variation * (days - i) / days)
        history.append(HistoryPoint(date=date, rate=round(rate, 2)))
    
    # Add today
    history.append(HistoryPoint(
        date=datetime.now().strftime("%Y-%m-%d"),
        rate=base_rate
    ))
    
    return history


# Mock alerts storage
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
    # In production, validate against BOT_TOKEN
    # For now, just return success
    return {"valid": True, "user_id": 12345}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
