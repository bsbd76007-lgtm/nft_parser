import csv
import io
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select, update

from src.database.connection import async_session
from src.database.models import User, GiftTracking
from src.services.tracking_service import tracking_service
from src.keyboards.inline import (
    get_tools_menu, 
    get_settings_menu,
    get_tracking_menu,
    get_tracking_interval_keyboard,
    get_tracking_view_keyboard,
    get_main_menu,
    get_back_button
)

router = Router()


class TrackingStates(StatesGroup):
    waiting_gift_url = State()
    waiting_interval = State()


async def get_user_lang(session, telegram_id: int) -> str:
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()
    return user.language if user else "ru"


async def is_user_premium(session, telegram_id: int) -> bool:
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        return False
    return user.is_premium or user.is_superadmin


@router.callback_query(F.data == "tools_menu")
async def callback_tools_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    
    async with async_session() as session:
        lang = await get_user_lang(session, callback.from_user.id)
        
        if lang == "en":
            text = "🛠 <b>Tools</b>\n\nSelect a tool:"
        else:
            text = "🛠 <b>Инструменты</b>\n\nВыберите инструмент:"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_tools_menu(lang),
            parse_mode="HTML"
        )
        await callback.answer()


@router.callback_query(F.data == "settings_menu")
async def callback_settings_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    
    async with async_session() as session:
        lang = await get_user_lang(session, callback.from_user.id)
        
        if lang == "en":
            text = "⚙️ <b>Settings</b>\n\nConfigure your preferences:"
        else:
            text = "⚙️ <b>Настройки</b>\n\nНастройте параметры:"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_settings_menu(lang),
            parse_mode="HTML"
        )
        await callback.answer()


@router.callback_query(F.data.startswith("set_lang:"))
async def callback_set_language(callback: CallbackQuery):
    new_lang = callback.data.split(":")[1]
    
    async with async_session() as session:
        await session.execute(
            update(User).where(User.telegram_id == callback.from_user.id).values(language=new_lang)
        )
        await session.commit()
        
        if new_lang == "en":
            text = "⚙️ <b>Settings</b>\n\n✅ Language changed to English"
        else:
            text = "⚙️ <b>Настройки</b>\n\n✅ Язык изменён на Русский"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_settings_menu(new_lang),
            parse_mode="HTML"
        )
        await callback.answer()


@router.callback_query(F.data == "tracking_menu")
async def callback_tracking_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    
    async with async_session() as session:
        lang = await get_user_lang(session, callback.from_user.id)
        is_premium = await is_user_premium(session, callback.from_user.id)
        
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            await callback.answer("Ошибка", show_alert=True)
            return
        
        trackings = await tracking_service.get_user_trackings(session, user.id)
        limit, min_interval = await tracking_service.get_tracking_limit(session, callback.from_user.id)
        
        if lang == "en":
            status = "⭐ Premium" if is_premium else "Standard"
            text = (
                f"👁 <b>Gift Tracking</b>\n\n"
                f"Status: {status}\n"
                f"Tracking limit: {len(trackings)}/{limit}\n"
                f"Check interval: min {min_interval} min\n\n"
                f"Your trackings:"
            )
        else:
            status = "⭐ Premium" if is_premium else "Стандарт"
            text = (
                f"👁 <b>Слежка за подарками</b>\n\n"
                f"Статус: {status}\n"
                f"Лимит слежек: {len(trackings)}/{limit}\n"
                f"Интервал проверки: мин {min_interval} мин\n\n"
                f"Ваши слежки:"
            )
        
        if not trackings:
            if lang == "en":
                text += "\n\n<i>No active trackings</i>"
            else:
                text += "\n\n<i>Нет активных слежек</i>"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_tracking_menu(trackings, lang),
            parse_mode="HTML"
        )
        await callback.answer()


