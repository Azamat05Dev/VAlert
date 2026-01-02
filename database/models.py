"""
Database Models for Currency Alert Bot - Extended
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all models"""
    pass


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    language: Mapped[str] = mapped_column(String(5), default="uz")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Notification settings
    daily_notify: Mapped[bool] = mapped_column(Boolean, default=False)
    daily_notify_time: Mapped[Optional[str]] = mapped_column(String(5), nullable=True, default="09:00")
    weekly_report: Mapped[bool] = mapped_column(Boolean, default=False)
    big_change_notify: Mapped[bool] = mapped_column(Boolean, default=True)  # >1% change
    last_daily_sent: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    alerts: Mapped[list["Alert"]] = relationship("Alert", back_populates="user", cascade="all, delete-orphan")
    portfolio: Mapped[list["Portfolio"]] = relationship("Portfolio", back_populates="user", cascade="all, delete-orphan")
    favorites: Mapped[list["FavoriteBank"]] = relationship("FavoriteBank", back_populates="user", cascade="all, delete-orphan")


class Alert(Base):
    """Alert model"""
    __tablename__ = "alerts"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    bank_code: Mapped[str] = mapped_column(String(50), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(10), nullable=False)
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    direction: Mapped[str] = mapped_column(String(10), nullable=False)
    rate_type: Mapped[str] = mapped_column(String(10), default="buy")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_triggered: Mapped[bool] = mapped_column(Boolean, default=False)
    is_repeating: Mapped[bool] = mapped_column(Boolean, default=False)  # Auto-repeat after trigger
    last_triggered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    user: Mapped["User"] = relationship("User", back_populates="alerts")


class Rate(Base):
    """Current rates"""
    __tablename__ = "rates"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bank_code: Mapped[str] = mapped_column(String(50), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(10), nullable=False)
    currency_name: Mapped[str] = mapped_column(String(100), nullable=True)
    buy_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sell_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    official_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    nominal: Mapped[int] = mapped_column(Integer, default=1)
    diff: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class RateHistory(Base):
    """Rate history for charts"""
    __tablename__ = "rate_history"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bank_code: Mapped[str] = mapped_column(String(50), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(10), nullable=False)
    buy_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sell_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    official_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Portfolio(Base):
    """User's currency portfolio"""
    __tablename__ = "portfolio"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(10), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    buy_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Sotib olgan narx
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    user: Mapped["User"] = relationship("User", back_populates="portfolio")


class FavoriteBank(Base):
    """User's favorite banks"""
    __tablename__ = "favorite_banks"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    bank_code: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    user: Mapped["User"] = relationship("User", back_populates="favorites")
