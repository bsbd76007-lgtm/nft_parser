from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, CommandStart
from aiogram.exceptions import TelegramBadRequest

from src.database.connection import async_session
from src.services.user_service import user_service
from src.services.settings_service import settings_service
from src.keyboards.inline import get_main_menu, get_admin_menu

router = Router()


async def check_subscription(bot, user_id: int, channel: str) -> bool:
    try:
        if channel.startswith("@"):
            channel_id = channel
        elif channel.startswith("-100"):
            channel_id = int(channel)
        else:
            channel_id = "@" + channel

        member = await bot.get_chat_member(channel_id, user_id)
        return member.status in ["creator", "administrator", "member"]
    except Exception:
        return True


def get_subscription_keyboard(channel: str) -> InlineKeyboardMarkup:
    if channel.startswith("@"):
        url = f"https://t.me/{channel[1:]}"
    elif channel.startswith("-100"):
        url = f"https://t.me/c/{channel[4:]}"
    else:
        url = f"https://t.me/{channel}"

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Подписаться на канал", url=url)],
        [
            InlineKeyboardButton(text="✅ Я подписался",
                                 callback_data="check_subscription")
        ]
    ])


WELCOME_MESSAGE = """
<b>🎁 NFT Gift Parser</b>

Поиск NFT-подарков Telegram с Telegram владельцами в реальном времени.

<b>Что я делаю:</b>
🔍 Ищу NFT подарки
👤 Нахожу подарки и Telegram владельцев
❌ Исключаю кошельки и удалённые аккаунты
💎 Показываю цены и атрибуты

Выберите действие:
"""

HELP_MESSAGE = """
<b>📖 Справка</b>

<b>Основные команды:</b>
/find - 🔍 Поиск подарков с TG владельцами
/stats - 📊 Статистика поисков

<b>Как работает поиск:</b>
1. Выбираете коллекцию подарков
2. Бот ищет подарки
3. Показывает только те, где владелец - Telegram аккаунт
4. Исключает кошельки и удалённые аккаунты

<b>Информация о подарке:</b>
• Название и номер
• Telegram владелец (@username)
• Цена в TON
• Атрибуты (Model, Backdrop, Symbol)
• Редкость атрибутов
"""


@router.message(CommandStart())
async def cmd_start(message: Message):
    if message.from_user:
        try:
            async with async_session() as session:
                await user_service.get_or_create_user(
                    session,
                    telegram_id=message.from_user.id,
                    username=message.from_user.username,
                    first_name=message.from_user.first_name,
                    last_name=message.from_user.last_name)

                is_required = await settings_service.is_subscription_required(
                    session)
                if is_required:
                    channel = await settings_service.get_subscription_channel(
                        session)
                    if channel:
                        is_subscribed = await check_subscription(
                            message.bot, message.from_user.id, channel)
                        if not is_subscribed:
                            await message.answer(
                                "📢 <b>Требуется подписка</b>\n\n"
                                "Для использования бота необходимо подписаться на наш канал.\n\n"
                                "После подписки нажмите кнопку «Я подписался».",
                                reply_markup=get_subscription_keyboard(
                                    channel),
                                parse_mode="HTML")
                            return
        except Exception:
            pass

    await message.answer(WELCOME_MESSAGE,
                         reply_markup=get_main_menu(),
                         parse_mode="HTML")


@router.callback_query(F.data == "check_subscription")
async def callback_check_subscription(callback: CallbackQuery):
    async with async_session() as session:
        is_required = await settings_service.is_subscription_required(session)
        if not is_required:
            await callback.message.edit_text(WELCOME_MESSAGE,
                                             reply_markup=get_main_menu(),
                                             parse_mode="HTML")
            await callback.answer()
            return

        channel = await settings_service.get_subscription_channel(session)
        if not channel:
            await callback.message.edit_text(WELCOME_MESSAGE,
                                             reply_markup=get_main_menu(),
                                             parse_mode="HTML")
            await callback.answer()
            return

        is_subscribed = await check_subscription(callback.bot,
                                                 callback.from_user.id,
                                                 channel)

        if is_subscribed:
            await callback.message.edit_text(WELCOME_MESSAGE,
                                             reply_markup=get_main_menu(),
                                             parse_mode="HTML")
            await callback.answer("✅ Подписка подтверждена!")
        else:
            await callback.answer("❌ Вы не подписаны на канал!",
                                  show_alert=True)


