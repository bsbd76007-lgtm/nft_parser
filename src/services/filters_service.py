"""
Filters service
================
Central place for all the gift-listing filter logic:

1. Quick search modes (light / medium / heavy) — price based tiers.
5. Rare model detection (rarity below a threshold, default 0.8%).
3. Emoji-prefixed gift names, similar in spirit to @PriceNFTbot.
2. Blacklist checks (gifts + sellers) so hidden items never show up.

None of this touches user/account search — it only filters gift listings
that the existing fragment_parser already returns.
"""
from dataclasses import dataclass
from typing import Iterable, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import BlacklistGift, BlacklistSeller


# ---------------------------------------------------------------------------
# 1. Quick search modes
# ---------------------------------------------------------------------------
# Thresholds are in TON. Tune these to taste / market conditions.
QUICK_MODES = {
    "light": {"label": "🟢 Лёгкий (до 10 TON)", "max_price": 10},
    "medium": {"label": "🟡 Средний (10-50 TON)", "min_price": 10, "max_price": 50},
    "heavy": {"label": "🔴 Жирный (50+ TON)", "min_price": 50},
}


def price_matches_mode(price_ton: Optional[float], mode: str) -> bool:
    """Check whether a gift's price fits a quick-search tier."""
    if mode not in QUICK_MODES or price_ton is None:
        return False
    cfg = QUICK_MODES[mode]
    if "min_price" in cfg and price_ton < cfg["min_price"]:
        return False
    if "max_price" in cfg and price_ton > cfg["max_price"]:
        return False
    return True


def get_quick_mode_label(mode: str) -> str:
    return QUICK_MODES.get(mode, {}).get("label", mode)


# ---------------------------------------------------------------------------
# 5. Rare models
# ---------------------------------------------------------------------------
DEFAULT_RARE_THRESHOLD = 0.8  # percent


def parse_rarity_percent(raw: Optional[str]) -> Optional[float]:
    """Turn '0.35%' / '0.35' into 0.35 (float), or None if unparseable."""
    if not raw:
        return None
    cleaned = raw.replace("%", "").replace(",", ".").strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


def is_rare_model(model_rarity: Optional[str], threshold: float = DEFAULT_RARE_THRESHOLD) -> bool:
    value = parse_rarity_percent(model_rarity)
    if value is None:
        return False
    return value < threshold


# ---------------------------------------------------------------------------
# 3. Emoji names for gifts (à la @PriceNFTbot)
# ---------------------------------------------------------------------------
# Extend this mapping with real collection slugs/names as needed.
GIFT_EMOJI_MAP = {
    "plush pepe": "🐸",
    "durov's cap": "🎩",
    "vintage cigar": "🚬",
    "toy bear": "🧸",
    "diamond ring": "💍",
    "santa hat": "🎅",
    "heart locket": "💝",
    "eternal rose": "🌹",
    "signet ring": "💍",
    "precious peach": "🍑",
    "party sparkler": "🎉",
    "golden star": "⭐",
}

DEFAULT_GIFT_EMOJI = "🎁"


def get_gift_emoji(name: Optional[str], collection_name: Optional[str] = None) -> str:
    key = (name or collection_name or "").strip().lower()
    for known, emoji in GIFT_EMOJI_MAP.items():
        if known in key:
            return emoji
    return DEFAULT_GIFT_EMOJI


def format_gift_name_with_emoji(name: str, collection_name: Optional[str] = None) -> str:
    emoji = get_gift_emoji(name, collection_name)
    return f"{emoji} {name}"


# ---------------------------------------------------------------------------
# 2. Blacklist (gifts + sellers)
# ---------------------------------------------------------------------------
async def get_blacklisted_gift_patterns(session: AsyncSession) -> List[dict]:
    result = await session.execute(select(BlacklistGift))
    rows = result.scalars().all()
    return [{"slug": r.slug, "name_pattern": r.name_pattern} for r in rows]


async def get_blacklisted_sellers(session: AsyncSession) -> List[str]:
    result = await session.execute(select(BlacklistSeller))
    rows = result.scalars().all()
    return [r.username.lower() for r in rows if r.username]


