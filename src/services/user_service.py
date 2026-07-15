from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.dialects.postgresql import insert

from src.database.models import User, UserBlock


class UserService:
    async def get_or_create_user(
        self,
        session: AsyncSession,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> User:
        query = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(query)
        user = result.scalar_one_or_none()
        
        if user:
            updated = False
            if username and user.username != username:
                user.username = username
                updated = True
            if first_name and user.first_name != first_name:
                user.first_name = first_name
                updated = True
            if last_name and user.last_name != last_name:
                user.last_name = last_name
                updated = True
            if updated:
                await session.commit()
            return user
        
        try:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user
        except IntegrityError:
            await session.rollback()
            query = select(User).where(User.telegram_id == telegram_id)
            result = await session.execute(query)
            user = result.scalar_one_or_none()
            return user
    
    async def is_admin(self, session: AsyncSession, telegram_id: int) -> bool:
        query = select(User).where(
            User.telegram_id == telegram_id,
            User.is_admin == True
        )
        result = await session.execute(query)
        return result.scalar_one_or_none() is not None
    
    async def is_superadmin(self, session: AsyncSession, telegram_id: int) -> bool:
        query = select(User).where(
            User.telegram_id == telegram_id,
            User.is_superadmin == True
        )
        result = await session.execute(query)
        return result.scalar_one_or_none() is not None
    
    async def set_admin(
        self,
        session: AsyncSession,
        telegram_id: int,
        is_admin: bool = True
    ) -> bool:
        query = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(query)
        user = result.scalar_one_or_none()
        
        if user:
            user.is_admin = is_admin
            await session.commit()
            return True
        return False
    
    async def set_superadmin(
        self,
        session: AsyncSession,
        telegram_id: int,
        is_superadmin: bool = True
    ) -> bool:
        query = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(query)
        user = result.scalar_one_or_none()
        
        if user:
            user.is_superadmin = is_superadmin
            user.is_admin = True
            await session.commit()
            return True
        return False
    
    async def get_all_users(self, session: AsyncSession) -> List[User]:
        query = select(User)
        result = await session.execute(query)
        return list(result.scalars().all())
    
    async def get_users_count(self, session: AsyncSession) -> int:
        query = select(func.count(User.id))
        result = await session.execute(query)
        return result.scalar() or 0
    
    async def get_premium_count(self, session: AsyncSession) -> int:
        query = select(func.count(User.id)).where(User.is_premium == True)
        result = await session.execute(query)
        return result.scalar() or 0
    
    async def block_gift(
        self,
        session: AsyncSession,
        user_id: int,
        gift_id: Optional[int] = None,
        gift_name: Optional[str] = None
    ) -> bool:
        existing = await session.execute(
            select(UserBlock).where(
                UserBlock.user_id == user_id,
                UserBlock.nft_gift_id == gift_id
            )
        )
        if existing.scalar_one_or_none():
            return False
        
        try:
            block = UserBlock(
                user_id=user_id,
                nft_gift_id=gift_id,
                gift_name=gift_name
            )
            session.add(block)
            await session.commit()
            return True
        except IntegrityError:
            await session.rollback()
            return False
    
    async def unblock_gift(
        self,
        session: AsyncSession,
        user_id: int,
        gift_id: int
    ) -> bool:
        query = select(UserBlock).where(
            UserBlock.user_id == user_id,
            UserBlock.nft_gift_id == gift_id
        )
        result = await session.execute(query)
        block = result.scalar_one_or_none()
        
        if block:
            await session.delete(block)
            await session.commit()
            return True
        return False
    
    async def get_user_blocks(
        self,
        session: AsyncSession,
        user_id: int
    ) -> List[UserBlock]:
        query = select(UserBlock).where(UserBlock.user_id == user_id)
        result = await session.execute(query)
        return list(result.scalars().all())
    
    async def get_user_by_telegram_id(
        self,
        session: AsyncSession,
        telegram_id: int
    ) -> Optional[User]:
        query = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()
    
    async def set_premium(
        self,
        session: AsyncSession,
        telegram_id: int,
        is_premium: bool = True
    ) -> bool:
        query = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(query)
        user = result.scalar_one_or_none()
        
        if user:
            user.is_premium = is_premium
            await session.commit()
            return True
        return False
    
    async def get_premium_users(self, session: AsyncSession) -> List[User]:
        query = select(User).where(User.is_premium == True)
        result = await session.execute(query)
        return list(result.scalars().all())


user_service = UserService()
