"""
Marketplace feature (item 14) + chat monitoring (item 10).

Flow:
1. An admin registers a chat as a "gift market" source with /register_market_chat
   (run inside that chat) — this is item 10, search/monitoring by chats.
2. When a message in a registered chat looks like a gift listing (simple
   pattern: name + price in TON, optionally an @seller), the bot creates a
   MarketplaceListing and posts a tiered notification (cheap/medium/expensive)
   to the configured marketplace notification chat, with a "Take it" button.
3. The first user to press the button claims the listing; the bot then
   privately introduces buyer and seller to each other. Everyone else who
   taps afterwards just sees "already taken" — nobody else can message the
   seller through this flow once it's claimed.

This never scrapes or messages random users on its own; it only reacts to
explicit listing messages posted in chats an admin opted the bot into, and
only proceeds when a real person taps the claim button.
"""
import re
from typing import Optional

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from sqlalchemy import select

from src.config import ADMINS
from src.database.connection import async_session
from src.database.models import ChatSource, MarketplaceListing, User
from src.services.filters_service import is_seller_blacklisted, format_gift_name_with_emoji
from src.services.marketplace_service import (
    create_listing, try_claim_listing, PRICE_TIERS,
)
from src.keyboards.inline import get_marketplace_menu, get_claim_keyboard

router = Router()

# Matches things like: "Plush Pepe #123 - 45 TON @seller_name"
LISTING_PATTERN = re.compile(
    r"(?P<name>[A-Za-zА-Яа-я0-9 ']{3,60}?)\s*#?(?P<number>\d+)?\s*[-–—]\s*"
    r"(?P<price>\d+(?:\.\d+)?)\s*TON\b(?:.*?@(?P<seller>[A-Za-z0-9_]{4,32}))?",
    re.IGNORECASE,
)


def _tier_label(tier: Optional[str]) -> str:
    return PRICE_TIERS.get(tier, {}).get("label", "—")


