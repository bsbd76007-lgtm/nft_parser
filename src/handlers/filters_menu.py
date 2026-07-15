"""
Handlers for:
  1. Quick search modes (light / medium / heavy)
  2. Blacklist management (gifts + sellers)
  5. Rare models toggle
  4. Backdrop filter (combined with the above)
  8. Combined multi-filter search
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select

from src.database.connection import async_session
from src.database.models import User, BlacklistGift, BlacklistSeller
from src.services.fragment_parser import fragment_parser
from src.services.filters_service import (
    GiftFilterCriteria, apply_gift_filters, get_quick_mode_label,
    add_gift_to_blacklist, add_seller_to_blacklist,
    get_blacklisted_gift_patterns, get_blacklisted_sellers,
)
from src.keyboards.inline import (
    get_quick_search_menu, get_adv_filters_menu, get_blacklist_menu,
    get_main_menu, get_back_button,
)
from src.handlers.search import get_search_keyboard

router = Router()


class AdvFilterStates(StatesGroup):
    waiting_backdrop = State()


class BlacklistStates(StatesGroup):
    waiting_gift_pattern = State()
    waiting_seller_username = State()


async def _get_or_create_user(session, tg_user) -> User:
    result = await session.execute(select(User).where(User.telegram_id == tg_user.id))
    user = result.scalar_one_or_none()
    if not user:
        user = User(telegram_id=tg_user.id, username=tg_user.username,
                     first_name=tg_user.first_name, last_name=tg_user.last_name)
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user


# ---------------------------------------------------------------------------
# 1. Quick search modes
# ---------------------------------------------------------------------------
@router.callback_query(F.data == "quick_search_menu")
async def callback_quick_search_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "⚡ <b>Быстрый поиск</b>\n\n"
        "Выберите режим по цене подарка:",
        reply_markup=get_quick_search_menu(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(
    F.data.startswith("quick_mode:"),
    ~F.message.text.contains("Выберите ценовой режим"),
)
async def callback_quick_mode(callback: CallbackQuery):
    mode = callback.data.split(":")[1]
    label = get_quick_mode_label(mode)

    from src.keyboards.inline import get_random_search_count_keyboard

    await callback.message.edit_text(
        f"⚡ <b>Быстрый поиск: {label}</b>\n\n"
        f"Выберите количество результатов:",
        reply_markup=get_random_search_count_keyboard(mode),
        parse_mode="HTML"
    )
    await callback.answer()


# ---------------------------------------------------------------------------
# 8. Combined / advanced filters
# ---------------------------------------------------------------------------
def _get_adv_state(fsm_data: dict) -> dict:
    return {
        "quick_mode": fsm_data.get("adv_quick_mode"),
        "backdrop": fsm_data.get("adv_backdrop"),
        "rare_only": fsm_data.get("adv_rare_only", False),
    }


@router.callback_query(F.data == "adv_filters_menu")
async def callback_adv_filters_menu(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await callback.message.edit_text(
        "🧰 <b>Расширенные фильтры</b>\n\n"
        "Комбинируйте несколько фильтров и запустите поиск сразу по всем:",
        reply_markup=get_adv_filters_menu(_get_adv_state(data)),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "adv_pick_mode")
async def callback_adv_pick_mode(callback: CallbackQuery):
    await callback.message.edit_text(
        "💰 Выберите ценовой режим:",
        reply_markup=get_quick_search_menu(),
        parse_mode="HTML"
    )
    # reuse quick_mode: callbacks but mark that we came from adv menu
    await callback.answer()


@router.callback_query(F.data.startswith("quick_mode:"), F.message.text.contains("Выберите ценовой режим"))
async def callback_adv_mode_selected(callback: CallbackQuery, state: FSMContext):
    mode = callback.data.split(":")[1]
    await state.update_data(adv_quick_mode=mode)
    data = await state.get_data()
    await callback.message.edit_text(
        "🧰 <b>Расширенные фильтры</b>\n\nКомбинируйте несколько фильтров:",
        reply_markup=get_adv_filters_menu(_get_adv_state(data)),
        parse_mode="HTML"
    )
    await callback.answer("Режим сохранён")


@router.callback_query(F.data == "adv_pick_backdrop")
async def callback_adv_pick_backdrop(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdvFilterStates.waiting_backdrop)
    await callback.message.edit_text(
        "🖼 Введите название фона (backdrop), по которому искать:",
        reply_markup=get_back_button("adv_filters_menu"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(AdvFilterStates.waiting_backdrop)
async def process_adv_backdrop(message: Message, state: FSMContext):
    await state.update_data(adv_backdrop=message.text.strip())
    await state.set_state(None)
    data = await state.get_data()
    await message.answer(
        "🧰 <b>Расширенные фильтры</b>\n\nКомбинируйте несколько фильтров:",
        reply_markup=get_adv_filters_menu(_get_adv_state(data)),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "adv_toggle_rare")
async def callback_adv_toggle_rare(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current = data.get("adv_rare_only", False)
    await state.update_data(adv_rare_only=not current)
    data = await state.get_data()
    await callback.message.edit_text(
        "🧰 <b>Расширенные фильтры</b>\n\nКомбинируйте несколько фильтров:",
        reply_markup=get_adv_filters_menu(_get_adv_state(data)),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "adv_apply")
async def callback_adv_apply(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id

    if fragment_parser.is_searching(user_id):
        await callback.answer("У вас уже есть активный поиск!", show_alert=True)
        return

    data = await state.get_data()
    criteria = GiftFilterCriteria(
        quick_mode=data.get("adv_quick_mode"),
        backdrop=data.get("adv_backdrop"),
        rare_models_only=data.get("adv_rare_only", False),
    )

    await callback.answer()
    progress_message = await callback.message.edit_text(
        "🧰 <b>Расширенный поиск</b>\n\n🔍 Применяем фильтры...",
        reply_markup=get_search_keyboard(user_id),
        parse_mode="HTML"
    )

    await _run_filtered_search(progress_message, user_id, criteria, title="🧰 Расширенный поиск")


async def _run_filtered_search(progress_message, user_id: int, criteria: GiftFilterCriteria, title: str,
                                target: int = 15):
    from src.handlers.search import search_results_cache, show_results_page
    from src.services.filters_service import QUICK_MODES, get_blacklisted_sellers

    async def update_progress(found, target_count, attempts, gift):
        try:
            await progress_message.edit_text(
                f"{title}\n\n🔍 Проверено кандидатов: {attempts}\n✅ Найдено: {found}",
                reply_markup=get_search_keyboard(user_id),
                parse_mode="HTML"
            )
        except Exception:
            pass

    cfg = QUICK_MODES.get(criteria.quick_mode, {}) if criteria.quick_mode else {}

    result = await fragment_parser.search_gifts_filtered(
        user_id=user_id,
        min_price=cfg.get("min_price"),
        max_price=cfg.get("max_price"),
        backdrop=criteria.backdrop,
        rare_only=criteria.rare_models_only,
        rare_threshold=criteria.rare_threshold,
        max_results=target,
        max_total_attempts=4000,
        batch_size=10,
        progress_callback=update_progress,
    )

    gifts = result.get("gifts", [])

    if gifts:
        async with async_session() as session:
            blacklisted = set(await get_blacklisted_sellers(session))
        if blacklisted:
            gifts = [g for g in gifts if not (g.owner and g.owner.lower() in blacklisted)]

    if gifts:
        search_results_cache[user_id] = {
            "slug": "filtered",
            "collection_name": title,
            "gifts": gifts,
            "total": len(gifts),
            "image_url": None,
            "debug": result.get("debug"),
        }
        await show_results_page(progress_message, user_id, page=1, is_first=True)
    else:
        from src.handlers.search import format_debug_diagnostics
        diag = format_debug_diagnostics(result)
        await progress_message.edit_text(
            f"{title}\n\n😔 По этим фильтрам ничего не нашлось. Попробуйте изменить критерии."
            + (f"\n\n{diag}" if diag else ""),
            reply_markup=get_main_menu(),
            parse_mode="HTML"
        )


# ---------------------------------------------------------------------------
# 2. Blacklist management
# ---------------------------------------------------------------------------
@router.callback_query(F.data == "blacklist_menu")
async def callback_blacklist_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "🚫 <b>Чёрный список</b>\n\n"
        "Скрывайте нежелательные подарки или продавцов из результатов поиска и уведомлений маркетплейса.",
        reply_markup=get_blacklist_menu(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "bl_add_gift")
async def callback_bl_add_gift(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BlacklistStates.waiting_gift_pattern)
    await callback.message.edit_text(
        "➕ Введите название подарка (или его часть) / slug коллекции, который нужно скрыть:",
        reply_markup=get_back_button("blacklist_menu"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(BlacklistStates.waiting_gift_pattern)
async def process_bl_add_gift(message: Message, state: FSMContext):
    await state.set_state(None)
    pattern = message.text.strip()

    async with async_session() as session:
        user = await _get_or_create_user(session, message.from_user)
        await add_gift_to_blacklist(session, user.id, name_pattern=pattern)

    await message.answer(
        f"✅ «{pattern}» добавлен(о) в чёрный список подарков.",
        reply_markup=get_blacklist_menu(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "bl_add_seller")
async def callback_bl_add_seller(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BlacklistStates.waiting_seller_username)
    await callback.message.edit_text(
        "➕ Введите username продавца (без @), которого нужно скрыть:",
        reply_markup=get_back_button("blacklist_menu"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(BlacklistStates.waiting_seller_username)
async def process_bl_add_seller(message: Message, state: FSMContext):
    await state.set_state(None)
    username = message.text.strip().lstrip("@")

    async with async_session() as session:
        user = await _get_or_create_user(session, message.from_user)
        await add_seller_to_blacklist(session, user.id, username=username)

    await message.answer(
        f"✅ @{username} добавлен в чёрный список продавцов.",
        reply_markup=get_blacklist_menu(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "bl_list_gifts")
async def callback_bl_list_gifts(callback: CallbackQuery):
    async with async_session() as session:
        patterns = await get_blacklisted_gift_patterns(session)

    if not patterns:
        text = "📋 Чёрный список подарков пуст."
    else:
        lines = [f"• {p['slug'] or p['name_pattern']}" for p in patterns]
        text = "📋 <b>Чёрный список подарков:</b>\n\n" + "\n".join(lines)

    await callback.message.edit_text(text, reply_markup=get_blacklist_menu(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "bl_list_sellers")
async def callback_bl_list_sellers(callback: CallbackQuery):
    async with async_session() as session:
        sellers = await get_blacklisted_sellers(session)

    if not sellers:
        text = "📋 Чёрный список продавцов пуст."
    else:
        text = "📋 <b>Чёрный список продавцов:</b>\n\n" + "\n".join(f"• @{s}" for s in sellers)

    await callback.message.edit_text(text, reply_markup=get_blacklist_menu(), parse_mode="HTML")
    await callback.answer()
