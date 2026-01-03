"""
Database Connection - Uses config.DATABASE_URL
With automatic migration for new columns
"""
import os
import logging
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text

from database.models import Base
from config import DATABASE_URL

logger = logging.getLogger(__name__)

# Create engine based on database type
if "sqlite" in DATABASE_URL:
    # Create data directory for SQLite
    os.makedirs("data", exist_ok=True)
    engine = create_async_engine(DATABASE_URL, echo=False)
else:
    # PostgreSQL settings
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True
    )

# Session maker
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@asynccontextmanager
async def get_session():
    """Get database session"""
    session = async_session()
    try:
        yield session
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def init_db():
    """Initialize database tables and run migrations"""
    async with engine.begin() as conn:
        # Create tables
        await conn.run_sync(Base.metadata.create_all)
    
    # Run migrations for existing tables
    await run_migrations()
    
    db_type = "PostgreSQL" if "postgresql" in DATABASE_URL else "SQLite"
    logger.info(f"Database initialized: {db_type}")


async def run_migrations():
    """Add missing columns to existing tables"""
    migrations = [
        # Alert table - is_paused column
        ("alerts", "is_paused", "BOOLEAN DEFAULT FALSE"),
        # SmartExchange table - snooze_until column
        ("smart_exchanges", "snooze_until", "TIMESTAMP"),
    ]
    
    async with engine.begin() as conn:
        for table, column, col_type in migrations:
            try:
                # Check if column exists
                if "postgresql" in DATABASE_URL:
                    check_sql = text(f"""
                        SELECT column_name FROM information_schema.columns 
                        WHERE table_name = '{table}' AND column_name = '{column}'
                    """)
                    result = await conn.execute(check_sql)
                    exists = result.fetchone() is not None
                    
                    if not exists:
                        # Add column
                        add_sql = text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
                        await conn.execute(add_sql)
                        logger.info(f"Migration: added {table}.{column}")
                else:
                    # SQLite - try to add, ignore if exists
                    try:
                        add_sql = text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
                        await conn.execute(add_sql)
                        logger.info(f"Migration: added {table}.{column}")
                    except Exception:
                        pass  # Column already exists
            except Exception as e:
                logger.debug(f"Migration skip {table}.{column}: {e}")


async def close_db():
    """Close database connections"""
    await engine.dispose()
    logger.info("Database connections closed")
