"""
Database Connection - Uses config.DATABASE_URL
"""
import os
import logging
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

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
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    db_type = "PostgreSQL" if "postgresql" in DATABASE_URL else "SQLite"
    logger.info(f"Database initialized: {db_type}")


async def close_db():
    """Close database connections"""
    await engine.dispose()
    logger.info("Database connections closed")
