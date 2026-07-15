import csv
import io
import math
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, LinkPreviewOptions, BufferedInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest
from cachetools import TTLCache

from src.services.fragment_parser import fragment_parser, GiftData
from src.services.filters_service import get_gift_emoji, is_rare_model
from src.database.connection import async_session
from src.keyboards.inline import (
    get_search_count_keyboard, 
    get_results_pagination_keyboard,
    get_random_search_count_keyboard,
    get_random_mode_keyboard,
    get_filter_type_keyboard,
    get_filter_values_keyboard,
    get_filter_count_keyboard
)

router = Router()

COLLECTIONS_PER_PAGE = 9
RESULTS_PER_PAGE = 5

search_results_cache = TTLCache(maxsize=1000, ttl=3600)


class SearchStates(StatesGroup):
    waiting_for_query = State()
    waiting_custom_filter_value = State()


def get_collections_keyboard(page: int = 1) -> InlineKeyboardMarkup:
    collections = fragment_parser.get_all_collections()
    total_pages = math.ceil(len(collections) / COLLECTIONS_PER_PAGE)
    
    start = (page - 1) * COLLECTIONS_PER_PAGE
    end = start + COLLECTIONS_PER_PAGE
    page_items = collections[start:end]
    
    buttons = []
    row = []
    for col in page_items:
        display_name = col["name"][:12] + ".." if len(col["name"]) > 14 else col["name"]
        row.append(InlineKeyboardButton(
            text=display_name,
            callback_data=f"search:{col['slug']}"
        ))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    
    buttons.append([InlineKeyboardButton(
        text="🔍 Поиск по названию",
        callback_data="search_by_name"
    )])
    
    nav_row = []
    if page > 1:
        nav_row.append(InlineKeyboardButton(text="◀️", callback_data=f"collections_page:{page-1}"))
    nav_row.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        nav_row.append(InlineKeyboardButton(text="▶️", callback_data=f"collections_page:{page+1}"))
    buttons.append(nav_row)
    
    buttons.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_search_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛑 Остановить поиск", callback_data=f"stop_search:{user_id}")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])


def get_results_keyboard(slug: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Искать ещё", callback_data=f"search:{slug}")],
        [InlineKeyboardButton(text="📦 Другая коллекция", callback_data="find")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])


def format_debug_diagnostics(result: dict) -> str:
    """Turn the parser's debug stats into a short human-readable note so
    users can tell 'nothing matched' apart from 'requests are being
    throttled/blocked' instead of both looking like silent zero results."""
    debug = result.get("debug") or {}
    ok = debug.get("ok", 0)
    not_found = debug.get("not_found", 0)
    rate_limited = debug.get("rate_limited", 0)
    network_error = debug.get("network_error", 0)
    server_error = debug.get("server_error", 0)
    blocked_or_empty = debug.get("blocked_or_empty", 0)

    total_failures = rate_limited + network_error + server_error
    total_checked = ok + not_found + total_failures

    if total_checked == 0:
        return ""

    lines = [f"📊 Проверено запросов: {total_checked} (успешно: {ok}, не существует: {not_found})"]

    if blocked_or_empty > 0 and ok > 0:
        blocked_pct = round(blocked_or_empty / ok * 100)
        lines.append(f"🤖 Страниц без цены/статуса при HTTP 200: {blocked_or_empty} ({blocked_pct}%)")
        if blocked_pct > 50:
            lines.append(
                "🚫 Похоже, Fragment.com отдаёт страницу-заглушку/защиту от ботов вместо реальных данных."
            )

    if total_failures > 0:
        failure_pct = round(total_failures / total_checked * 100)
        lines.append(f"⚠️ Сетевых сбоев: {total_failures} ({failure_pct}%)")
        if rate_limited > total_checked * 0.15:
            lines.append(
                "🚫 Похоже, Telegram/Fragment ограничивают частоту запросов (много 429 ошибок). "
                "Попробуйте повторить поиск позже или с меньшим количеством результатов."
            )
        elif network_error > total_checked * 0.15:
            lines.append(
                "🌐 Много таймаутов/сетевых ошибок — проверьте соединение или повторите попытку."
            )

    return "\n".join(lines)


