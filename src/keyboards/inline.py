from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List


def get_main_menu(lang: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    if lang == "en":
        builder.row(
            InlineKeyboardButton(text="🔍 Search by collection", callback_data="find")
        )
        builder.row(
            InlineKeyboardButton(text="🎲 Random search", callback_data="random_search"),
            InlineKeyboardButton(text="🎯 Filter search", callback_data="filter_search")
        )
        builder.row(
            InlineKeyboardButton(text="⚡ Quick search", callback_data="quick_search_menu"),
            InlineKeyboardButton(text="🧰 Advanced filters", callback_data="adv_filters_menu")
        )
        builder.row(
            InlineKeyboardButton(text="🏪 Marketplace", callback_data="marketplace_menu"),
            InlineKeyboardButton(text="🚫 Blacklist", callback_data="blacklist_menu")
        )
        builder.row(
            InlineKeyboardButton(text="🛠 Tools", callback_data="tools_menu"),
            InlineKeyboardButton(text="⚙️ Settings", callback_data="settings_menu")
        )
        builder.row(
            InlineKeyboardButton(text="📊 Stats", callback_data="show_stats"),
            InlineKeyboardButton(text="❓ Help", callback_data="help")
        )
    else:
        builder.row(
            InlineKeyboardButton(text="🔍 Поиск по коллекции", callback_data="find")
        )
        builder.row(
            InlineKeyboardButton(text="🎲 Случайный поиск", callback_data="random_search"),
            InlineKeyboardButton(text="🎯 Поиск по фильтрам", callback_data="filter_search")
        )
        builder.row(
            InlineKeyboardButton(text="⚡ Быстрый поиск", callback_data="quick_search_menu"),
            InlineKeyboardButton(text="🧰 Расширенные фильтры", callback_data="adv_filters_menu")
        )
        builder.row(
            InlineKeyboardButton(text="🏪 Маркетплейс", callback_data="marketplace_menu"),
            InlineKeyboardButton(text="🚫 Чёрный список", callback_data="blacklist_menu")
        )
        builder.row(
            InlineKeyboardButton(text="🛠 Инструменты", callback_data="tools_menu"),
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings_menu")
        )
        builder.row(
            InlineKeyboardButton(text="📊 Статистика", callback_data="show_stats"),
            InlineKeyboardButton(text="❓ Помощь", callback_data="help")
        )
    return builder.as_markup()


def get_admin_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats"),
        InlineKeyboardButton(text="📣 Рассылка", callback_data="admin_broadcast")
    )
    builder.row(
        InlineKeyboardButton(text="📢 Подписка на канал", callback_data="admin_subscription")
    )
    builder.row(
        InlineKeyboardButton(text="⭐ Premium пользователи", callback_data="admin_premium")
    )
    builder.row(
        InlineKeyboardButton(text="👥 Управление админами", callback_data="admin_manage")
    )
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")
    )
    return builder.as_markup()