@router.message(Command("register_market_chat"))
async def cmd_register_market_chat(message: Message):
    if message.from_user.id not in ADMINS:
        await message.answer("⛔ Только администраторы могут регистрировать чаты.")
        return

    async with async_session() as session:
        result = await session.execute(
            select(ChatSource).where(ChatSource.chat_id == message.chat.id)
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.is_active = True
            await session.commit()
            await message.answer("✅ Этот чат уже отслеживается как источник объявлений о подарках.")
            return

        source = ChatSource(
            added_by_user_id=message.from_user.id,
            chat_id=message.chat.id,
            chat_title=message.chat.title or str(message.chat.id),
        )
        session.add(source)
        await session.commit()

    await message.answer(
        "✅ Чат добавлен как источник объявлений. "
        "Сообщения вида «Название - 45 TON @продавец» будут попадать в маркетплейс."
    )


@router.message(Command("unregister_market_chat"))
async def cmd_unregister_market_chat(message: Message):
    if message.from_user.id not in ADMINS:
        await message.answer("⛔ Только администраторы могут это делать.")
        return

    async with async_session() as session:
        result = await session.execute(
            select(ChatSource).where(ChatSource.chat_id == message.chat.id)
        )
        source = result.scalar_one_or_none()
        if source:
            source.is_active = False
            await session.commit()
            await message.answer("✅ Чат больше не отслеживается.")
        else:
            await message.answer("Этот чат не был зарегистрирован.")


@router.message(Command("set_market_channel"))
async def cmd_set_market_channel(message: Message):
    """Marks the current chat as the destination where tiered marketplace
    notifications (with the claim button) get posted."""
    if message.from_user.id not in ADMINS:
        await message.answer("⛔ Только администраторы могут это делать.")
        return

    from src.database.models import BotSettings
    async with async_session() as session:
        result = await session.execute(select(BotSettings).where(BotSettings.key == "market_channel_id"))
        setting = result.scalar_one_or_none()
        if setting:
            setting.value = str(message.chat.id)
        else:
            setting = BotSettings(key="market_channel_id", value=str(message.chat.id))
            session.add(setting)
        await session.commit()

    await message.answer("✅ Этот чат назначен каналом уведомлений маркетплейса.")


async def _get_market_channel_id(session) -> Optional[int]:
    from src.database.models import BotSettings
    result = await session.execute(select(BotSettings).where(BotSettings.key == "market_channel_id"))
    setting = result.scalar_one_or_none()
    if setting and setting.value:
        try:
            return int(setting.value)
        except ValueError:
            return None
    return None


@router.message(F.text.regexp(LISTING_PATTERN.pattern))
async def catch_listing_message(message: Message):
    """Only reacts in chats explicitly registered as gift-market sources."""
    async with async_session() as session:
        result = await session.execute(
            select(ChatSource).where(
                ChatSource.chat_id == message.chat.id, ChatSource.is_active == True
            )
        )
        source = result.scalar_one_or_none()
        if not source:
            return

        match = LISTING_PATTERN.search(message.text or "")
        if not match:
            return

        name = match.group("name").strip()
        price = match.group("price")
        seller = match.group("seller") or (message.from_user.username if message.from_user else None)

        if seller and await is_seller_blacklisted(session, seller):
            return

        listing = await create_listing(
            session,
            slug="chat-source",
            number=int(match.group("number")) if match.group("number") else 0,
            gift_name=name,
            seller_username=seller,
            price_ton=price,
            source_chat_id=message.chat.id,
        )

        market_channel_id = await _get_market_channel_id(session)

    if not market_channel_id:
        return  # no destination configured yet

    display_name = format_gift_name_with_emoji(name)
    text = (
        f"🏪 <b>Новый подарок в продаже</b>\n\n"
        f"{display_name}\n"
        f"💰 {price} TON  |  Уровень: {_tier_label(listing.tier)}\n"
    )
    if seller:
        text += f"👤 Продавец: @{seller}\n"
    text += "\nНажмите кнопку, чтобы забрать — первый нажавший получит контакт продавца."

    sent = await message.bot.send_message(
        market_channel_id, text, reply_markup=get_claim_keyboard(listing.id), parse_mode="HTML"
    )

    async with async_session() as session:
        listing2 = await session.get(MarketplaceListing, listing.id)
        if listing2:
            listing2.notified_chat_id = market_channel_id
            listing2.notified_message_id = sent.message_id
            await session.commit()


@router.callback_query(F.data == "marketplace_menu")
async def callback_marketplace_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "🏪 <b>Маркетплейс</b>\n\n"
        "Уведомления о новых подарках на продажу, поделённые по цене. "
        "Нажмите «Забрать», чтобы застолбить подарок за собой — остальным "
        "он после этого будет показан как занятый.",
        reply_markup=get_marketplace_menu(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("market_claim:"))
async def callback_market_claim(callback: CallbackQuery):
    listing_id = int(callback.data.split(":")[1])
    user = callback.from_user

    async with async_session() as session:
        success, listing = await try_claim_listing(session, listing_id, user.id, user.username)

    if listing is None:
        await callback.answer("Это объявление больше не существует.", show_alert=True)
        return

    if not success:
        await callback.answer(
            f"😔 Уже занято пользователем @{listing.claimed_by_username or 'кто-то'}.",
            show_alert=True
        )
        return

    # Update the public message so nobody else tries.
    try:
        display_name = format_gift_name_with_emoji(listing.gift_name or "")
        taken_text = (
            f"🏪 <b>Подарок разобран</b>\n\n"
            f"{display_name}\n"
            f"💰 {listing.price_ton} TON\n"
            f"✅ Забрал: @{user.username or user.id}"
        )
        await callback.message.edit_text(taken_text, parse_mode="HTML")
    except Exception:
        pass

    await callback.answer("✅ Подарок за вами! Продавцу отправлены ваши контакты.", show_alert=True)

    # Introduce buyer and seller to each other (only after an explicit claim).
    if listing.seller_username:
        buyer_mention = f"@{user.username}" if user.username else f"tg://user?id={user.id}"
        try:
            await callback.bot.send_message(
                listing.claimed_by_telegram_id,
                f"🤝 Вы забрали «{listing.gift_name}» за {listing.price_ton} TON.\n"
                f"Продавец: @{listing.seller_username}\n"
                f"Напишите ему, чтобы договориться о сделке."
            )
        except Exception:
            pass
