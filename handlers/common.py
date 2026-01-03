"""
Common utilities for handlers - NO duplicate menu keyboard
"""
from sqlalchemy import select

from database.db import get_session
from database.models import User


async def get_or_create_user(user_id: int, username: str = None, 
                              first_name: str = None, last_name: str = None) -> User:
    """Get existing user or create new one"""
    async with get_session() as session:
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if user is None:
            user = User(
                id=user_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                language="uz",
                daily_notify_time="09:00"
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        else:
            if username and user.username != username:
                user.username = username
            if first_name and user.first_name != first_name:
                user.first_name = first_name
            if last_name and user.last_name != last_name:
                user.last_name = last_name
            await session.commit()
        
        return user


async def get_user_language(user_id: int) -> str:
    """Get user's language preference"""
    async with get_session() as session:
        result = await session.execute(
            select(User.language).where(User.id == user_id)
        )
        lang = result.scalar_one_or_none()
        return lang if lang else "uz"


async def set_user_language(user_id: int, language: str) -> bool:
    """Set user's language preference"""
    async with get_session() as session:
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if user:
            user.language = language
            await session.commit()
            return True
        return False