def get_tools_menu(lang: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    if lang == "en":
        builder.row(
            InlineKeyboardButton(text="👁 Gift Tracking", callback_data="tracking_menu")
        )
        builder.row(
            InlineKeyboardButton(text="🔔 Auto-notifications", callback_data="auto_search_menu")
        )
        builder.row(
            InlineKeyboardButton(text="◀️ Back", callback_data="main_menu")
        )
    else:
        builder.row(
            InlineKeyboardButton(text="👁 Слежка за подарком", callback_data="tracking_menu")
        )
        builder.row(
            InlineKeyboardButton(text="🔔 Автоуведомления", callback_data="auto_search_menu")
        )
        builder.row(
            InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")
        )
    return builder.as_markup()


def get_settings_menu(lang: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    if lang == "en":
        builder.row(
            InlineKeyboardButton(text="🌍 Language: English", callback_data="set_lang:ru")
        )
        builder.row(
            InlineKeyboardButton(text="◀️ Back", callback_data="main_menu")
        )
    else:
        builder.row(
            InlineKeyboardButton(text="🌍 Язык: Русский", callback_data="set_lang:en")
        )
        builder.row(
            InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")
        )
    return builder.as_markup()


def get_tracking_menu(trackings: list, lang: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    for t in trackings[:5]:
        status = "🟢" if t.is_active else "🔴"
        builder.row(
            InlineKeyboardButton(
                text=f"{status} {t.slug}-{t.number}",
                callback_data=f"view_tracking:{t.id}"
            )
        )
    
    if lang == "en":
        builder.row(
            InlineKeyboardButton(text="➕ Add tracking", callback_data="add_tracking")
        )
        builder.row(
            InlineKeyboardButton(text="◀️ Back", callback_data="tools_menu")
        )
    else:
        builder.row(
            InlineKeyboardButton(text="➕ Добавить слежку", callback_data="add_tracking")
        )
        builder.row(
            InlineKeyboardButton(text="◀️ Назад", callback_data="tools_menu")
        )
    return builder.as_markup()


def get_tracking_interval_keyboard(is_premium: bool, lang: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    if is_premium:
        builder.row(
            InlineKeyboardButton(text="10 мин", callback_data="track_interval:10"),
            InlineKeyboardButton(text="30 мин", callback_data="track_interval:30"),
            InlineKeyboardButton(text="1 час", callback_data="track_interval:60")
        )
        builder.row(
            InlineKeyboardButton(text="3 часа", callback_data="track_interval:180"),
            InlineKeyboardButton(text="6 часов", callback_data="track_interval:360")
        )
    else:
        builder.row(
            InlineKeyboardButton(text="1 час (стандарт)", callback_data="track_interval:60")
        )
    
    back_text = "◀️ Back" if lang == "en" else "◀️ Назад"
    builder.row(InlineKeyboardButton(text=back_text, callback_data="tracking_menu"))
    return builder.as_markup()


def get_tracking_view_keyboard(tracking_id: int, lang: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    if lang == "en":
        builder.row(
            InlineKeyboardButton(text="🗑 Remove", callback_data=f"remove_tracking:{tracking_id}")
        )
        builder.row(
            InlineKeyboardButton(text="◀️ Back", callback_data="tracking_menu")
        )
    else:
        builder.row(
            InlineKeyboardButton(text="🗑 Удалить", callback_data=f"remove_tracking:{tracking_id}")
        )
        builder.row(
            InlineKeyboardButton(text="◀️ Назад", callback_data="tracking_menu")
        )
    return builder.as_markup()


def get_random_mode_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🟢 Лёгкий (до 10 TON)", callback_data="random_mode:light")
    )
    builder.row(
        InlineKeyboardButton(text="🟡 Средний (10-50 TON)", callback_data="random_mode:medium")
    )
    builder.row(
        InlineKeyboardButton(text="🔴 Жирный (50+ TON)", callback_data="random_mode:heavy")
    )
    builder.row(
        InlineKeyboardButton(text="🌈 Любая цена", callback_data="random_mode:any")
    )
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu"))
    return builder.as_markup()


def get_random_search_count_keyboard(mode: str = "any") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="10", callback_data=f"random_count:10:{mode}"),
        InlineKeyboardButton(text="25", callback_data=f"random_count:25:{mode}"),
        InlineKeyboardButton(text="50", callback_data=f"random_count:50:{mode}")
    )
    builder.row(
        InlineKeyboardButton(text="100", callback_data=f"random_count:100:{mode}"),
        InlineKeyboardButton(text="🔥 Максимум (200)", callback_data=f"random_count:200:{mode}")
    )
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="random_search"))
    return builder.as_markup()


def get_filter_type_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🖼 Фон (Backdrop)", callback_data="filter_type:backdrop")
    )
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu"))
    return builder.as_markup()


FILTER_VALUES = {
    "model": [
        "Gold", "Silver", "Bronze", "Platinum", "Diamond",
        "Green", "Blue", "Red", "Purple", "Pink",
        "White", "Black", "Orange", "Yellow", "Cyan",
        "Emerald", "Ruby", "Sapphire", "Amethyst", "Crystal",
        "Holographic", "Rainbow", "Neon", "Gradient", "Chrome",
        "Electric", "Cosmic", "Galaxy", "Mystic", "Royal"
    ],
    "backdrop": [
        "Black", "White", "Gold", "Silver", "Copper",
        "Blue", "Red", "Green", "Purple", "Pink",
        "Orange", "Yellow", "Cyan", "Magenta", "Teal",
        "Dark", "Light", "Gradient", "Rainbow", "Holographic",
        "Galaxy", "Cosmic", "Neon", "Electric", "Mystic",
        "Sunset", "Midnight", "Aurora", "Crystal", "Diamond"
    ],
    "symbol": [
        "Star", "Heart", "Crown", "Diamond", "Moon",
        "Sun", "Fire", "Lightning", "Snowflake", "Clover",
        "Skull", "Ghost", "Pumpkin", "Bat", "Spider",
        "Rose", "Lotus", "Butterfly", "Unicorn", "Dragon",
        "Pegasus", "Phoenix", "Angel", "Devil", "Wizard",
        "Rocket", "Planet", "Comet", "Gem", "Crystal"
    ]
}