@router.callback_query(F.data == "add_tracking")
async def callback_add_tracking(callback: CallbackQuery, state: FSMContext):
    async with async_session() as session:
        lang = await get_user_lang(session, callback.from_user.id)
        
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            await callback.answer("Ошибка", show_alert=True)
            return
        
        limit, _ = await tracking_service.get_tracking_limit(session, callback.from_user.id)
        current_count = await tracking_service.get_user_tracking_count(session, user.id)
        
        if current_count >= limit:
            if lang == "en":
                await callback.answer(f"Tracking limit reached ({limit})", show_alert=True)
            else:
                await callback.answer(f"Лимит слежек достигнут ({limit})", show_alert=True)
            return
        
        await state.set_state(TrackingStates.waiting_gift_url)
        
        if lang == "en":
            text = (
                "👁 <b>Add Tracking</b>\n\n"
                "Send the gift link:\n\n"
                "Examples:\n"
                "• https://t.me/nft/DurovsCap-28\n"
                "• https://fragment.com/gift/eternalrose-123"
            )
        else:
            text = (
                "👁 <b>Добавить слежку</b>\n\n"
                "Отправьте ссылку на подарок:\n\n"
                "Примеры:\n"
                "• https://t.me/nft/DurovsCap-28\n"
                "• https://fragment.com/gift/eternalrose-123"
            )
        
        await callback.message.edit_text(
            text,
            reply_markup=get_back_button("tracking_menu"),
            parse_mode="HTML"
        )
        await callback.answer()


@router.message(TrackingStates.waiting_gift_url)
async def process_gift_url(message: Message, state: FSMContext):
    url = message.text.strip()
    
    parsed = tracking_service.parse_gift_url(url)
    
    async with async_session() as session:
        lang = await get_user_lang(session, message.from_user.id)
        is_premium = await is_user_premium(session, message.from_user.id)
        
        if not parsed:
            if lang == "en":
                await message.answer(
                    "❌ Invalid link format.\n\n"
                    "Please send a valid link:\n"
                    "• https://t.me/nft/DurovsCap-28\n"
                    "• https://fragment.com/gift/eternalrose-123",
                    reply_markup=get_back_button("tracking_menu"),
                    parse_mode="HTML"
                )
            else:
                await message.answer(
                    "❌ Неверный формат ссылки.\n\n"
                    "Отправьте корректную ссылку:\n"
                    "• https://t.me/nft/DurovsCap-28\n"
                    "• https://fragment.com/gift/eternalrose-123",
                    reply_markup=get_back_button("tracking_menu"),
                    parse_mode="HTML"
                )
            return
        
        slug, number = parsed
        await state.update_data(slug=slug, number=number)
        await state.set_state(TrackingStates.waiting_interval)
        
        if lang == "en":
            text = (
                f"👁 <b>Tracking: {slug}-{number}</b>\n\n"
                f"Select check interval:"
            )
        else:
            text = (
                f"👁 <b>Слежка: {slug}-{number}</b>\n\n"
                f"Выберите интервал проверки:"
            )
        
        await message.answer(
            text,
            reply_markup=get_tracking_interval_keyboard(is_premium, lang),
            parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("track_interval:"))
async def callback_track_interval(callback: CallbackQuery, state: FSMContext):
    interval = int(callback.data.split(":")[1])
    data = await state.get_data()
    slug = data.get("slug")
    number = data.get("number")
    
    await state.clear()
    
    if not slug or not number:
        await callback.answer("Ошибка, попробуйте снова", show_alert=True)
        return
    
    async with async_session() as session:
        lang = await get_user_lang(session, callback.from_user.id)
        
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            await callback.answer("Ошибка", show_alert=True)
            return
        
        success, message = await tracking_service.add_tracking(
            session, user.id, callback.from_user.id, slug, number, interval
        )
        
        if success:
            if lang == "en":
                text = (
                    f"✅ <b>Tracking added!</b>\n\n"
                    f"Gift: {slug}-{number}\n"
                    f"Check interval: {interval} min\n\n"
                    f"You will receive notifications about:\n"
                    f"• Status changes (on sale, auction, sold)\n"
                    f"• Owner changes\n"
                    f"• Price changes\n"
                    f"• Gift hidden/unhidden"
                )
            else:
                text = (
                    f"✅ <b>Слежка добавлена!</b>\n\n"
                    f"Подарок: {slug}-{number}\n"
                    f"Интервал проверки: {interval} мин\n\n"
                    f"Вы будете получать уведомления о:\n"
                    f"• Изменении статуса (продажа, аукцион)\n"
                    f"• Смене владельца\n"
                    f"• Изменении цены\n"
                    f"• Скрытии/показе подарка"
                )
        else:
            if lang == "en":
                text = f"❌ Failed to add tracking:\n{message}"
            else:
                text = f"❌ Не удалось добавить слежку:\n{message}"
        
        trackings = await tracking_service.get_user_trackings(session, user.id)
        
        await callback.message.edit_text(
            text,
            reply_markup=get_tracking_menu(trackings, lang),
            parse_mode="HTML"
        )
        await callback.answer()