def format_gift_result(gift: GiftData, index: int) -> str:
    raw_name = gift.name or f"#{gift.number}"
    name = f"{get_gift_emoji(raw_name)} {raw_name}"
    username = gift.owner or "Unknown"
    gift_url = gift.tme_url or gift.fragment_url or f"https://t.me/nft/{gift.slug}-{gift.number}"
    
    status_emoji = ""
    if gift.status:
        if "auction" in gift.status.lower():
            status_emoji = "🔥"
        elif "sale" in gift.status.lower():
            status_emoji = "💰"
        elif "sold" in gift.status.lower():
            status_emoji = "✅"
    
    text = f"<b>{index}. {status_emoji} <a href=\"{gift_url}\">{name}</a></b>\n"
    text += f"   👤 <a href=\"https://t.me/{username}\">@{username}</a>\n"
    
    if gift.price_ton:
        price_str = f"💎 {gift.price_ton} TON"
        if gift.min_bid:
            price_str += f" (мин: {gift.min_bid})"
        if gift.status:
            price_str += f" | {gift.status}"
        text += f"   {price_str}\n"
    elif gift.status:
        text += f"   📊 {gift.status}\n"
    
    if gift.issued and gift.total_supply:
        text += f"   📦 {gift.issued:,}/{gift.total_supply:,} выпущено\n"
    
    attrs = []
    if gift.model:
        rarity = f" ({gift.model_rarity})" if gift.model_rarity else ""
        rare_marker = " 💎RARE" if is_rare_model(gift.model_rarity) else ""
        attrs.append(f"🎨 {gift.model}{rarity}{rare_marker}")
    if gift.backdrop:
        rarity = f" ({gift.backdrop_rarity})" if gift.backdrop_rarity else ""
        attrs.append(f"🖼 {gift.backdrop}{rarity}")
    if gift.symbol:
        rarity = f" ({gift.symbol_rarity})" if gift.symbol_rarity else ""
        attrs.append(f"✨ {gift.symbol}{rarity}")
    
    if attrs:
        text += f"   {' | '.join(attrs)}\n"
    
    return text


@router.message(Command("find"))
async def cmd_find(message: Message):
    collections = fragment_parser.get_all_collections()
    
    await message.answer(
        f"🔍 <b>Поиск NFT подарков</b>\n\n"
        f"📦 Доступно {len(collections)} коллекций\n\n"
        "Выберите коллекцию для поиска:",
        reply_markup=get_collections_keyboard(1),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "find")
async def callback_find(callback: CallbackQuery):
    collections = fragment_parser.get_all_collections()
    
    if callback.message:
        try:
            await callback.message.edit_text(
                f"🔍 <b>Поиск NFT подарков</b>\n\n"
                f"📦 Доступно {len(collections)} коллекций\n\n"
                "Выберите коллекцию для поиска:",
                reply_markup=get_collections_keyboard(1),
                parse_mode="HTML"
            )
        except TelegramBadRequest:
            pass
    await callback.answer()


@router.callback_query(F.data.startswith("collections_page:"))
async def callback_collections_page(callback: CallbackQuery):
    if not callback.data:
        return await callback.answer()
    page = int(callback.data.split(":")[1])
    collections = fragment_parser.get_all_collections()
    
    if callback.message:
        try:
            await callback.message.edit_text(
                f"🔍 <b>Поиск NFT подарков с Telegram владельцами</b>\n\n"
                f"📦 Доступно {len(collections)} коллекций\n\n"
                "Выберите коллекцию для поиска:",
                reply_markup=get_collections_keyboard(page),
                parse_mode="HTML"
            )
        except TelegramBadRequest:
            pass
    await callback.answer()


@router.callback_query(F.data == "search_by_name")
async def callback_search_by_name(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SearchStates.waiting_for_query)
    
    if callback.message:
        await callback.message.edit_text(
            "🔍 <b>Поиск по названию</b>\n\n"
            "Введите название подарка:\n"
            "<i>Например: Snoop Dogg, Plush Pepe, Loot Bag</i>",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад", callback_data="find")]
            ]),
            parse_mode="HTML"
        )
    await callback.answer()


