"""
Currency Alert Bot Configuration - All Uzbekistan Banks
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Bot configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/bot.db")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x]

# Rate update interval (seconds)
UPDATE_INTERVAL = int(os.getenv("UPDATE_INTERVAL", 60))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Timezone (Tashkent)
TIMEZONE = "Asia/Tashkent"

# CBU API
CBU_API_URL = "https://cbu.uz/uz/arkhiv-kursov-valyut/json/"

# Popular currencies
POPULAR_CURRENCIES = ["USD", "EUR", "RUB", "GBP", "CHF", "JPY", "CNY", "KRW", "TRY", "KZT"]

# ========== ALL UZBEKISTAN BANKS ==========
# type: "official" = CBU, "commercial" = tijorat bank
# Spreads are fallback values used if scraper fails

BANKS = {
    # Markaziy Bank (rasmiy)
    "cbu": {
        "name_uz": "Markaziy Bank",
        "name_ru": "Центральный Банк",
        "type": "official",
        "buy_spread": 0,
        "sell_spread": 0,
    },
    
    # ===== DAVLAT BANKLARI =====
    "nbu": {
        "name_uz": "Milliy Bank (NBU)",
        "name_ru": "Национальный Банк",
        "type": "commercial",
        "buy_spread": -0.5,
        "sell_spread": 0.8,
    },
    "asakabank": {
        "name_uz": "Asakabank",
        "name_ru": "Асакабанк",
        "type": "commercial",
        "buy_spread": -0.6,
        "sell_spread": 0.9,
    },
    "xalqbank": {
        "name_uz": "Xalq Banki",
        "name_ru": "Халк Банк",
        "type": "commercial",
        "buy_spread": -0.7,
        "sell_spread": 1.0,
    },
    "ipotekabank": {
        "name_uz": "Ipoteka Bank",
        "name_ru": "Ипотека Банк",
        "type": "commercial",
        "buy_spread": -0.5,
        "sell_spread": 0.8,
    },
    "agrobank": {
        "name_uz": "Agrobank",
        "name_ru": "Агробанк",
        "type": "commercial",
        "buy_spread": -0.6,
        "sell_spread": 0.9,
    },
    "aloqabank": {
        "name_uz": "Aloqabank",
        "name_ru": "Алокабанк",
        "type": "commercial",
        "buy_spread": -0.5,
        "sell_spread": 0.8,
    },
    
    # ===== TIJORAT BANKLARI =====
    "kapitalbank": {
        "name_uz": "Kapitalbank",
        "name_ru": "Капиталбанк",
        "type": "commercial",
        "buy_spread": -0.4,
        "sell_spread": 0.7,
    },
    "uzumbank": {
        "name_uz": "Uzum Bank",
        "name_ru": "Узум Банк",
        "type": "commercial",
        "buy_spread": -0.3,
        "sell_spread": 0.6,
    },
    "hamkorbank": {
        "name_uz": "Hamkorbank",
        "name_ru": "Хамкорбанк",
        "type": "commercial",
        "buy_spread": -0.5,
        "sell_spread": 0.8,
    },
    "infinbank": {
        "name_uz": "Infinbank",
        "name_ru": "Инфинбанк",
        "type": "commercial",
        "buy_spread": -0.4,
        "sell_spread": 0.7,
    },
    "davr": {
        "name_uz": "Davr Bank",
        "name_ru": "Давр Банк",
        "type": "commercial",
        "buy_spread": -0.5,
        "sell_spread": 0.8,
    },
    "orientfinans": {
        "name_uz": "Orient Finans",
        "name_ru": "Ориент Финанс",
        "type": "commercial",
        "buy_spread": -0.4,
        "sell_spread": 0.7,
    },
    "anorbank": {
        "name_uz": "Anorbank",
        "name_ru": "Анорбанк",
        "type": "commercial",
        "buy_spread": -0.3,
        "sell_spread": 0.6,
    },
    "tbc": {
        "name_uz": "TBC Bank",
        "name_ru": "ТБС Банк",
        "type": "commercial",
        "buy_spread": -0.4,
        "sell_spread": 0.7,
    },
    "ipak": {
        "name_uz": "Ipak Yo'li Bank",
        "name_ru": "Ипак Йули Банк",
        "type": "commercial",
        "buy_spread": -0.5,
        "sell_spread": 0.8,
    },
    "trustbank": {
        "name_uz": "Trustbank",
        "name_ru": "Трастбанк",
        "type": "commercial",
        "buy_spread": -0.4,
        "sell_spread": 0.7,
    },
}