ITEMS_PER_PAGE = 12


def get_filter_values_keyboard(filter_type: str, page: int = 1) -> InlineKeyboardMarkup:
    import math
    builder = InlineKeyboardBuilder()
    
    values = FILTER_VALUES.get(filter_type, [])
    total_pages = math.ceil(len(values) / ITEMS_PER_PAGE)
    
    start = (page - 1) * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    page_values = values[start:end]
    
    row = []
    for value in page_values:
        row.append(InlineKeyboardButton(
            text=value,
            callback_data=f"filter_val:{filter_type}:{value}"
        ))
        if len(row) == 3:
            builder.row(*row)
            row = []
    if row:
        builder.row(*row)
    
    nav_row = []
    if page > 1:
        nav_row.append(InlineKeyboardButton(text="◀️", callback_data=f"filter_page:{filter_type}:{page-1}"))
    nav_row.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        nav_row.append(InlineKeyboardButton(text="▶️", callback_data=f"filter_page:{filter_type}:{page+1}"))
    builder.row(*nav_row)
    
    builder.row(InlineKeyboardButton(text="✏️ Ввести свой вариант", callback_data=f"filter_custom:{filter_type}"))
    builder.row(InlineKeyboardButton(text="◀️ К выбору фильтра", callback_data="filter_search"))
    
    return builder.as_markup()


def get_filter_count_keyboard(filter_type: str, filter_value: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="10", callback_data=f"filter_count:{filter_type}:{filter_value}:10"),
        InlineKeyboardButton(text="25", callback_data=f"filter_count:{filter_type}:{filter_value}:25"),
        InlineKeyboardButton(text="50", callback_data=f"filter_count:{filter_type}:{filter_value}:50")
    )
    builder.row(
        InlineKeyboardButton(text="100", callback_data=f"filter_count:{filter_type}:{filter_value}:100"),
        InlineKeyboardButton(text="🔥 Максимум (200)", callback_data=f"filter_count:{filter_type}:{filter_value}:200")
    )
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data=f"filter_type:{filter_type}"))
    return builder.as_markup()


def get_subscription_settings_keyboard(enabled: bool, channel: str | None = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    status = "✅ Включена" if enabled else "❌ Выключена"
    builder.row(
        InlineKeyboardButton(
            text=f"Подписка: {status}",
            callback_data="toggle_subscription"
        )
    )
    if channel:
        builder.row(
            InlineKeyboardButton(text=f"Канал: {channel}", callback_data="noop")
        )
    builder.row(
        InlineKeyboardButton(text="📝 Изменить канал", callback_data="change_channel")
    )
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="admin_menu"))
    return builder.as_markup()


def get_back_button(callback_data: str = "main_menu") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data=callback_data))
    return builder.as_markup()


def get_filters_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="По фону (Backdrop)", callback_data="filter_backdrop"),
        InlineKeyboardButton(text="По узору (Symbol)", callback_data="filter_symbol")
    )
    builder.row(
        InlineKeyboardButton(text="По модели (Model)", callback_data="filter_model")
    )
    builder.row(
        InlineKeyboardButton(text="Назад", callback_data="main_menu")
    )
    return builder.as_markup()


def get_backdrop_filters(backdrops: List[str], page: int = 1, per_page: int = 8) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    start = (page - 1) * per_page
    end = start + per_page
    page_backdrops = backdrops[start:end]
    
    for i in range(0, len(page_backdrops), 2):
        row_items = page_backdrops[i:i+2]
        buttons = [
            InlineKeyboardButton(
                text=b[:20],
                callback_data=f"backdrop:{b[:30]}"
            ) for b in row_items
        ]
        builder.row(*buttons)
    
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="◀️", callback_data=f"backdrop_page:{page-1}"))
    if end < len(backdrops):
        nav_buttons.append(InlineKeyboardButton(text="▶️", callback_data=f"backdrop_page:{page+1}"))
    
    if nav_buttons:
        builder.row(*nav_buttons)
    
    builder.row(InlineKeyboardButton(text="Назад", callback_data="filters_menu"))
    return builder.as_markup()


