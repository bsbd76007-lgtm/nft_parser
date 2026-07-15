import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from src.database.connection import async_session
from src.services.user_service import user_service
from src.services.settings_service import settings_service
from src.keyboards.inline import get_admin_menu, get_back_button, get_confirm_keyboard, get_subscription_settings_keyboard
from src.config import ADMINS

router = Router()


class AdminStates(StatesGroup):
    waiting_broadcast_message = State()
    waiting_admin_id = State()
    waiting_channel_link = State()
    waiting_premium_id = State()


@router.callback_query(F.data == "admin_stats")
async def callback_admin_stats(callback: CallbackQuery):
    async with async_session() as session:
        is_admin = await user_service.is_admin(session, callback.from_user.id)
        
        if not is_admin:
            await callback.answer("Нет доступа", show_alert=True)
            return
        
        users_count = await user_service.get_users_count(session)
        premium_count = await user_service.get_premium_count(session)
        
        from src.services.fragment_parser import fragment_parser
        collections_count = len(fragment_parser.get_all_collections())
        stats = fragment_parser.get_global_stats()
        
        text = f"""📊 <b>Статистика бота</b>

👥 Пользователей: {users_count}
⭐ Premium: {premium_count}
📦 Коллекций: {collections_count}

🔍 <b>Поиск:</b>
• Всего поисков: {stats['total_searches']}
• Найдено с TG: {stats['total_found']}
"""
        
        if callback.message:
            await callback.message.edit_text(
                text,
                reply_markup=get_admin_menu(),
                parse_mode="HTML"
            )
        await callback.answer()


@router.callback_query(F.data == "admin_broadcast")
async def callback_admin_broadcast(callback: CallbackQuery, state: FSMContext):
    async with async_session() as session:
        is_admin = await user_service.is_admin(session, callback.from_user.id)
        
        if not is_admin:
            await callback.answer("Нет доступа", show_alert=True)
            return
        
        await state.set_state(AdminStates.waiting_broadcast_message)
        await callback.message.edit_text(
            "📣 <b>Рассылка</b>\n\n"
            "Отправьте сообщение для рассылки всем пользователям.\n\n"
            "✅ Поддерживается:\n"
            "• Текст с форматированием (HTML)\n"
            "• Фото с подписью\n"
            "• Эмодзи\n\n"
            "💡 Можете прикрепить фото к сообщению.",
            reply_markup=get_back_button("admin_menu"),
            parse_mode="HTML"
        )
        await callback.answer()


@router.callback_query(F.data == "admin_menu")
async def callback_admin_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    
    async with async_session() as session:
        is_admin = await user_service.is_admin(session, callback.from_user.id)
        
        if not is_admin:
            await callback.answer("Нет доступа", show_alert=True)
            return
        
        await callback.message.edit_text(
            "🔧 <b>Админ-панель</b>\n\nВыберите действие:",
            reply_markup=get_admin_menu(),
            parse_mode="HTML"
        )
        await callback.answer()


@router.message(AdminStates.waiting_broadcast_message)
async def process_broadcast_message(message: Message, state: FSMContext):
    async with async_session() as session:
        is_admin = await user_service.is_admin(session, message.from_user.id)
        
        if not is_admin:
            await state.clear()
            return
        
        broadcast_text = message.text or message.caption or ""
        photo_file_id = None
        
        if message.photo:
            photo_file_id = message.photo[-1].file_id
        
        if not broadcast_text and not photo_file_id:
            await message.answer(
                "❌ Отправьте текст или фото с подписью:",
                reply_markup=get_back_button("admin_menu")
            )
            return
        
        await state.update_data(broadcast_text=broadcast_text, photo_file_id=photo_file_id)
        
        preview = broadcast_text[:500] + "..." if len(broadcast_text) > 500 else broadcast_text
        photo_text = "\n\n📷 <i>С прикрепленным фото</i>" if photo_file_id else ""
        
        if photo_file_id:
            await message.answer_photo(
                photo=photo_file_id,
                caption=f"👁 <b>Предпросмотр рассылки:</b>\n\n{preview}{photo_text}\n\n<b>Отправить?</b>",
                reply_markup=get_confirm_keyboard("broadcast"),
                parse_mode="HTML"
            )
        else:
            await message.answer(
                f"👁 <b>Предпросмотр рассылки:</b>\n\n{preview}\n\n<b>Отправить?</b>",
                reply_markup=get_confirm_keyboard("broadcast"),
                parse_mode="HTML"
            )