@router.message(SearchStates.waiting_for_query)
async def process_search_query(message: Message, state: FSMContext):
    if not message.text:
        return
    query = message.text.strip()
    await state.clear()
    
    matching = fragment_parser.find_collection(query)
    
    if not matching:
        await message.answer(
            f"❌ Подарок '<b>{message.text}</b>' не найден.\n\n"
            "Выберите из списка:",
            reply_markup=get_collections_keyboard(1),
            parse_mode="HTML"
        )
        return
    
    if len(matching) == 1:
        col = matching[0]
        await message.answer(
            f"🎁 <b>{col['name']}</b>\n\n"
            f"Сколько подарков искать?\n\n"
            f"<i>Чем больше - тем дольше поиск</i>",
            reply_markup=get_search_count_keyboard(col['slug']),
            parse_mode="HTML"
        )
    else:
        buttons = []
        for col in matching[:9]:
            buttons.append([InlineKeyboardButton(
                text=col["name"],
                callback_data=f"search:{col['slug']}"
            )])
        buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="find")])
        
        await message.answer(
            f"🔍 Найдено {len(matching)} коллекций по запросу '<b>{message.text}</b>':\n\n"
            "Выберите нужную:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
            parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("search:"))
async def callback_search(callback: CallbackQuery):
    if not callback.data:
        return await callback.answer()
    slug = callback.data.split(":")[1]
    
    col = fragment_parser.get_collection_by_slug(slug)
    if not col:
        await callback.answer("Коллекция не найдена")
        return
    
    if callback.message:
        await callback.message.edit_text(
            f"🎁 <b>{col['name']}</b>\n\n"
            f"Сколько подарков искать?\n\n"
            f"<i>Чем больше - тем дольше поиск</i>",
            reply_markup=get_search_count_keyboard(slug),
            parse_mode="HTML"
        )
    await callback.answer()


@router.callback_query(F.data.startswith("select_count:"))
async def callback_select_count(callback: CallbackQuery):
    if not callback.data:
        return await callback.answer()
    slug = callback.data.split(":")[1]
    
    col = fragment_parser.get_collection_by_slug(slug)
    if not col:
        await callback.answer("Коллекция не найдена")
        return
    
    if callback.message:
        await callback.message.edit_text(
            f"🎁 <b>{col['name']}</b>\n\n"
            f"Сколько подарков искать?\n\n"
            f"<i>Чем больше - тем дольше поиск</i>",
            reply_markup=get_search_count_keyboard(slug),
            parse_mode="HTML"
        )
    await callback.answer()


@router.callback_query(F.data.startswith("search_count:"))
async def callback_search_count(callback: CallbackQuery):
    if not callback.data or not callback.message:
        return await callback.answer()
    parts = callback.data.split(":")
    slug = parts[1]
    max_results = int(parts[2])
    
    col = fragment_parser.get_collection_by_slug(slug)
    if not col:
        await callback.answer("Коллекция не найдена")
        return
    
    await callback.answer()
    await start_realtime_search(callback.message, slug, col["name"], callback.from_user.id, max_results)