def get_symbol_filters(symbols: List[str], page: int = 1, per_page: int = 8) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    start = (page - 1) * per_page
    end = start + per_page
    page_symbols = symbols[start:end]
    
    for i in range(0, len(page_symbols), 2):
        row_items = page_symbols[i:i+2]
        buttons = [
            InlineKeyboardButton(
                text=s[:20],
                callback_data=f"symbol:{s[:30]}"
            ) for s in row_items
        ]
        builder.row(*buttons)
    
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="◀️", callback_data=f"symbol_page:{page-1}"))
    if end < len(symbols):
        nav_buttons.append(InlineKeyboardButton(text="▶️", callback_data=f"symbol_page:{page+1}"))
    
    if nav_buttons:
        builder.row(*nav_buttons)
    
    builder.row(InlineKeyboardButton(text="Назад", callback_data="filters_menu"))
    return builder.as_markup()


def get_pagination_keyboard(
    current_page: int,
    total_pages: int,
    callback_prefix: str,
    extra_data: str = ""
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    nav_buttons = []
    
    if current_page > 1:
        nav_buttons.append(
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data=f"{callback_prefix}:{current_page - 1}:{extra_data}"
            )
        )
    
    nav_buttons.append(
        InlineKeyboardButton(
            text=f"{current_page}/{total_pages}",
            callback_data="page_info"
        )
    )
    
    if current_page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(
                text="Вперед ▶️",
                callback_data=f"{callback_prefix}:{current_page + 1}:{extra_data}"
            )
        )
    
    builder.row(*nav_buttons)
    builder.row(InlineKeyboardButton(text="В меню", callback_data="main_menu"))
    
    return builder.as_markup()


def get_gift_actions(gift_id: int, is_blocked: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    if is_blocked:
        builder.row(
            InlineKeyboardButton(text="Разблокировать", callback_data=f"unblock:{gift_id}")
        )
    else:
        builder.row(
            InlineKeyboardButton(text="Заблокировать", callback_data=f"block:{gift_id}")
        )
    
    builder.row(InlineKeyboardButton(text="Назад", callback_data="main_menu"))
    return builder.as_markup()


def get_blocks_keyboard(blocks: List, page: int = 1, per_page: int = 5) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    start = (page - 1) * per_page
    end = start + per_page
    page_blocks = blocks[start:end]
    
    for block in page_blocks:
        gift_name = block.gift_name or f"ID: {block.nft_gift_id}"
        builder.row(
            InlineKeyboardButton(
                text=f"❌ {gift_name[:25]}",
                callback_data=f"unblock:{block.nft_gift_id}"
            )
        )
    
    nav_buttons = []
    total_pages = (len(blocks) + per_page - 1) // per_page
    
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="◀️", callback_data=f"blocks_page:{page-1}"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(text="▶️", callback_data=f"blocks_page:{page+1}"))
    
    if nav_buttons:
        builder.row(*nav_buttons)
    
    builder.row(InlineKeyboardButton(text="В меню", callback_data="main_menu"))
    return builder.as_markup()


def get_random_count_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    counts = [10, 20, 30, 50, 100]
    
    builder.row(*[
        InlineKeyboardButton(text=str(c), callback_data=f"random:{c}")
        for c in counts[:3]
    ])
    builder.row(*[
        InlineKeyboardButton(text=str(c), callback_data=f"random:{c}")
        for c in counts[3:]
    ])
    builder.row(InlineKeyboardButton(text="Назад", callback_data="main_menu"))
    return builder.as_markup()


def get_confirm_keyboard(action: str, data: str = "") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Да", callback_data=f"confirm_{action}:{data}"),
        InlineKeyboardButton(text="❌ Нет", callback_data="main_menu")
    )
    return builder.as_markup()


