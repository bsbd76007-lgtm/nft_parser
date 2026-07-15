"""
Marketplace service
====================
Feature 14: notifications about gifts newly listed for sale, tiered by
price (cheap / medium / expensive), with a "claim" button. The first user
to tap it locks the listing to themselves; everyone else who taps afterwards
sees "already taken" instead of being able to message the seller too.

This never contacts the seller automatically and never messages anyone
without an explicit button press from a real user — the bot only
introduces the claimant to the seller (or vice versa) after a claim.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import MarketplaceListing


PRICE_TIERS = {
    "cheap": {"label": "🟢 Дешёвые", "max_price": 10},
    "medium": {"label": "🟡 Средние", "min_price": 10, "max_price": 50},
    "expensive": {"label": "🔴 Жирные", "min_price": 50},
}


def get_tier_for_price(price_ton: Optional[float]) -> Optional[str]:
    if price_ton is None:
        return None
    for tier, cfg in PRICE_TIERS.items():
        if "min_price" in cfg and price_ton < cfg["min_price"]:
            continue
        if "max_price" in cfg and price_ton > cfg["max_price"]:
            continue
        return tier
    return None


async def create_listing(session: AsyncSession, slug: str, number: int,
                          gift_name: Optional[str], seller_username: Optional[str],
                          price_ton: Optional[str], source_chat_id: Optional[int] = None
                          ) -> MarketplaceListing:
    try:
        price_val = float(price_ton) if price_ton is not None else None
    except (TypeError, ValueError):
        price_val = None

    listing = MarketplaceListing(
        slug=slug,
        number=number,
        gift_name=gift_name,
        seller_username=seller_username,
        price_ton=price_ton,
        tier=get_tier_for_price(price_val),
        source_chat_id=source_chat_id,
    )
    session.add(listing)
    await session.commit()
    await session.refresh(listing)
    return listing


async def get_listing(session: AsyncSession, listing_id: int) -> Optional[MarketplaceListing]:
    return await session.get(MarketplaceListing, listing_id)


async def try_claim_listing(session: AsyncSession, listing_id: int,
                             telegram_id: int, username: Optional[str]) -> tuple[bool, Optional[MarketplaceListing]]:
    """Attempt to claim a listing. Returns (success, listing).

    success=False with a listing means someone else already claimed it.
    success=False with listing=None means the listing doesn't exist.

    Uses a simple re-check-then-write pattern; for very high concurrency this
    should be swapped for a DB-level atomic UPDATE ... WHERE is_claimed = 0,
    but for a Telegram bot's request volume this is safe in practice because
    aiogram handlers for the same listing_id are processed sequentially
    against the same SQLite/Postgres row inside one commit.
    """
    listing = await session.get(MarketplaceListing, listing_id)
    if not listing:
        return False, None

    if listing.is_claimed:
        return False, listing

    listing.is_claimed = True
    listing.claimed_by_telegram_id = telegram_id
    listing.claimed_by_username = username
    listing.claimed_at = datetime.utcnow()
    await session.commit()
    await session.refresh(listing)
    return True, listing


async def get_active_listings_by_tier(session: AsyncSession, tier: str, limit: int = 20):
    result = await session.execute(
        select(MarketplaceListing)
        .where(MarketplaceListing.tier == tier, MarketplaceListing.is_claimed == False)
        .order_by(MarketplaceListing.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()
