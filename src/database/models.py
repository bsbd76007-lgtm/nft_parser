from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, String, Boolean, DateTime, Text, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    is_admin = Column(Boolean, default=False)
    is_superadmin = Column(Boolean, default=False)
    is_premium = Column(Boolean, default=False)
    language = Column(String(10), default="ru")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    blocks = relationship("UserBlock", back_populates="user", cascade="all, delete-orphan")
    tracked_gifts = relationship("GiftTracking", back_populates="user", cascade="all, delete-orphan")
    auto_searches = relationship("AutoSearch", back_populates="user", cascade="all, delete-orphan")


class NFTGift(Base):
    __tablename__ = "nft_gifts"
    
    id = Column(Integer, primary_key=True)
    nft_id = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    collection_name = Column(String(255), nullable=True)
    owner_address = Column(String(255), nullable=True, index=True)
    owner_username = Column(String(255), nullable=True)
    
    model = Column(String(255), nullable=True, index=True)
    backdrop = Column(String(255), nullable=True, index=True)
    symbol = Column(String(255), nullable=True, index=True)
    
    rarity_percent = Column(String(50), nullable=True)
    image_url = Column(Text, nullable=True)
    lottie_url = Column(Text, nullable=True)
    
    price_ton = Column(String(50), nullable=True)
    total_issued = Column(Integer, nullable=True)
    number_in_collection = Column(BigInteger, nullable=True)
    
    gifted_by = Column(String(255), nullable=True)
    gifted_to = Column(String(255), nullable=True)
    gifted_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_nft_gifts_backdrop_symbol', 'backdrop', 'symbol'),
    )


class UserBlock(Base):
    __tablename__ = "user_blocks"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    nft_gift_id = Column(Integer, ForeignKey("nft_gifts.id"), nullable=True)
    gift_name = Column(String(255), nullable=True)
    blocked_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="blocks")
    gift = relationship("NFTGift")
    
    __table_args__ = (
        Index('ix_user_blocks_user_gift', 'user_id', 'nft_gift_id'),
    )


class Broadcast(Base):
    __tablename__ = "broadcasts"
    
    id = Column(Integer, primary_key=True)
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message_text = Column(Text, nullable=False)
    photo_file_id = Column(String(255), nullable=True)
    sent_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    admin = relationship("User")


class BotSettings(Base):
    __tablename__ = "bot_settings"
    
    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GiftTracking(Base):
    __tablename__ = "gift_trackings"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    slug = Column(String(100), nullable=False)
    number = Column(Integer, nullable=False)
    
    last_owner = Column(String(255), nullable=True)
    last_status = Column(String(100), nullable=True)
    last_price = Column(String(100), nullable=True)
    is_hidden = Column(Boolean, default=False)
    
    check_interval = Column(Integer, default=60)
    last_checked = Column(DateTime, nullable=True)
    next_check = Column(DateTime, nullable=True)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="tracked_gifts")
    
    __table_args__ = (
        Index('ix_gift_tracking_user_slug_num', 'user_id', 'slug', 'number'),
        Index('ix_gift_tracking_next_check', 'next_check', 'is_active'),
    )


class BlacklistGift(Base):
    """Gifts hidden from search results (e.g. known scam/fake listings)."""
    __tablename__ = "blacklist_gifts"

    id = Column(Integer, primary_key=True)
    added_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    slug = Column(String(100), nullable=True, index=True)
    name_pattern = Column(String(255), nullable=True, index=True)
    reason = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class BlacklistSeller(Base):
    """Sellers/owners hidden from search results and marketplace notifications
    (e.g. known scammers on the marketplace)."""
    __tablename__ = "blacklist_sellers"

    id = Column(Integer, primary_key=True)
    added_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    username = Column(String(255), nullable=False, index=True)
    reason = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('ix_blacklist_seller_username', 'username'),
    )


class ChatSource(Base):
    """Telegram chats/channels monitored for gift trading activity."""
    __tablename__ = "chat_sources"

    id = Column(Integer, primary_key=True)
    added_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    chat_id = Column(BigInteger, nullable=False, index=True)
    chat_title = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('ix_chat_source_chat_id', 'chat_id'),
    )


class MarketplaceListing(Base):
    """A gift listed for sale, tracked so the bot can notify subscribers and
    manage the claim workflow (one buyer at a time)."""
    __tablename__ = "marketplace_listings"

    id = Column(Integer, primary_key=True)
    slug = Column(String(100), nullable=False)
    number = Column(Integer, nullable=False)
    gift_name = Column(String(255), nullable=True)
    seller_username = Column(String(255), nullable=True)
    price_ton = Column(String(50), nullable=True)
    tier = Column(String(20), nullable=True)  # cheap / medium / expensive

    source_chat_id = Column(BigInteger, nullable=True)

    is_claimed = Column(Boolean, default=False)
    claimed_by_telegram_id = Column(BigInteger, nullable=True)
    claimed_by_username = Column(String(255), nullable=True)
    claimed_at = Column(DateTime, nullable=True)

    notified_chat_id = Column(BigInteger, nullable=True)
    notified_message_id = Column(BigInteger, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('ix_marketplace_listing_slug_num', 'slug', 'number'),
        Index('ix_marketplace_listing_claimed', 'is_claimed'),
    )


class UserFilterPreset(Base):
    """Saved combination of search filters for a user (quick search mode,
    backdrop, rarity threshold, price tier, etc.) so several filters can be
    applied together and reused."""
    __tablename__ = "user_filter_presets"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=True)

    quick_mode = Column(String(20), nullable=True)     # light / medium / heavy
    backdrop = Column(String(255), nullable=True)
    rare_models_only = Column(Boolean, default=False)
    price_tier = Column(String(20), nullable=True)      # cheap / medium / expensive
    collection_slug = Column(String(100), nullable=True)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AutoSearch(Base):
    __tablename__ = "auto_searches"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    search_type = Column(String(50), nullable=False)
    collection_slug = Column(String(100), nullable=True)
    filter_type = Column(String(50), nullable=True)
    filter_value = Column(String(100), nullable=True)
    
    found_owners = Column(Text, nullable=True)
    last_run = Column(DateTime, nullable=True)
    next_run = Column(DateTime, nullable=True)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="auto_searches")
    
    __table_args__ = (
        Index('ix_auto_search_next_run', 'next_run', 'is_active'),
    )