def get_search_count_keyboard(slug: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="10", callback_data=f"search_count:{slug}:10"),
        InlineKeyboardButton(text="25", callback_data=f"search_count:{slug}:25"),
        InlineKeyboardButton(text="50", callback_data=f"search_count:{slug}:50")
    )
    builder.row(
        InlineKeyboardButton(text="100", callback_data=f"search_count:{slug}:100"),
        InlineKeyboardButton(text="🔥 Максимум", callback_data=f"search_count:{slug}:500")
    )
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="find"))
    return builder.as_markup()


def get_results_pagination_keyboard(
    slug: str,
    current_page: int,
    total_pages: int,
    total_results: int
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    nav_buttons = []
    
    if current_page > 1:
        nav_buttons.append(
            InlineKeyboardButton(text="◀️", callback_data=f"results_page:{slug}:{current_page - 1}")
        )
    
    nav_buttons.append(
        InlineKeyboardButton(text=f"📄 {current_page}/{total_pages}", callback_data="noop")
    )
    
    if current_page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(text="▶️", callback_data=f"results_page:{slug}:{current_page + 1}")
        )
    
    builder.row(*nav_buttons)

    if slug == "random":
        new_search_callback = "random_search"
    elif slug == "filtered":
        new_search_callback = "adv_apply"
    elif slug.startswith("filter_"):
        new_search_callback = "filter_search"
    else:
        new_search_callback = f"select_count:{slug}"

    builder.row(
        InlineKeyboardButton(text="📥 CSV", callback_data="export_csv"),
        InlineKeyboardButton(text="🔄 Новый", callback_data=new_search_callback),
        InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")
    )
    
    return builder.as_markup()


# ---------------------------------------------------------------------------
# New: quick search / advanced filters / blacklist / marketplace keyboards
# ---------------------------------------------------------------------------

def get_quick_search_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🟢 Лёгкий (до 10 TON)", callback_data="quick_mode:light")
    )
    builder.row(
        InlineKeyboardButton(text="🟡 Средний (10-50 TON)", callback_data="quick_mode:medium")
    )
    builder.row(
        InlineKeyboardButton(text="🔴 Жирный (50+ TON)", callback_data="quick_mode:heavy")
    )
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu"))
    return builder.as_markup()


def get_adv_filters_menu(state: dict) -> InlineKeyboardMarkup:
    """state: {"quick_mode": str|None, "backdrop": str|None, "rare_only": bool}"""
    builder = InlineKeyboardBuilder()

    mode = state.get("quick_mode")
    mode_label = {"light": "🟢 Лёгкий", "medium": "🟡 Средний", "heavy": "🔴 Жирный"}.get(mode, "Не выбран")
    builder.row(
        InlineKeyboardButton(text=f"💰 Ценовой режим: {mode_label}", callback_data="adv_pick_mode")
    )

    backdrop = state.get("backdrop") or "Любой"
    builder.row(
        InlineKeyboardButton(text=f"🖼 Фон: {backdrop}", callback_data="adv_pick_backdrop")
    )

    rare_flag = "✅ Вкл" if state.get("rare_only") else "❌ Выкл"
    builder.row(
        InlineKeyboardButton(text=f"💎 Только редкие модели (<0.8%): {rare_flag}", callback_data="adv_toggle_rare")
    )

    builder.row(
        InlineKeyboardButton(text="🚀 Применить фильтры", callback_data="adv_apply")
    )
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu"))
    return builder.as_markup()


def get_blacklist_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="➕ Добавить подарок", callback_data="bl_add_gift"),
        InlineKeyboardButton(text="➕ Добавить продавца", callback_data="bl_add_seller")
    )
    builder.row(
        InlineKeyboardButton(text="📋 Список подарков", callback_data="bl_list_gifts"),
        InlineKeyboardButton(text="📋 Список продавцов", callback_data="bl_list_sellers")
    )
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu"))
    return builder.as_markup()


def get_marketplace_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🟢 Дешёвые", callback_data="market_tier:cheap"),
        InlineKeyboardButton(text="🟡 Средние", callback_data="market_tier:medium"),
        InlineKeyboardButton(text="🔴 Жирные", callback_data="market_tier:expensive")
    )
    builder.row(
        InlineKeyboardButton(text="🔔 Подписаться на все", callback_data="market_sub_all")
    )
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu"))
    return builder.as_markup()


def get_claim_keyboard(listing_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🤝 Забрать подарок", callback_data=f"market_claim:{listing_id}")
    )
    return builder.as_markup()
