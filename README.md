# Currency Alert Bot

O'zbekiston valyuta kurslarini kuzatuvchi Telegram bot.

## Funksiyalar

- 📊 **Kurslar** - Markaziy bank va tijorat banklari kurslari
- 🔔 **Alertlar** - Kurs o'zgarganda xabar olish
- 📈 **Grafiklar** - Kurs tarixi grafigi (7/30 kun)
- 🤖 **Tahlil** - RSI, MACD, AI prognoz
- 💼 **Portfel** - Valyuta portfelini kuzatish
- ⚙️ **Sozlamalar** - Kunlik xabar vaqti, sevimli banklar

## O'rnatish

```bash
# Virtual muhit
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Kutubxonalar
pip install -r requirements.txt

# .env fayl
cp .env.example .env
# BOT_TOKEN ni qo'shing
```

## Ishga tushirish

```bash
python main.py
```

## Sozlamalar

`.env` fayl:

```env
BOT_TOKEN=your_bot_token
DATABASE_URL=sqlite+aiosqlite:///./data/bot.db
ADMIN_IDS=1377933746
LOG_LEVEL=INFO
```

PostgreSQL uchun:
```env
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
```

## Cloud Hosting

### Railway
1. GitHub'ga push qiling
2. [railway.app](https://railway.app) dan import qiling
3. Environment variables qo'shing

### Docker
```bash
docker-compose up -d
```

## Tuzilma

```
Val_Bot/
├── main.py              # Asosiy fayl
├── config.py            # Sozlamalar
├── handlers/            # Bot handlerlari
│   ├── start.py         # /start
│   ├── rates.py         # Kurslar
│   ├── alerts.py        # Alertlar
│   ├── charts.py        # Grafiklar
│   ├── analysis.py      # Tahlil
│   └── admin.py         # Admin panel
├── services/            # Servislar
│   ├── scheduler.py     # Scheduler
│   ├── rate_manager.py  # Kurs boshqaruvi
│   └── chart_service.py # Grafik yaratish
├── database/            # Ma'lumotlar bazasi
│   ├── db.py            # Ulanish
│   └── models.py        # Modellar
└── locales/             # Tillar
    ├── uz.py            # O'zbek
    └── ru.py            # Rus
```

## Muallif

Azamat Qalmuratov
