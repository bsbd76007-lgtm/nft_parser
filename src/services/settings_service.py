from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import BotSettings


class SettingsService:
    SUBSCRIPTION_ENABLED = "subscription_enabled"
    SUBSCRIPTION_CHANNEL = "subscription_channel"
    
    async def get_setting(self, session: AsyncSession, key: str) -> Optional[str]:
        result = await session.execute(
            select(BotSettings).where(BotSettings.key == key)
        )
        setting = result.scalar_one_or_none()
        return setting.value if setting else None
    
    async def set_setting(self, session: AsyncSession, key: str, value: str) -> None:
        result = await session.execute(
            select(BotSettings).where(BotSettings.key == key)
        )
        setting = result.scalar_one_or_none()
        
        if setting:
            setting.value = value
        else:
            setting = BotSettings(key=key, value=value)
            session.add(setting)
        
        await session.commit()
    
    async def is_subscription_required(self, session: AsyncSession) -> bool:
        value = await self.get_setting(session, self.SUBSCRIPTION_ENABLED)
        return value == "true"
    
    async def set_subscription_required(self, session: AsyncSession, enabled: bool) -> None:
        await self.set_setting(session, self.SUBSCRIPTION_ENABLED, "true" if enabled else "false")
    
    async def get_subscription_channel(self, session: AsyncSession) -> Optional[str]:
        return await self.get_setting(session, self.SUBSCRIPTION_CHANNEL)
    
    async def set_subscription_channel(self, session: AsyncSession, channel: str) -> None:
        await self.set_setting(session, self.SUBSCRIPTION_CHANNEL, channel)


settings_service = SettingsService()