@router.callback_query(F.data.startswith("view_tracking:"))
async def callback_view_tracking(callback: CallbackQuery):
    tracking_id = int(callback.data.split(":")[1])
    
    async with async_session() as session:
        lang = await get_user_lang(session, callback.from_user.id)
        
        result = await session.execute(
            select(GiftTracking).where(GiftTracking.id == tracking_id)
        )
        tracking = result.scalar_one_or_none()
        
        if not tracking:
            await callback.answer("Слежка не найдена", show_alert=True)
            return
        
        if lang == "en":
            text = (
                f"👁 <b>Tracking: {tracking.slug}-{tracking.number}</b>\n\n"
                f"Owner: @{tracking.last_owner or 'Unknown'}\n"
                f"Status: {tracking.last_status or 'Unknown'}\n"
                f"Price: {tracking.last_price or 'N/A'} TON\n"
                f"Hidden: {'Yes' if tracking.is_hidden else 'No'}\n\n"
                f"Check interval: {tracking.check_interval} min\n"
                f"Last check: {tracking.last_checked.strftime('%d.%m %H:%M') if tracking.last_checked else 'Never'}"
            )
        else:
            text = (
                f"👁 <b>Слежка: {tracking.slug}-{tracking.number}</b>\n\n"
                f"Владелец: @{tracking.last_owner or 'Неизвестен'}\n"
                f"Статус: {tracking.last_status or 'Неизвестен'}\n"
                f"Цена: {tracking.last_price or 'Нет'} TON\n"
                f"Скрыт: {'Да' if tracking.is_hidden else 'Нет'}\n\n"
                f"Интервал проверки: {tracking.check_interval} мин\n"
                f"Последняя проверка: {tracking.last_checked.strftime('%d.%m %H:%M') if tracking.last_checked else 'Никогда'}"
            )
        
        await callback.message.edit_text(
            text,
            reply_markup=get_tracking_view_keyboard(tracking_id, lang),
            parse_mode="HTML"
        )
        await callback.answer()


@router.callback_query(F.data.startswith("remove_tracking:"))
async def callback_remove_tracking(callback: CallbackQuery):
    tracking_id = int(callback.data.split(":")[1])
    
    async with async_session() as session:
        lang = await get_user_lang(session, callback.from_user.id)
        
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            await callback.answer("Ошибка", show_alert=True)
            return
        
        success = await tracking_service.remove_tracking(session, tracking_id, user.id)
        
        if success:
            if lang == "en":
                await callback.answer("✅ Tracking removed", show_alert=True)
            else:
                await callback.answer("✅ Слежка удалена", show_alert=True)
        else:
            await callback.answer("❌ Ошибка", show_alert=True)
        
        trackings = await tracking_service.get_user_trackings(session, user.id)
        limit, min_interval = await tracking_service.get_tracking_limit(session, callback.from_user.id)
        is_premium = await is_user_premium(session, callback.from_user.id)
        
        if lang == "en":
            status = "⭐ Premium" if is_premium else "Standard"
            text = (
                f"👁 <b>Gift Tracking</b>\n\n"
                f"Status: {status}\n"
                f"Tracking limit: {len(trackings)}/{limit}\n\n"
                f"Your trackings:"
            )
        else:
            status = "⭐ Premium" if is_premium else "Стандарт"
            text = (
                f"👁 <b>Слежка за подарками</b>\n\n"
                f"Статус: {status}\n"
                f"Лимит слежек: {len(trackings)}/{limit}\n\n"
                f"Ваши слежки:"
            )
        
        if not trackings:
            if lang == "en":
                text += "\n\n<i>No active trackings</i>"
            else:
                text += "\n\n<i>Нет активных слежек</i>"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_tracking_menu(trackings, lang),
            parse_mode="HTML"
        )


@router.callback_query(F.data == "auto_search_menu")
async def callback_auto_search_menu(callback: CallbackQuery):
    async with async_session() as session:
        lang = await get_user_lang(session, callback.from_user.id)
        
        if lang == "en":
            text = (
                "🔔 <b>Auto-notifications</b>\n\n"
                "🚧 This feature is under development.\n\n"
                "Soon you will be able to set up automatic searches "
                "that run every 30 minutes and notify you about new finds."
            )
        else:
            text = (
                "🔔 <b>Автоуведомления</b>\n\n"
                "🚧 Функция в разработке.\n\n"
                "Скоро вы сможете настроить автоматические поиски, "
                "которые запускаются каждые 30 минут и уведомляют о новых находках."
            )
        
        await callback.message.edit_text(
            text,
            reply_markup=get_back_button("tools_menu"),
            parse_mode="HTML"
        )
        await callback.answer()