@router.callback_query(F.data == "main_menu")
async def callback_main_menu(callback: CallbackQuery):
    try:
        if callback.message.photo:
            await callback.message.delete()
            await callback.message.answer(WELCOME_MESSAGE,
                                          reply_markup=get_main_menu(),
                                          parse_mode="HTML")
        else:
            await callback.message.edit_text(WELCOME_MESSAGE,
                                             reply_markup=get_main_menu(),
                                             parse_mode="HTML")
    except TelegramBadRequest:
        try:
            await callback.message.answer(WELCOME_MESSAGE,
                                          reply_markup=get_main_menu(),
                                          parse_mode="HTML")
        except:
            pass
    await callback.answer()


@router.callback_query(F.data == "help")
async def callback_help(callback: CallbackQuery):
    from src.keyboards.inline import get_back_button
    try:
        await callback.message.edit_text(HELP_MESSAGE,
                                         reply_markup=get_back_button(),
                                         parse_mode="HTML")
    except TelegramBadRequest:
        pass
    await callback.answer()


@router.message(Command("help"))
async def cmd_help(message: Message):
    from src.keyboards.inline import get_back_button
    await message.answer(HELP_MESSAGE,
                         reply_markup=get_back_button(),
                         parse_mode="HTML")


@router.callback_query(F.data == "show_stats")
async def callback_show_stats(callback: CallbackQuery):
    from src.services.fragment_parser import fragment_parser
    from src.keyboards.inline import get_back_button

    stats = fragment_parser.get_global_stats()

    uptime_sec = stats["uptime_seconds"]
    if uptime_sec >= 3600:
        uptime_str = f"{uptime_sec // 3600}ч {(uptime_sec % 3600) // 60}м"
    elif uptime_sec >= 60:
        uptime_str = f"{uptime_sec // 60}м {uptime_sec % 60}с"
    else:
        uptime_str = f"{uptime_sec}с"

    total_attempts = stats["total_attempts"]
    total_found = stats["total_found"]
    conversion = round(total_found / total_attempts *
                       100, 1) if total_attempts > 0 else 0

    collections_count = len(fragment_parser.get_all_collections())

    text = (f"📊 <b>Статистика</b>\n\n"
            f"📦 Коллекций: {collections_count}\n"
            f"⏱ Аптайм: {uptime_str}\n"
            f"🔄 Активных поисков: {stats['active_searches']}\n\n"
            f"🔍 <b>Поиски:</b>\n"
            f"• Всего: {stats['total_searches']}\n"
            f"• Завершено: {stats['completed_searches']}\n"
            f"• Отменено: {stats['cancelled_searches']}\n\n"
            f"📈 <b>Результаты:</b>\n"
            f"• Проверено NFT: {total_attempts}\n"
            f"• Найдено с TG: {total_found}\n"
            f"• Конверсия: {conversion}%")

    try:
        await callback.message.edit_text(text,
                                         reply_markup=get_back_button(),
                                         parse_mode="HTML")
    except TelegramBadRequest:
        pass
    await callback.answer()


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not message.from_user:
        return

    try:
        async with async_session() as session:
            is_admin = await user_service.is_admin(session,
                                                   message.from_user.id)

            if not is_admin:
                await message.answer("У вас нет доступа к админ-панели.")
                return

            await message.answer("<b>Админ-панель</b>\n\nВыберите действие:",
                                 reply_markup=get_admin_menu(),
                                 parse_mode="HTML")
    except Exception:
        await message.answer("Ошибка проверки прав доступа.")