async def start_realtime_search(message, slug: str, collection_name: str, user_id: int, max_results: int = 25):
    if not hasattr(message, 'edit_text'):
        return
    
    if fragment_parser.is_searching(user_id):
        try:
            await message.answer(
                "⚠️ У вас уже есть активный поиск.\n"
                "Дождитесь завершения или остановите его.",
                reply_markup=get_search_keyboard(user_id)
            )
        except Exception:
            pass
        return
    
    max_attempts = min(max_results * 10, 5000)
    
    try:
        status_msg = await message.edit_text(
            f"🔍 <b>Ищу подарки {collection_name}...</b>\n\n"
            f"🎯 Цель: {max_results} подарков\n"
            f"✅ Найдено: 0\n"
            f"🔄 Проверено: 0\n\n"
            f"<i>Ищу Telegram владельцев, цены и статус...</i>",
            reply_markup=get_search_keyboard(user_id),
            parse_mode="HTML"
        )
    except Exception:
        return
    
    found_count = 0
    last_update = 0
    
    async def progress_callback(found: int, target: int, attempts: int, gift: GiftData = None):
        nonlocal found_count, last_update
        
        if found != found_count or attempts - last_update >= 20:
            found_count = found
            last_update = attempts
            
            status_text = f"🔍 <b>Ищу подарки {collection_name}...</b>\n\n"
            status_text += f"🎯 Цель: {target}\n"
            status_text += f"✅ Найдено: {found}\n"
            status_text += f"🔄 Проверено: {attempts}\n"
            
            if gift and gift.status:
                status_text += f"\n🆕 Последний: {gift.status}"
                if gift.price_ton:
                    status_text += f" - {gift.price_ton} TON"
            
            try:
                await status_msg.edit_text(
                    status_text,
                    reply_markup=get_search_keyboard(user_id),
                    parse_mode="HTML"
                )
            except TelegramBadRequest:
                pass
    
    result = await fragment_parser.search_gifts_with_telegram_owners(
        slug=slug,
        user_id=user_id,
        max_results=max_results,
        max_attempts=max_attempts,
        batch_size=10,
        progress_callback=progress_callback
    )
    
    if result["gifts"]:
        gifts = result["gifts"]
        total = result['total_found']
        
        image_url = None
        if gifts:
            for g in gifts[:5]:
                if g.image_url:
                    image_url = g.image_url
                    break
        
        search_results_cache[user_id] = {
            "slug": slug,
            "collection_name": collection_name,
            "gifts": gifts,
            "total": total,
            "attempts": result['attempts'],
            "conversion": result['conversion'],
            "image_url": image_url,
            "debug": result.get("debug"),
        }
        
        await show_results_page(status_msg, user_id, 1, is_first=True)
    else:
        diag = format_debug_diagnostics(result)
        try:
            await status_msg.edit_text(
                f"❌ <b>{collection_name}</b>\n\n"
                f"Подарки с Telegram владельцами не найдены.\n"
                f"Проверено: {result['attempts']} подарков\n\n"
                f"Возможные причины:\n"
                f"• Все подарки принадлежат TON кошелькам\n"
                f"• Удалённые аккаунты\n\n"
                f"Попробуйте другую коллекцию."
                + (f"\n\n{diag}" if diag else ""),
                reply_markup=get_results_keyboard(slug),
                parse_mode="HTML"
            )
        except Exception:
            pass


