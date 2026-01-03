"""
Bot Configuration - Single Source of Truth
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Bot settings
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Database - single standard format
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/bot.db")

# Convert postgres:// to postgresql+asyncpg:// for async
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql://") and "asyncpg" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Admin IDs
ADMIN_IDS_STR = os.getenv("ADMIN_IDS", "1377933746")
ADMIN_IDS = [int(x) for x in ADMIN_IDS_STR.split(",") if x.strip()]

# Rate update interval (seconds)
UPDATE_INTERVAL = int(os.getenv("UPDATE_INTERVAL", "60"))

# CBU API
CBU_API_URL = "https://cbu.uz/uz/arkhiv-kursov-valyut/json/"

# Popular currencies
POPULAR_CURRENCIES = ["USD", "EUR", "RUB", "GBP", "CHF", "JPY", "CNY", "KRW", "TRY", "KZT"]

# Banks with spreads (percentage from CBU rate)
BANKS = {
    "cbu": {
        "name_uz": "Markaziy Bank",
        "name_ru": "Центральный Банк",
        "type": "official",
        "buy_spread": 0,
        "sell_spread": 0,
    },
    "nbu": {
        "name_uz": "Milliy Bank",
        "name_ru": "Национальный Банк",
        "type": "commercial",
        "buy_spread": -0.5,
        "sell_spread": 0.8,
    },
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
    "asakabank": {
        "name_uz": "Asakabank",
        "name_ru": "Асакабанк",
        "type": "commercial",
        "buy_spread": -0.6,
        "sell_spread": 0.9,
    },
    "ipotekabank": {
        "name_uz": "Ipoteka Bank",
        "name_ru": "Ипотека Банк",
        "type": "commercial",
        "buy_spread": -0.5,
        "sell_spread": 0.8,
    },
    "xalqbank": {
        "name_uz": "Xalq Banki",
        "name_ru": "Халк Банк",
        "type": "commercial",
        "buy_spread": -0.7,
        "sell_spread": 1.0,
    },
    "aloqabank": {
        "name_uz": "Aloqabank",
        "name_ru": "Алокабанк",
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
