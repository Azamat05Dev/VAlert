# Currency Alert Bot 💱

O'zbekiston valyuta kurslarini kuzatuvchi Telegram bot.

## Funksiyalar

- 📊 **Kurslar** - Markaziy bank va tijorat banklari kurslari (real+taxminiy)
- 🔔 **Alertlar** - Kurs o'zgarganda xabar olish
- 📈 **Grafiklar** - Kurs tarixi grafigi (7/30 kun)
- 🤖 **Tahlil** - RSI, MACD, SMA teknik tahlil
- 💼 **Portfel** - Valyuta portfelini kuzatish
- 💫 **Aqlli almashtirish** - Eng yaxshi vaqtda xabar olish
- ⚙️ **Sozlamalar** - Kunlik xabar vaqti, til tanlash

## Ma'lumotlar Bazasi

| Muhit | DB | Sozlama |
|-------|----|---------| 
| **Local** | SQLite | `DATABASE_URL=sqlite+aiosqlite:///./data/bot.db` |
| **Docker** | PostgreSQL | `DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/db` |
| **Railway** | PostgreSQL | Railway avtomatik beradi |

## Local O'rnatish

```bash
# 1. Virtual muhit
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# 2. Kutubxonalar
pip install -r requirements.txt

# 3. Konfiguratsiya
cp .env.example .env
# .env faylda BOT_TOKEN ni qo'shing

# 4. Ishga tushirish
python main.py
```

## Docker bilan Ishga Tushirish

```bash
# 1. Environment o'zgaruvchilarini sozlang
export BOT_TOKEN=your_bot_token
export POSTGRES_PASSWORD=secure_password

# 2. Ishga tushirish
docker-compose up -d
```

## Railway Deploy

1. GitHub'ga push qiling
2. [railway.app](https://railway.app) dan repo import qiling
3. PostgreSQL plugin qo'shing
4. Environment variables:
   - `BOT_TOKEN` - @BotFather dan
   - `DATABASE_URL` - Railway avtomatik beradi

## Konfiguratsiya (.env)

```env
# Bot token (@BotFather)
BOT_TOKEN=123456:ABC-DEF...

# Database (local = SQLite, production = PostgreSQL)
DATABASE_URL=sqlite+aiosqlite:///./data/bot.db

# Admin Telegram IDs (vergul bilan)
ADMIN_IDS=1377933746

# Kurs yangilanish intervali (soniya)
UPDATE_INTERVAL=60

# Log darajasi
LOG_LEVEL=INFO
```

## Tuzilma

```
Val_Bot/
├── main.py              # Asosiy fayl
├── config.py            # Sozlamalar
├── handlers/            # Bot handlerlari
│   ├── start.py         # /start, /help
│   ├── rates.py         # Kurslar
│   ├── alerts.py        # Alertlar
│   ├── smart_exchange.py # Aqlli almashtirish
│   ├── analysis.py      # Texnik tahlil
│   └── admin.py         # Admin panel
├── services/            # Servislar
│   ├── scheduler.py     # Scheduler (APScheduler)
│   ├── rate_manager.py  # Kurs boshqaruvi
│   ├── bank_scraper.py  # Real bank kurslari
│   └── cbu_fetcher.py   # CBU API
├── database/            # Ma'lumotlar bazasi
│   ├── db.py            # Ulanish
│   └── models.py        # Modellar
└── locales/             # Tillar (uz, ru)
```

## Tijorat Bank Kurslari

Bot quyidagi manbalardan real kurslarni oladi:
- **NBU** - nbu.uz (scraping)
- **Kapitalbank** - kapitalbank.uz (scraping)
- **Uzum Bank** - API

Boshqa banklar uchun CBU kursi + spread asosida taxminiy kurs hisoblanadi.

## Muallif

Azamat Qalmuratov - [@Azamat05Dev](https://github.com/Azamat05Dev)