async def show_results_page(message, user_id: int, page: int, is_first: bool = False):
    if user_id not in search_results_cache:
        return
    
    if not hasattr(message, 'edit_text') and not hasattr(message, 'edit_caption'):
        return
    
    data = search_results_cache[user_id]
    gifts = data["gifts"]
    total = data["total"]
    collection_name = data["collection_name"]
    slug = data["slug"]
    image_url = data.get("image_url")
    
    total_pages = math.ceil(len(gifts) / RESULTS_PER_PAGE)
    start = (page - 1) * RESULTS_PER_PAGE
    end = start + RESULTS_PER_PAGE
    page_gifts = gifts[start:end]
    
    text = f"🎁 <b>{collection_name}</b>\n"
    text += f"✅ Найдено {total} подарков с TG владельцами\n"

    diag = format_debug_diagnostics(data) if data.get("debug") else ""
    if diag:
        text += f"{diag}\n"

    text += "\n"
    
    for i, gift in enumerate(page_gifts, start + 1):
        text += format_gift_result(gift, i)
        text += "\n"
    
    keyboard = get_results_pagination_keyboard(slug, page, total_pages, total)
    
    try:
        if is_first and image_url:
            chat_id = message.chat.id
            bot = message.bot
            
            try:
                await message.delete()
            except:
                pass
            
            try:
                import aiohttp
                from aiogram.types import BufferedInputFile
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(image_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        if resp.status == 200:
                            image_data = await resp.read()
                            photo = BufferedInputFile(image_data, filename="gift.jpg")
                            
                            await bot.send_photo(
                                chat_id=chat_id,
                                photo=photo,
                                caption=text,
                                reply_markup=keyboard,
                                parse_mode="HTML"
                            )
                            return
            except Exception:
                pass
            
            await bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=keyboard,
                parse_mode="HTML",
                link_preview_options=LinkPreviewOptions(is_disabled=True)
            )
            return
        elif is_first:
            await message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode="HTML",
                link_preview_options=LinkPreviewOptions(is_disabled=True)
            )
        else:
            if hasattr(message, 'photo') and message.photo:
                await message.edit_caption(
                    caption=text,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
            else:
                await message.edit_text(
                    text,
                    reply_markup=keyboard,
                    parse_mode="HTML",
                    link_preview_options=LinkPreviewOptions(is_disabled=True)
                )
    except TelegramBadRequest:
        try:
            await message.answer(
                text,
                reply_markup=keyboard,
                parse_mode="HTML",
                link_preview_options=LinkPreviewOptions(is_disabled=True)
            )
        except:
            pass


@router.callback_query(F.data.startswith("results_page:"))
async def callback_results_page(callback: CallbackQuery):
    parts = callback.data.split(":")
    slug = parts[1]
    page = int(parts[2])
    
    user_id = callback.from_user.id
    
    if user_id not in search_results_cache:
        await callback.answer("Результаты устарели. Запустите новый поиск.")
        return
    
    await callback.answer()
    await show_results_page(callback.message, user_id, page)


@router.callback_query(F.data.startswith("stop_search:"))
async def callback_stop_search(callback: CallbackQuery):
    if not callback.data:
        return await callback.answer()
    user_id = int(callback.data.split(":")[1])
    
    if fragment_parser.stop_search(user_id):
        await callback.answer("🛑 Поиск остановлен")
    else:
        await callback.answer("Поиск уже завершён")


@router.callback_query(F.data == "noop")
async def callback_noop(callback: CallbackQuery):
    await callback.answer()


@router.message(Command("stats"))
async def cmd_stats(message: Message):
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
    conversion = round(total_found / total_attempts * 100, 1) if total_attempts > 0 else 0
    
    collections_count = len(fragment_parser.get_all_collections())
    
    text = (
        f"📊 <b>Статистика поиска</b>\n\n"
        f"📦 Коллекций: {collections_count}\n"
        f"⏱ Аптайм: {uptime_str}\n"
        f"🔄 Активных поисков: {stats['active_searches']}\n\n"
        f"🔍 <b>Поиски:</b>\n"
        f"• Всего запущено: {stats['total_searches']}\n"
        f"• Завершено: {stats['completed_searches']}\n"
        f"• Отменено: {stats['cancelled_searches']}\n\n"
        f"📈 <b>Результаты:</b>\n"
        f"• Проверено NFT: {total_attempts}\n"
        f"• Найдено с TG: {total_found}\n"
        f"• Конверсия: {conversion}%"
    )
    
    await message.answer(text, parse_mode="HTML")


@router.callback_query(F.data == "random_search")
async def callback_random_search(callback: CallbackQuery):
    if callback.message:
        await callback.message.edit_text(
            "🎲 <b>Случайный поиск</b>\n\n"
            "Поиск случайных подарков с Telegram владельцами из всех коллекций.\n\n"
            "Выберите ценовой режим:",
            reply_markup=get_random_mode_keyboard(),
            parse_mode="HTML"
        )
    await callback.answer()


@router.callback_query(F.data.startswith("random_mode:"))
async def callback_random_mode(callback: CallbackQuery):
    if not callback.data or not callback.message:
        return await callback.answer()
    mode = callback.data.split(":")[1]

    mode_labels = {
        "light": "🟢 Лёгкий (до 10 TON)",
        "medium": "🟡 Средний (10-50 TON)",
        "heavy": "🔴 Жирный (50+ TON)",
        "any": "🌈 Любая цена",
    }

    await callback.message.edit_text(
        f"🎲 <b>Случайный поиск</b>\n\n"
        f"Режим: {mode_labels.get(mode, mode)}\n\n"
        f"Выберите количество результатов:",
        reply_markup=get_random_search_count_keyboard(mode),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("random_count:"))
async def callback_random_count(callback: CallbackQuery):
    if not callback.data or not callback.message:
        return await callback.answer()
    parts = callback.data.split(":")
    count = int(parts[1])
    mode = parts[2] if len(parts) > 2 else "any"
    user_id = callback.from_user.id
    
    if fragment_parser.is_searching(user_id):
        await callback.answer("У вас уже есть активный поиск!", show_alert=True)
        return
    
    await callback.answer()

    mode_labels = {
        "light": "🟢 Лёгкий (до 10 TON)",
        "medium": "🟡 Средний (10-50 TON)",
        "heavy": "🔴 Жирный (50+ TON)",
        "any": "🌈 Любая цена",
    }
    mode_label = mode_labels.get(mode, mode)
    
    progress_message = await callback.message.edit_text(
        f"🎲 <b>Случайный поиск</b>\n\n"
        f"Режим: {mode_label}\n"
        f"🔍 Ищем {count} подарков...\n"
        f"⏳ Это может занять некоторое время.",
        reply_markup=get_search_keyboard(user_id),
        parse_mode="HTML"
    )
    
    async def update_progress(found: int, target: int, attempts: int, gift):
        try:
            progress = int((found / target) * 20)
            progress_bar = "▓" * progress + "░" * (20 - progress)
            
            text = (
                f"🎲 <b>Случайный поиск</b>\n\n"
                f"Режим: {mode_label}\n"
                f"[{progress_bar}] {found}/{target}\n"
                f"🔍 Проверено: {attempts}\n"
            )
            
            if gift:
                text += f"\n✅ +@{gift.owner}"
            
            await progress_message.edit_text(
                text,
                reply_markup=get_search_keyboard(user_id),
                parse_mode="HTML"
            )
        except Exception:
            pass

    if mode == "any":
        result = await fragment_parser.search_random_gifts(
            user_id=user_id,
            max_results=count,
            max_attempts_per_collection=50,
            batch_size=10,
            progress_callback=update_progress
        )
        gifts = result["gifts"]
    else:
        from src.services.filters_service import QUICK_MODES
        cfg = QUICK_MODES.get(mode, {})

        result = await fragment_parser.search_gifts_filtered(
            user_id=user_id,
            min_price=cfg.get("min_price"),
            max_price=cfg.get("max_price"),
            max_results=count,
            max_total_attempts=4000,
            batch_size=10,
            progress_callback=update_progress
        )
        gifts = result["gifts"]

    if gifts:
        from src.services.filters_service import get_blacklisted_sellers
        async with async_session() as session:
            blacklisted = set(await get_blacklisted_sellers(session))
        if blacklisted:
            gifts = [g for g in gifts if not (g.owner and g.owner.lower() in blacklisted)]
    
    if gifts:
        total = len(gifts)
        
        search_results_cache[user_id] = {
            "slug": "random",
            "collection_name": f"Случайные подарки — {mode_label}",
            "gifts": gifts,
            "total": total,
            "image_url": None,
            "debug": result.get("debug"),
        }
        
        await show_results_page(progress_message, user_id, page=1, is_first=True)
    else:
        from src.keyboards.inline import get_main_menu
        diag = format_debug_diagnostics(result)
        await progress_message.edit_text(
            "😔 Не удалось найти подарки с Telegram владельцами по этому режиму.\n\n"
            "Попробуйте еще раз."
            + (f"\n\n{diag}" if diag else ""),
            reply_markup=get_main_menu(),
            parse_mode="HTML"
        )


@router.callback_query(F.data == "filter_search")
async def callback_filter_search(callback: CallbackQuery):
    if callback.message:
        await callback.message.edit_text(
            f"🎯 <b>Поиск по {FILTER_TITLES['backdrop']}</b>\n\n"
            f"Выберите значение для поиска:",
            reply_markup=get_filter_values_keyboard("backdrop", page=1),
            parse_mode="HTML"
        )
    await callback.answer()


FILTER_NAMES = {
    "model": "модели",
    "backdrop": "фону", 
    "symbol": "узору"
}

FILTER_TITLES = {
    "model": "🎨 Модель (Model)",
    "backdrop": "🖼 Фон (Backdrop)",
    "symbol": "✨ Узор (Symbol)"
}


@router.callback_query(F.data.startswith("filter_type:"))
async def callback_filter_type(callback: CallbackQuery):
    if not callback.data:
        return await callback.answer()
    filter_type = callback.data.split(":")[1]
    
    if callback.message:
        await callback.message.edit_text(
            f"🎯 <b>Поиск по {FILTER_TITLES[filter_type]}</b>\n\n"
            f"Выберите значение для поиска:",
            reply_markup=get_filter_values_keyboard(filter_type, page=1),
            parse_mode="HTML"
        )
    await callback.answer()


@router.callback_query(F.data.startswith("filter_page:"))
async def callback_filter_page(callback: CallbackQuery):
    if not callback.data:
        return await callback.answer()
    parts = callback.data.split(":")
    filter_type = parts[1]
    page = int(parts[2])
    
    if callback.message:
        await callback.message.edit_text(
            f"🎯 <b>Поиск по {FILTER_TITLES[filter_type]}</b>\n\n"
            f"Выберите значение для поиска:",
            reply_markup=get_filter_values_keyboard(filter_type, page=page),
            parse_mode="HTML"
        )
    await callback.answer()


@router.callback_query(F.data.startswith("filter_custom:"))
async def callback_filter_custom(callback: CallbackQuery, state: FSMContext):
    if not callback.data:
        return await callback.answer()
    filter_type = callback.data.split(":")[1]
    await state.update_data(custom_filter_type=filter_type)
    await state.set_state(SearchStates.waiting_custom_filter_value)

    if callback.message:
        await callback.message.edit_text(
            f"✏️ Введите текст для поиска по {FILTER_NAMES.get(filter_type, filter_type)} "
            f"(можно часть названия):",
            reply_markup=get_back_button_for_filters(),
            parse_mode="HTML"
        )
    await callback.answer()


def get_back_button_for_filters():
    from src.keyboards.inline import get_back_button
    return get_back_button("filter_search")


@router.message(SearchStates.waiting_custom_filter_value)
async def process_custom_filter_value(message: Message, state: FSMContext):
    data = await state.get_data()
    filter_type = data.get("custom_filter_type", "backdrop")
    filter_value = (message.text or "").strip()
    await state.set_state(None)

    if not filter_value:
        await message.answer("Пустой запрос, попробуйте ещё раз.")
        return

    await message.answer(
        f"🎯 <b>Поиск по {FILTER_NAMES.get(filter_type, filter_type)}: {filter_value}</b>\n\n"
        f"Выберите количество результатов:",
        reply_markup=get_filter_count_keyboard(filter_type, filter_value),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("filter_val:"))
async def callback_filter_value(callback: CallbackQuery):
    if not callback.data:
        return await callback.answer()
    parts = callback.data.split(":")
    filter_type = parts[1]
    filter_value = parts[2]
    
    if callback.message:
        await callback.message.edit_text(
            f"🎯 <b>Поиск по {FILTER_NAMES[filter_type]}: {filter_value}</b>\n\n"
            f"Выберите количество результатов:",
            reply_markup=get_filter_count_keyboard(filter_type, filter_value),
            parse_mode="HTML"
        )
    await callback.answer()


@router.callback_query(F.data.startswith("filter_count:"))
async def callback_filter_count(callback: CallbackQuery):
    if not callback.data or not callback.message:
        return await callback.answer()
    parts = callback.data.split(":")
    filter_type = parts[1]
    filter_value = parts[2]
    max_results = int(parts[3])
    
    user_id = callback.from_user.id
    
    if fragment_parser.is_searching(user_id):
        await callback.answer("У вас уже есть активный поиск!", show_alert=True)
        return
    
    await callback.answer()
    
    progress_message = await callback.message.edit_text(
        f"🎯 <b>Поиск по {FILTER_NAMES[filter_type]}: {filter_value}</b>\n\n"
        f"🔍 Ищем подарки (0/{max_results})...\n"
        f"⏳ Это может занять некоторое время.",
        reply_markup=get_search_keyboard(user_id),
        parse_mode="HTML"
    )
    
    async def update_progress(found: int, target: int, attempts: int, gift):
        try:
            progress = int((found / target) * 20)
            progress_bar = "▓" * progress + "░" * (20 - progress)
            
            text = (
                f"🎯 <b>Поиск по {FILTER_NAMES[filter_type]}: {filter_value}</b>\n\n"
                f"[{progress_bar}] {found}/{target}\n"
                f"🔍 Проверено: {attempts}\n"
            )
            
            if gift:
                text += f"\n✅ +@{gift.owner}"
            
            await progress_message.edit_text(
                text,
                reply_markup=get_search_keyboard(user_id),
                parse_mode="HTML"
            )
        except Exception:
            pass
    
    result = await fragment_parser.search_by_filter(
        user_id=user_id,
        filter_type=filter_type,
        filter_value=filter_value,
        max_results=max_results,
        max_attempts_per_collection=50,
        batch_size=10,
        progress_callback=update_progress
    )
    
    if result["gifts"]:
        gifts = result["gifts"]
        total = result['total_found']
        
        search_results_cache[user_id] = {
            "slug": f"filter_{filter_type}_{filter_value}",
            "collection_name": f"По {FILTER_NAMES[filter_type]}: {filter_value}",
            "gifts": gifts,
            "total": total,
            "image_url": None
        }
        
        await show_results_page(progress_message, user_id, page=1, is_first=True)
    else:
        from src.keyboards.inline import get_main_menu
        await progress_message.edit_text(
            f"😔 Не удалось найти подарки с {FILTER_NAMES[filter_type]} <b>{filter_value}</b>.\n\n"
            f"Попробуйте другое значение.",
            reply_markup=get_main_menu(),
            parse_mode="HTML"
        )


@router.callback_query(F.data == "export_csv")
async def callback_export_csv(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    if user_id not in search_results_cache:
        await callback.answer("Нет данных для экспорта", show_alert=True)
        return
    
    cache_data = search_results_cache[user_id]
    gifts = cache_data.get("gifts", [])
    
    if not gifts:
        await callback.answer("Нет результатов для экспорта", show_alert=True)
        return
    
    await callback.answer("⏳ Создаю CSV файл...")
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        "№", "Slug", "Number", "Name", "Owner", "Owner Type",
        "Price TON", "Status", "Min Bid",
        "Model", "Model Rarity", "Backdrop", "Backdrop Rarity", 
        "Symbol", "Symbol Rarity", "Issued", "Total Supply",
        "Fragment URL", "t.me URL"
    ])
    
    for i, gift in enumerate(gifts, 1):
        writer.writerow([
            i,
            gift.slug,
            gift.number,
            gift.name or f"{gift.slug}-{gift.number}",
            gift.owner or "",
            gift.owner_type or "",
            gift.price_ton or "",
            gift.status or "",
            gift.min_bid or "",
            gift.model or "",
            gift.model_rarity or "",
            gift.backdrop or "",
            gift.backdrop_rarity or "",
            gift.symbol or "",
            gift.symbol_rarity or "",
            gift.issued or "",
            gift.total_supply or "",
            gift.fragment_url or f"https://fragment.com/gift/{gift.slug}-{gift.number}",
            f"https://t.me/nft/{gift.slug}-{gift.number}"
        ])
    
    csv_content = output.getvalue().encode('utf-8-sig')
    
    collection_name = cache_data.get("collection_name", "results")
    safe_name = "".join(c for c in collection_name if c.isalnum() or c in (' ', '-', '_')).strip()
    filename = f"nft_gifts_{safe_name[:30]}_{len(gifts)}.csv"
    
    document = BufferedInputFile(csv_content, filename=filename)
    
    if callback.message:
        await callback.message.answer_document(
            document,
            caption=f"📥 <b>Экспорт результатов</b>\n\n"
                    f"📊 {cache_data.get('collection_name', 'Результаты')}\n"
                    f"📝 Записей: {len(gifts)}",
            parse_mode="HTML"
        )
    
    await callback.answer("✅ CSV файл отправлен!")