async def is_gift_blacklisted(session: AsyncSession, slug: Optional[str], name: Optional[str]) -> bool:
    patterns = await get_blacklisted_gift_patterns(session)
    for p in patterns:
        if p["slug"] and slug and p["slug"].lower() == slug.lower():
            return True
        if p["name_pattern"] and name and p["name_pattern"].lower() in name.lower():
            return True
    return False


async def is_seller_blacklisted(session: AsyncSession, username: Optional[str]) -> bool:
    if not username:
        return False
    blacklisted = await get_blacklisted_sellers(session)
    return username.lower() in blacklisted


async def add_gift_to_blacklist(session: AsyncSession, added_by_user_id: int,
                                 slug: Optional[str] = None,
                                 name_pattern: Optional[str] = None,
                                 reason: Optional[str] = None) -> BlacklistGift:
    entry = BlacklistGift(added_by_user_id=added_by_user_id, slug=slug,
                           name_pattern=name_pattern, reason=reason)
    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    return entry


async def add_seller_to_blacklist(session: AsyncSession, added_by_user_id: int,
                                   username: str, reason: Optional[str] = None) -> BlacklistSeller:
    entry = BlacklistSeller(added_by_user_id=added_by_user_id,
                             username=username.lstrip("@"), reason=reason)
    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    return entry


async def remove_gift_from_blacklist(session: AsyncSession, entry_id: int) -> bool:
    entry = await session.get(BlacklistGift, entry_id)
    if not entry:
        return False
    await session.delete(entry)
    await session.commit()
    return True


async def remove_seller_from_blacklist(session: AsyncSession, entry_id: int) -> bool:
    entry = await session.get(BlacklistSeller, entry_id)
    if not entry:
        return False
    await session.delete(entry)
    await session.commit()
    return True


# ---------------------------------------------------------------------------
# 4. Backdrop filter helper
# ---------------------------------------------------------------------------
def matches_backdrop(gift_backdrop: Optional[str], wanted_backdrop: Optional[str]) -> bool:
    if not wanted_backdrop:
        return True
    if not gift_backdrop:
        return False
    return wanted_backdrop.strip().lower() in gift_backdrop.strip().lower()


# ---------------------------------------------------------------------------
# 8. Combined filter application over a list of gifts
# ---------------------------------------------------------------------------
@dataclass
class GiftFilterCriteria:
    quick_mode: Optional[str] = None          # light / medium / heavy
    backdrop: Optional[str] = None
    rare_models_only: bool = False
    rare_threshold: float = DEFAULT_RARE_THRESHOLD


async def apply_gift_filters(session: AsyncSession, gifts: Iterable, criteria: GiftFilterCriteria) -> List:
    """Filter a list of GiftData-like objects (must expose .price_ton,
    .backdrop, .model_rarity, .slug, .name, .owner) according to the given
    criteria plus blacklist rules."""
    blacklisted_patterns = await get_blacklisted_gift_patterns(session)
    blacklisted_sellers = await get_blacklisted_sellers(session)

    filtered = []
    for gift in gifts:
        name = getattr(gift, "name", None)
        slug = getattr(gift, "slug", None)
        owner = getattr(gift, "owner", None)

        if owner and owner.lower() in blacklisted_sellers:
            continue

        skip = False
        for p in blacklisted_patterns:
            if p["slug"] and slug and p["slug"].lower() == slug.lower():
                skip = True
                break
            if p["name_pattern"] and name and p["name_pattern"].lower() in name.lower():
                skip = True
                break
        if skip:
            continue

        if criteria.quick_mode:
            price = getattr(gift, "price_ton", None)
            try:
                price_val = float(price) if price is not None else None
            except (TypeError, ValueError):
                price_val = None
            if not price_matches_mode(price_val, criteria.quick_mode):
                continue

        if criteria.backdrop and not matches_backdrop(getattr(gift, "backdrop", None), criteria.backdrop):
            continue

        if criteria.rare_models_only and not is_rare_model(
                getattr(gift, "model_rarity", None), criteria.rare_threshold):
            continue

        filtered.append(gift)

    return filtered
