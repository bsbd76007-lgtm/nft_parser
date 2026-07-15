import asyncio
import re
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import GiftTracking, User
from src.services.fragment_parser import fragment_parser


class TrackingService:
    def __init__(self):
        self.is_running = False
        self._task = None
    
    def parse_gift_url(self, url: str) -> Optional[Tuple[str, int]]:
        patterns = [
            r't\.me/nft/([a-zA-Z]+)-(\d+)',
            r'fragment\.com/gift/([a-zA-Z]+)-(\d+)',
            r'nft\.fragment\.com/gift/([a-zA-Z]+)-(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                return match.group(1).lower(), int(match.group(2))
        return None
    
    async def get_user_tracking_count(self, session: AsyncSession, user_id: int) -> int:
        result = await session.execute(
            select(GiftTracking).where(
                and_(
                    GiftTracking.user_id == user_id,
                    GiftTracking.is_active == True
                )
            )
        )
        return len(result.scalars().all())
    
    async def get_user_trackings(self, session: AsyncSession, user_id: int) -> List[GiftTracking]:
        result = await session.execute(
            select(GiftTracking).where(
                and_(
                    GiftTracking.user_id == user_id,
                    GiftTracking.is_active == True
                )
            ).order_by(GiftTracking.created_at.desc())
        )
        return result.scalars().all()
    
    async def get_tracking_limit(self, session: AsyncSession, telegram_id: int) -> Tuple[int, int]:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return 1, 60
        
        if user.is_superadmin:
            return 100, 1
        
        if user.is_premium:
            return 5, 10
        
        return 1, 60
    
    async def add_tracking(
        self,
        session: AsyncSession,
        user_id: int,
        telegram_id: int,
        slug: str,
        number: int,
        interval_minutes: int = 60
    ) -> Tuple[bool, str]:
        limit, min_interval = await self.get_tracking_limit(session, telegram_id)
        current_count = await self.get_user_tracking_count(session, user_id)
        
        if current_count >= limit:
            return False, f"Достигнут лимит слежек ({limit})"
        
        if interval_minutes < min_interval:
            interval_minutes = min_interval
        
        existing = await session.execute(
            select(GiftTracking).where(
                and_(
                    GiftTracking.user_id == user_id,
                    GiftTracking.slug == slug,
                    GiftTracking.number == number,
                    GiftTracking.is_active == True
                )
            )
        )
        if existing.scalar_one_or_none():
            return False, "Этот подарок уже отслеживается"
        
        gift_data = await fragment_parser.get_gift_full_data(slug, number)
        
        if not gift_data:
            return False, "Не удалось получить данные о подарке"
        
        now = datetime.utcnow()
        price_str = str(gift_data.price_ton) if gift_data.price_ton is not None else None
        tracking = GiftTracking(
            user_id=user_id,
            slug=slug,
            number=number,
            last_owner=gift_data.owner,
            last_status=gift_data.status,
            last_price=price_str,
            is_hidden=False,
            check_interval=interval_minutes,
            last_checked=now,
            next_check=now + timedelta(minutes=interval_minutes),
            is_active=True
        )
        
        session.add(tracking)
        await session.commit()
        
        return True, "Слежка добавлена"
    
    async def remove_tracking(self, session: AsyncSession, tracking_id: int, user_id: int) -> bool:
        result = await session.execute(
            select(GiftTracking).where(
                and_(
                    GiftTracking.id == tracking_id,
                    GiftTracking.user_id == user_id
                )
            )
        )
        tracking = result.scalar_one_or_none()
        
        if tracking:
            tracking.is_active = False
            await session.commit()
            return True
        return False
    
    async def get_pending_checks(self, session: AsyncSession) -> List[GiftTracking]:
        now = datetime.utcnow()
        result = await session.execute(
            select(GiftTracking).where(
                and_(
                    GiftTracking.is_active == True,
                    GiftTracking.next_check <= now
                )
            ).limit(50)
        )
        return result.scalars().all()
    
    async def check_gift_status(self, tracking: GiftTracking) -> Optional[Dict[str, Any]]:
        gift_data = await fragment_parser.get_gift_full_data(tracking.slug, tracking.number)
        
        changes = {}
        
        if not gift_data:
            if not tracking.is_hidden:
                changes["hidden"] = True
            return changes if changes else None
        
        if tracking.is_hidden and gift_data:
            changes["unhidden"] = True
        
        if gift_data.owner != tracking.last_owner:
            changes["owner_changed"] = {
                "old": tracking.last_owner,
                "new": gift_data.owner
            }
        
        if gift_data.status != tracking.last_status:
            changes["status_changed"] = {
                "old": tracking.last_status,
                "new": gift_data.status
            }
        
        new_price_str = str(gift_data.price_ton) if gift_data.price_ton is not None else None
        if new_price_str != tracking.last_price:
            changes["price_changed"] = {
                "old": tracking.last_price,
                "new": new_price_str
            }
        
        return changes if changes else None
    
    async def update_tracking_after_check(
        self,
        session: AsyncSession,
        tracking: GiftTracking,
        gift_data: Optional[Any] = None,
        is_hidden: bool = False
    ):
        now = datetime.utcnow()
        
        tracking.last_checked = now
        tracking.next_check = now + timedelta(minutes=tracking.check_interval)
        tracking.is_hidden = is_hidden
        
        if gift_data:
            tracking.last_owner = gift_data.owner
            tracking.last_status = gift_data.status
            tracking.last_price = str(gift_data.price_ton) if gift_data.price_ton is not None else None
        
        await session.commit()


tracking_service = TrackingService()