@router.callback_query(F.data.startswith("confirm_broadcast:"))
async def callback_confirm_broadcast(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    broadcast_text = data.get("broadcast_text", "")
    photo_file_id = data.get("photo_file_id")
    
    if not broadcast_text and not photo_file_id:
        await callback.answer("Сообщение для рассылки не найдено", show_alert=True)
        await state.clear()
        return
    
    await state.clear()
    
    async with async_session() as session:
        users = await user_service.get_all_users(session)
        
        sent = 0
        failed = 0
        
        if callback.message.photo:
            await callback.message.delete()
            status_message = await callback.message.answer(
                f"📣 <b>Рассылка...</b>\n\nОтправлено: 0/{len(users)}",
                parse_mode="HTML"
            )
        else:
            status_message = await callback.message.edit_text(
                f"📣 <b>Рассылка...</b>\n\nОтправлено: 0/{len(users)}",
                parse_mode="HTML"
            )
        
        for user in users:
            try:
                if photo_file_id:
                    await callback.bot.send_photo(
                        user.telegram_id,
                        photo=photo_file_id,
                        caption=broadcast_text,
                        parse_mode="HTML"
                    )
                else:
                    await callback.bot.send_message(
                        user.telegram_id,
                        broadcast_text,
                        parse_mode="HTML"
                    )
                sent += 1
            except Exception:
                failed += 1
            
            if sent % 10 == 0:
                try:
                    await status_message.edit_text(
                        f"📣 <b>Рассылка...</b>\n\nОтправлено: {sent}/{len(users)}",
                        parse_mode="HTML"
                    )
                except Exception:
                    pass
            
            await asyncio.sleep(0.05)
        
        await status_message.edit_text(
            f"✅ <b>Рассылка завершена!</b>\n\n"
            f"📨 Отправлено: {sent}\n"
            f"❌ Ошибок: {failed}",
            reply_markup=get_admin_menu(),
            parse_mode="HTML"
        )


@router.callback_query(F.data == "admin_subscription")
async def callback_admin_subscription(callback: CallbackQuery):
    async with async_session() as session:
        is_admin = await user_service.is_admin(session, callback.from_user.id)
        
        if not is_admin:
            await callback.answer("Нет доступа", show_alert=True)
            return
        
        is_enabled = await settings_service.is_subscription_required(session)
        channel = await settings_service.get_subscription_channel(session)
        
        text = (
            "📢 <b>Настройки подписки на канал</b>\n\n"
            f"Статус: {'✅ Включена' if is_enabled else '❌ Выключена'}\n"
        )
        
        if channel:
            text += f"Канал: {channel}\n"
        else:
            text += "Канал: <i>не установлен</i>\n"
        
        text += "\n⚠️ Пользователи должны быть подписаны на канал, чтобы использовать бота."
        
        await callback.message.edit_text(
            text,
            reply_markup=get_subscription_settings_keyboard(is_enabled, channel),
            parse_mode="HTML"
        )
        await callback.answer()


@router.callback_query(F.data == "toggle_subscription")
async def callback_toggle_subscription(callback: CallbackQuery):
    async with async_session() as session:
        is_admin = await user_service.is_admin(session, callback.from_user.id)
        
        if not is_admin:
            await callback.answer("Нет доступа", show_alert=True)
            return
        
        current = await settings_service.is_subscription_required(session)
        await settings_service.set_subscription_required(session, not current)
        
        is_enabled = not current
        channel = await settings_service.get_subscription_channel(session)
        
        text = (
            "📢 <b>Настройки подписки на канал</b>\n\n"
            f"Статус: {'✅ Включена' if is_enabled else '❌ Выключена'}\n"
        )
        
        if channel:
            text += f"Канал: {channel}\n"
        else:
            text += "Канал: <i>не установлен</i>\n"
        
        text += "\n⚠️ Пользователи должны быть подписаны на канал, чтобы использовать бота."
        
        await callback.message.edit_text(
            text,
            reply_markup=get_subscription_settings_keyboard(is_enabled, channel),
            parse_mode="HTML"
        )
        await callback.answer("Настройки сохранены!")


@router.callback_query(F.data == "change_channel")
async def callback_change_channel(callback: CallbackQuery, state: FSMContext):
    async with async_session() as session:
        is_admin = await user_service.is_admin(session, callback.from_user.id)
        
        if not is_admin:
            await callback.answer("Нет доступа", show_alert=True)
            return
        
        await state.set_state(AdminStates.waiting_channel_link)
        await callback.message.edit_text(
            "📝 <b>Изменение канала подписки</b>\n\n"
            "Отправьте ссылку на канал или его @username:\n\n"
            "Примеры:\n"
            "• @mychannel\n"
            "• https://t.me/mychannel\n"
            "• -1001234567890 (ID канала)",
            reply_markup=get_back_button("admin_subscription"),
            parse_mode="HTML"
        )
        await callback.answer()


@router.message(AdminStates.waiting_channel_link)
async def process_channel_link(message: Message, state: FSMContext):
    async with async_session() as session:
        is_admin = await user_service.is_admin(session, message.from_user.id)
        
        if not is_admin:
            await state.clear()
            return
        
        channel_input = message.text.strip()
        
        if channel_input.startswith("https://t.me/"):
            channel = "@" + channel_input.replace("https://t.me/", "")
        elif channel_input.startswith("t.me/"):
            channel = "@" + channel_input.replace("t.me/", "")
        elif channel_input.startswith("@"):
            channel = channel_input
        elif channel_input.startswith("-100"):
            channel = channel_input
        else:
            channel = "@" + channel_input
        
        await settings_service.set_subscription_channel(session, channel)
        await state.clear()
        
        is_enabled = await settings_service.is_subscription_required(session)
        
        await message.answer(
            f"✅ Канал успешно изменен на: <b>{channel}</b>",
            reply_markup=get_subscription_settings_keyboard(is_enabled, channel),
            parse_mode="HTML"
        )


@router.callback_query(F.data == "admin_manage")
async def callback_admin_manage(callback: CallbackQuery, state: FSMContext):
    async with async_session() as session:
        is_superadmin = await user_service.is_superadmin(session, callback.from_user.id)
        
        if not is_superadmin:
            await callback.answer("Только для суперадминов", show_alert=True)
            return
        
        await state.set_state(AdminStates.waiting_admin_id)
        await callback.message.edit_text(
            "👥 <b>Управление админами</b>\n\n"
            "Введите Telegram ID пользователя для назначения/снятия админа:",
            reply_markup=get_back_button("admin_menu"),
            parse_mode="HTML"
        )
        await callback.answer()


@router.message(AdminStates.waiting_admin_id)
async def process_admin_id(message: Message, state: FSMContext):
    async with async_session() as session:
        is_superadmin = await user_service.is_superadmin(session, message.from_user.id)
        
        if not is_superadmin:
            await state.clear()
            return
        
        try:
            target_id = int(message.text.strip())
        except ValueError:
            await message.answer("❌ Введите корректный Telegram ID (число):")
            return
        
        await state.clear()
        
        target_user = await user_service.get_user_by_telegram_id(session, target_id)
        
        if not target_user:
            await message.answer(
                f"❌ Пользователь с ID {target_id} не найден в базе.\n\n"
                f"Он должен сначала написать боту /start",
                reply_markup=get_admin_menu()
            )
            return
        
        new_status = not target_user.is_admin
        await user_service.set_admin(session, target_id, new_status)
        
        status_text = "✅ назначен админом" if new_status else "❌ снят с админа"
        
        await message.answer(
            f"Пользователь <b>{target_user.first_name or target_id}</b> {status_text}.",
            reply_markup=get_admin_menu(),
            parse_mode="HTML"
        )


@router.callback_query(F.data == "admin_premium")
async def callback_admin_premium(callback: CallbackQuery, state: FSMContext):
    async with async_session() as session:
        is_admin = await user_service.is_admin(session, callback.from_user.id)
        
        if not is_admin:
            await callback.answer("Нет доступа", show_alert=True)
            return
        
        premium_users = await user_service.get_premium_users(session)
        
        text = "⭐ <b>Premium пользователи</b>\n\n"
        
        if premium_users:
            for user in premium_users[:20]:
                name = user.username or user.first_name or str(user.telegram_id)
                text += f"• {name} (ID: {user.telegram_id})\n"
        else:
            text += "<i>Нет premium пользователей</i>\n"
        
        text += "\n💡 Отправьте Telegram ID чтобы добавить/убрать premium"
        
        await state.set_state(AdminStates.waiting_premium_id)
        await callback.message.edit_text(
            text,
            reply_markup=get_back_button("admin_menu"),
            parse_mode="HTML"
        )
        await callback.answer()


@router.message(AdminStates.waiting_premium_id)
async def process_premium_id(message: Message, state: FSMContext):
    async with async_session() as session:
        is_admin = await user_service.is_admin(session, message.from_user.id)
        
        if not is_admin:
            await state.clear()
            return
        
        try:
            target_id = int(message.text.strip())
        except ValueError:
            await message.answer("❌ Введите корректный Telegram ID (число):")
            return
        
        await state.clear()
        
        target_user = await user_service.get_user_by_telegram_id(session, target_id)
        
        if not target_user:
            await message.answer(
                f"❌ Пользователь с ID {target_id} не найден в базе.\n\n"
                f"Он должен сначала написать боту /start",
                reply_markup=get_admin_menu()
            )
            return
        
        new_status = not target_user.is_premium
        await user_service.set_premium(session, target_id, new_status)
        
        status_text = "⭐ добавлен в Premium" if new_status else "удалён из Premium"
        
        await message.answer(
            f"Пользователь <b>{target_user.first_name or target_id}</b> {status_text}.\n\n"
            f"Premium-преимущества:\n"
            f"• До 5 слежек за подарками\n"
            f"• Интервал проверки от 10 минут\n"
            f"• Приоритетный автопоиск",
            reply_markup=get_admin_menu(),
            parse_mode="HTML"
        )


async def setup_initial_admins():
    if not ADMINS:
        return
    
    async with async_session() as session:
        for admin_id in ADMINS:
            user = await user_service.get_user_by_telegram_id(session, admin_id)
            if user:
                await user_service.set_superadmin(session, admin_id, True)
