
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

router = Router()

user_sessions: dict[int, dict] = {}

SAMPLE_ACCOUNTS = [
    {
        "name": "luna_star",
        "gift": "Moon Gem",
        "background": "Galaxy",
        "rare_score": 0.35,
        "gender": "girl",
        "premium": True,
        "nft": 3,
        "rating": 5,
        "phone": "+7 912 123 45 67",
        "chat": "NFT Club",
        "gift_category": "gift",
    },
    {
        "name": "rose_queen",
        "gift": "Heart Token",
        "background": "Rose",
        "rare_score": 0.75,
        "gender": "girl",
        "premium": False,
        "nft": 1,
        "rating": 1,
        "phone": "+380 50 765 43 21",
        "chat": "Girls Hangout",
        "gift_category": "gift",
    },
    {
        "name": "starboy",
        "gift": "Star Chest",
        "background": "Space",
        "rare_score": 0.12,
        "gender": "boy",
        "premium": False,
        "nft": 10,
        "rating": 4,
        "phone": "+1 555 123 9876",
        "chat": "Market Talk",
        "gift_category": "gift",
    },
    {
        "name": "pirate_angel",
        "gift": "Lucky Box",
        "background": "Pirate",
        "rare_score": 0.55,
        "gender": "girl",
        "premium": True,
        "nft": 2,
        "rating": 3,
        "phone": "+90 532 111 22 33",
        "chat": "Gift Chat",
        "gift_category": "gift",
    },
    {
        "name": "nova_nft",
        "gift": "Rose Bundle",
        "background": "Neon",
        "rare_score": 0.9,
        "gender": "boy",
        "premium": True,
        "nft": 15,
        "rating": 7,
        "phone": "+7 903 888 44 55",
        "chat": "NFT Club",
        "gift_category": "gift",
    },
    {
        "name": "sky_glow",
        "gift": "Crystal Heart",
        "background": "Cloud",
        "rare_score": 0.28,
        "gender": "girl",
        "premium": False,
        "nft": 5,
        "rating": 2,
        "phone": "+1 415 987 65 43",
        "chat": "Girls Hangout",
        "gift_category": "gift",
    },
]

MARKET_ITEMS = [
    {
        "id": 1,
        "title": "Лунная подвеска",
        "gift": "Moon Gem",
        "price": "399",
        "category": "cheap",
        "taken_by": None,
        "owner": "@OwnerA",
    },
    {
        "id": 2,
        "title": "Сердечный амулет",
        "gift": "Heart Token",
        "price": "1799",
        "category": "medium",
        "taken_by": None,
        "owner": "@OwnerB",
    },
    {
        "id": 3,
        "title": "Звездный сундук",
        "gift": "Star Chest",
        "price": "4999",
        "category": "heavy",
        "taken_by": None,
        "owner": "@OwnerC",
    },
]

BACKGROUND_OPTIONS = ["Galaxy", "Rose", "Space", "Pirate", "Neon", "Cloud"]
CHAT_OPTIONS = ["NFT Club", "Girls Hangout", "Gift Chat", "Market Talk"]
PHONE_COUNTRIES = {
    "ru": "+7",
    "ua": "+380",
    "us": "+1",
    "tr": "+90",
}
NFT_OPTIONS = [
    ("1", "1"),
    ("1-2", "1-2"),
    ("1-3", "1-3"),
    ("1-4", "1-4"),
    ("1-5", "1-5"),
    ("5-10", "5-10"),
    ("10-15", "10-15"),
    ("15-20", "15-20"),
    ("20+", "20+"),
]
RATING_OPTIONS = [
    ("1", "1"),
    ("2", "2"),
    ("3", "3"),
    ("4", "4"),
    ("5", "5"),
    ("1-2", "1-2"),
    ("1-3", "1-3"),
    ("1-4", "1-4"),
    ("1-5", "1-5"),
    ("5-7", "5-7"),
    ("7-9", "7-9"),
    ("10+", "10+"),
]
GIFT_OPTIONS = ["Moon Gem", "Heart Token", "Rose Bundle", "Lucky Box", "Star Chest"]


def get_session(user_id: int) -> dict:
    if user_id not in user_sessions:
        user_sessions[user_id] = {
            "background": None,
            "rare": False,
            "account_type": None,
            "gift_filter": None,
            "premium": None,
            "chat": None,
            "nft_count": None,
            "phone_countries": set(),
            "rating": None,
            "custom_text": None,
            "blacklist_users": [],
            "blacklist_gifts": [],
            "awaiting": None,
            "market_choice": None,
        }
    return user_sessions[user_id]


def format_gift_name(name: str) -> str:
    map_emoji = {
        "moon": "🌙",
        "heart": "❤️",
        "rose": "🌹",
        "star": "⭐",
        "lucky": "🍀",
        "crystal": "💎",
        "box": "📦",
    }
    lower = name.lower()
    for key, emoji in map_emoji.items():
        if key in lower:
            return f"{emoji} {name}"
    return name


def build_filter_summary(session: dict) -> str:
    parts = []
    if session["background"]:
        parts.append(f"🎨 фон: {session['background']}")
    if session["rare"]:
        parts.append("💎 редкие модели <0.8%")
    if session["account_type"]:
        parts.append(f"👩 аккаунты: {session['account_type']}")
    if session["gift_filter"]:
        parts.append(f"🎁 подарок: {session['gift_filter']}")
    if session["premium"]:
        parts.append("💼 только премиум" if session["premium"] == "premium" else "🚫 без премиума")
    if session["chat"]:
        parts.append(f"💬 чат: {session['chat']}")
    if session["nft_count"]:
        parts.append(f"🧾 NFT: {session['nft_count']}")
    if session["phone_countries"]:
        parts.append(f"📱 номера: {', '.join(sorted(session['phone_countries']))}")
    if session["rating"]:
        parts.append(f"⭐ рейтинг: {session['rating']}")
    if session["custom_text"]:
        parts.append("✉️ текст ЛС задан")
    if session["blacklist_users"]:
        parts.append(f"🚫 юзеров: {len(session['blacklist_users'])}")
    if session["blacklist_gifts"]:
        parts.append(f"🚫 подарков: {len(session['blacklist_gifts'])}")
    return "\n".join(parts) if parts else "Пока нет выбранных фильтров."


def match_nft_count(key: str, count: int) -> bool:
    if key == "1":
        return count == 1
    if key == "1-2":
        return 1 <= count <= 2
    if key == "1-3":
        return 1 <= count <= 3
    if key == "1-4":
        return 1 <= count <= 4
    if key == "1-5":
        return 1 <= count <= 5
    if key == "5-10":
        return 5 <= count <= 10
    if key == "10-15":
        return 10 <= count <= 15
    if key == "15-20":
        return 15 <= count <= 20
    if key == "20+":
        return count >= 20
    return True


def match_rating(key: str, rating: int) -> bool:
    if key == "1":
        return rating == 1
    if key == "2":
        return rating == 2
    if key == "3":
        return rating == 3
    if key == "4":
        return rating == 4
    if key == "5":
        return rating == 5
    if key == "1-2":
        return 1 <= rating <= 2
    if key == "1-3":
        return 1 <= rating <= 3
    if key == "1-4":
        return 1 <= rating <= 4
    if key == "1-5":
        return 1 <= rating <= 5
    if key == "5-7":
        return 5 <= rating <= 7
    if key == "7-9":
        return 7 <= rating <= 9
    if key == "10+":
        return rating >= 10
    return True


def filter_accounts(session: dict) -> list[dict]:
    results = []
    for item in SAMPLE_ACCOUNTS:
        if session["background"] and item["background"] != session["background"]:
            continue
        if session["rare"] and item["rare_score"] >= 0.8:
            continue
        if session["account_type"] == "girl" and item["gender"] != "girl":
            continue
        if session["gift_filter"] and item["gift"] != session["gift_filter"]:
            continue
        if session["premium"] == "premium" and not item["premium"]:
            continue
        if session["premium"] == "no_premium" and item["premium"]:
            continue
        if session["chat"] and item["chat"] != session["chat"]:
            continue
        if session["nft_count"] and not match_nft_count(session["nft_count"], item["nft"]):
            continue
        if session["rating"] and not match_rating(session["rating"], item["rating"]):
            continue
        if session["phone_countries"]:
            if not any(item["phone"].startswith(prefix) for prefix in PHONE_COUNTRIES.values() if prefix in [PHONE_COUNTRIES[c] for c in session["phone_countries"]]):
                continue
        if item["name"] in session["blacklist_users"]:
            continue
        if item["gift"] in session["blacklist_gifts"]:
            continue
        results.append(item)
    return results


def format_search_result_text(results: list[dict], session: dict, mode: str = None) -> str:
    if not results:
        return "🔍 Ничего не найдено по выбранным фильтрам."

    lines = []
    for item in results[:10]:
        lines.append(
            f"👤 @{item['name']}\n"
            f"🎁 {format_gift_name(item['gift'])}\n"
            f"🌐 фон: {item['background']} | ⭐ {item['rating']} | NFT: {item['nft']} | "
            f"{'💼 премиум' if item['premium'] else '🚫 без премиума'}\n"
            f"📱 {item['phone']} | 💬 {item['chat']}"
        )
    header = "🔎 Результаты поиска"
    if mode:
        header += f" ({mode})"
    text = header + "\n\n" + "\n\n".join(lines)
    if session["custom_text"]:
        text += f"\n\n✉️ Текст ЛС:\n{session['custom_text']}"
    return text


def get_main_menu() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="Фильтры", callback_data="filters_menu")],
        [InlineKeyboardButton(text="Быстрый поиск", callback_data="fast_search")],
        [InlineKeyboardButton(text="Черный список", callback_data="blacklist")],
        [InlineKeyboardButton(text="Телеграм маркет", callback_data="market")],
        [InlineKeyboardButton(text="Текст в ЛС", callback_data="custom_text")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_filters_menu(session: dict) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text=f"Фон {('✅' if session['background'] else '')}",
                callback_data="filter_background"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"Редкие модели {('✅' if session['rare'] else '')}",
                callback_data="filter_rare"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"Поиск аккаунтов {('✅' if session['account_type'] or session['gift_filter'] else '')}",
                callback_data="filter_accounts"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"Премиум / без премиума {('✅' if session['premium'] else '')}",
                callback_data="filter_premium"
            )
        ],
        [
            InlineKeyboardButton(
                text="Несколько фильтров",
                callback_data="filter_multi"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"По чатам {('✅' if session['chat'] else '')}",
                callback_data="filter_chat"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"Количество NFT {('✅' if session['nft_count'] else '')}",
                callback_data="filter_nft_count"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"Поиск по телефону {('✅' if session['phone_countries'] else '')}",
                callback_data="filter_phone"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"По рейтингу {('✅' if session['rating'] else '')}",
                callback_data="filter_rating"
            )
        ],
        [
            InlineKeyboardButton(text="Запустить поиск", callback_data="filter_run")
        ],
        [
            InlineKeyboardButton(text="Сбросить фильтры", callback_data="filter_reset"),
            InlineKeyboardButton(text="Главное меню", callback_data="main_menu"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_background_menu() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=bg, callback_data=f"filter_background_{bg}") for bg in BACKGROUND_OPTIONS[:2]],
        [InlineKeyboardButton(text=bg, callback_data=f"filter_background_{bg}") for bg in BACKGROUND_OPTIONS[2:4]],
        [InlineKeyboardButton(text=bg, callback_data=f"filter_background_{bg}") for bg in BACKGROUND_OPTIONS[4:]],
        [InlineKeyboardButton(text="Назад", callback_data="filters_menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_account_menu(session: dict) -> InlineKeyboardMarkup:
    gift_buttons = [
        InlineKeyboardButton(
            text=f"{gift} {('✅' if session['gift_filter'] == gift else '')}",
            callback_data=f"filter_gift_{gift.replace(' ', '_')}"
        )
        for gift in GIFT_OPTIONS
    ]
    buttons = [
        [InlineKeyboardButton(
            text=f"Девочки {('✅' if session['account_type'] == 'girl' else '')}",
            callback_data="filter_account_girl"
        )],
        *[[button] for button in gift_buttons],
        [InlineKeyboardButton(text="Очистить выбор", callback_data="filter_account_clear")],
        [InlineKeyboardButton(text="Назад", callback_data="filters_menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_premium_menu(session: dict) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text=f"Премиум {('✅' if session['premium'] == 'premium' else '')}",
                callback_data="filter_premium_premium"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"Без премиума {('✅' if session['premium'] == 'no_premium' else '')}",
                callback_data="filter_premium_no"
            )
        ],
        [InlineKeyboardButton(text="Очистить", callback_data="filter_premium_clear")],
        [InlineKeyboardButton(text="Назад", callback_data="filters_menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_chat_menu(session: dict) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text=f"{chat} {('✅' if session['chat'] == chat else '')}",
                callback_data=f"filter_chat_{chat.replace(' ', '_')}"
            )
        ]
        for chat in CHAT_OPTIONS
    ]
    buttons.append([InlineKeyboardButton(text="Очистить", callback_data="filter_chat_clear")])
    buttons.append([InlineKeyboardButton(text="Назад", callback_data="filters_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_nft_menu(session: dict) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text=f"{label} {('✅' if session['nft_count'] == key else '')}",
                callback_data=f"filter_nft_{key}"
            )
        ]
        for key, label in NFT_OPTIONS
    ]
    buttons.append([InlineKeyboardButton(text="Очистить", callback_data="filter_nft_clear")])
    buttons.append([InlineKeyboardButton(text="Назад", callback_data="filters_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_phone_menu(session: dict) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text=f"{code.upper()} {('✅' if code in session['phone_countries'] else '')}",
                callback_data=f"filter_phone_{code}"
            )
        ]
        for code in PHONE_COUNTRIES
    ]
    buttons.append([InlineKeyboardButton(text="Очистить", callback_data="filter_phone_clear")])
    buttons.append([InlineKeyboardButton(text="Назад", callback_data="filters_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_rating_menu(session: dict) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text=f"{label} {('✅' if session['rating'] == key else '')}",
                callback_data=f"filter_rating_{key.replace('+', 'plus').replace('-', '_')}"
            )
        ]
        for key, label in RATING_OPTIONS
    ]
    buttons.append([InlineKeyboardButton(text="Очистить", callback_data="filter_rating_clear")])
    buttons.append([InlineKeyboardButton(text="Назад", callback_data="filters_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_multi_menu(session: dict) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text=f"Девочки {('✅' if session['account_type'] == 'girl' else '')}",
                callback_data="multi_toggle_girl"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"Без премиума {('✅' if session['premium'] == 'no_premium' else '')}",
                callback_data="multi_toggle_no_premium"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"Рейтинг 1-3 {('✅' if session['rating'] == '1-3' else '')}",
                callback_data="multi_toggle_rating_1_3"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"NFT 1-3 {('✅' if session['nft_count'] == '1-3' else '')}",
                callback_data="multi_toggle_nft_1_3"
            )
        ],
        [InlineKeyboardButton(text="Запустить поиск", callback_data="filter_run")],
        [InlineKeyboardButton(text="Назад", callback_data="filters_menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_blacklist_menu(session: dict) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="Добавить пользователя", callback_data="blacklist_add_user")],
        [InlineKeyboardButton(text="Добавить подарок", callback_data="blacklist_add_gift")],
        [InlineKeyboardButton(text="Назад", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_market_menu() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="Дешевые", callback_data="market_category_cheap")],
        [InlineKeyboardButton(text="Средние", callback_data="market_category_medium")],
        [InlineKeyboardButton(text="Жирные", callback_data="market_category_heavy")],
        [InlineKeyboardButton(text="Назад", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_market_items_menu(category: str) -> InlineKeyboardMarkup:
    buttons = []
    for item in [x for x in MARKET_ITEMS if x["category"] == category]:
        label = f"{item['title']} — {item['price']} ₽"
        if item["taken_by"]:
            label += f" (занят {item['taken_by']})"
        buttons.append(
            [InlineKeyboardButton(text=label, callback_data=f"market_take_{item['id']}")]
        )
    buttons.append([InlineKeyboardButton(text="Назад", callback_data="market")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_after_search_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Фильтры", callback_data="filters_menu")],
            [InlineKeyboardButton(text="Главное меню", callback_data="main_menu")],
        ]
    )


async def update_filters_message(callback: CallbackQuery, session: dict, text: str, reply_markup: InlineKeyboardMarkup):
    if not callback.message:
        await callback.answer()
        return
    await callback.message.edit_text(text, reply_markup=reply_markup, parse_mode="HTML")
    await callback.answer()


@router.message(Command(commands=["start"]))
async def cmd_start(message: Message):
    text = (
        "⚡️ <b>Привет! Это лучший бесплатный парсер NFT-подарков.</b>\n\n"
        "👇 <b>Выбери действие:</b>"
    )
    await message.answer(text, reply_markup=get_main_menu(), parse_mode="HTML")


@router.callback_query(F.data == "main_menu")
async def callback_main_menu(callback: CallbackQuery):
    await update_filters_message(
        callback,
        get_session(callback.from_user.id),
        "⚡️ <b>Главное меню</b>\n\n👇 <b>Выбери действие:</b>",
        get_main_menu(),
    )


@router.callback_query(F.data == "filters_menu")
async def callback_filters(callback: CallbackQuery):
    session = get_session(callback.from_user.id)
    text = (
        "⚙️ <b>Поиск подарков по фильтрам.</b>\n\n"
        f"<i>Выбранные фильтры:</i>\n{build_filter_summary(session)}"
    )
    await update_filters_message(callback, session, text, get_filters_menu(session))


@router.callback_query(F.data == "fast_search")
async def callback_fast_search(callback: CallbackQuery):
    await update_filters_message(
        callback,
        get_session(callback.from_user.id),
        "🚀 <b>Быстрый поиск</b>\nВыберите режим",
        InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Легкий", callback_data="quick_easy")],
                [InlineKeyboardButton(text="Средний", callback_data="quick_medium")],
                [InlineKeyboardButton(text="Жирный", callback_data="quick_heavy")],
                [InlineKeyboardButton(text="Главное меню", callback_data="main_menu")],
            ]
        ),
    )


@router.callback_query(F.data == "blacklist")
async def callback_blacklist(callback: CallbackQuery):
    session = get_session(callback.from_user.id)
    text = (
        "🛑 <b>Черный список</b>\n\n"
        f"Пользователи: {', '.join(session['blacklist_users']) or 'нет'}\n"
        f"Подарки: {', '.join(session['blacklist_gifts']) or 'нет'}"
    )
    await update_filters_message(callback, session, text, get_blacklist_menu(session))


@router.callback_query(F.data == "market")
async def callback_market(callback: CallbackQuery):
    await update_filters_message(
        callback,
        get_session(callback.from_user.id),
        "🛒 <b>Телеграм маркет</b>\nВыберите категорию",
        get_market_menu(),
    )


@router.callback_query(F.data == "custom_text")
async def callback_custom_text(callback: CallbackQuery):
    session = get_session(callback.from_user.id)
    session["awaiting"] = "custom_text"
    text = (
        "✉️ <b>Свой текст в ЛС</b>\n\n"
        "Отправьте сообщение, которое будет прикрепляться к результатам поиска."
    )
    await update_filters_message(callback, session, text, InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Главное меню", callback_data="main_menu")]]
    ))


@router.callback_query(F.data == "filter_background")
async def callback_filter_background(callback: CallbackQuery):
    await update_filters_message(
        callback,
        get_session(callback.from_user.id),
        "🎨 <b>Выберите фон</b>",
        get_background_menu(),
    )


@router.callback_query(F.data.startswith("filter_background_"))
async def callback_filter_background_choice(callback: CallbackQuery):
    session = get_session(callback.from_user.id)
    background = callback.data.split("_", 2)[2]
    session["background"] = background
    await callback_filters(callback)


@router.callback_query(F.data == "filter_rare")
async def callback_filter_rare(callback: CallbackQuery):
    session = get_session(callback.from_user.id)
    session["rare"] = not session["rare"]
    await callback_filters(callback)


@router.callback_query(F.data == "filter_accounts")
async def callback_filter_accounts(callback: CallbackQuery):
    session = get_session(callback.from_user.id)
    await update_filters_message(
        callback,
        session,
        "👥 <b>Поиск аккаунтов</b>\nВыберите параметры",
        get_account_menu(session),
    )


@router.callback_query(F.data == "filter_account_girl")
async def callback_filter_account_girl(callback: CallbackQuery):
    session = get_session(callback.from_user.id)
    session["account_type"] = "girl" if session["account_type"] != "girl" else None
    await callback_filter_accounts(callback)


@router.callback_query(F.data.startswith("filter_gift_"))
async def callback_filter_gift_choice(callback: CallbackQuery):
    session = get_session(callback.from_user.id)
    gift = callback.data.split("_", 2)[2].replace("_", " ")
    session["gift_filter"] = gift
    await callback_filter_accounts(callback)


@router.callback_query(F.data == "filter_account_clear")
async def callback_filter_account_clear(callback: CallbackQuery):
    session = get_session(callback.from_user.id)
    session["account_type"] = None
    session["gift_filter"] = None
    await callback_filter_accounts(callback)


@router.callback_query(F.data == "filter_premium")
async def callback_filter_premium(callback: CallbackQuery):
    session = get_session(callback.from_user.id)
    await update_filters_message(
        callback,
        session,
        "💼 <b>Премиум / без премиума</b>\nВыберите режим",
        get_premium_menu(session),
    )


@router.callback_query(F.data == "filter_premium_premium")
async def callback_filter_premium_premium(callback: CallbackQuery):
    session = get_session(callback.from_user.id)
    session["premium"] = "premium"
    await callback_filter_premium(callback)


@router.callback_query(F.data == "filter_premium_no")
async def callback_filter_premium_no(callback: CallbackQuery):
    session = get_session(callback.from_user.id)
    session["premium"] = "no_premium"
    await callback_filter_premium(callback)


@router.callback_query(F.data == "filter_premium_clear")
async def callback_filter_premium_clear(callback: CallbackQuery):
    session = get_session(callback.from_user.id)
    session["premium"] = None
    await callback_filter_premium(callback)


@router.callback_query(F.data == "filter_chat")
async def callback_filter_chat(callback: CallbackQuery):
    session = get_session(callback.from_user.id)
    await update_filters_message(
        callback,
        session,
        "💬 <b>Поиск по чатам</b>\nВыберите чат",
        get_chat_menu(session),
    )


@router.callback_query(F.data.startswith("filter_chat_"))
async def callback_filter_chat_choice(callback: CallbackQuery):
    session = get_session(callback.from_user.id)
    chat = callback.data.split("_", 2)[2].replace("_", " ")
    session["chat"] = chat
    await callback_filter_chat(callback)


@router.callback_query(F.data == "filter_chat_clear")
async def callback_filter_chat_clear(callback: CallbackQuery):
    session = get_session(callback.from_user.id)
    session["chat"] = None
    await callback_filter_chat(callback)


@router.callback_query(F.data == "filter_nft_count")
async def callback_filter_nft(callback: CallbackQuery):
    session = get_session(callback.from_user.id)
    await update_filters_message(
        callback,
        session,
        "🧾 <b>Количество NFT</b>\nВыберите диапазон",
        get_nft_menu(session),
    )


@router.callback_query(F.data.startswith("filter_nft_"))
async def callback_filter_nft_choice(callback: CallbackQuery):
    session = get_session(callback.from_user.id)
    value = callback.data.split("_", 2)[2]
    session["nft_count"] = value
    await callback_filter_nft(callback)


@router.callback_query(F.data == "filter_nft_clear")
async def callback_filter_nft_clear(callback: CallbackQuery):
    session = get_session(callback.from_user.id)
    session["nft_count"] = None
    await callback_filter_nft(callback)


@router.callback_query(F.data == "filter_phone")
async def callback_filter_phone(callback: CallbackQuery):
    session = get_session(callback.from_user.id)
    await update_filters_message(
        callback,
        session,
        "📱 <b>Поиск по номеру телефона</b>\nВыберите страны",
        get_phone_menu(session),
    )


@router.callback_query(F.data.startswith("filter_phone_"))
async def callback_filter_phone_choice(callback: CallbackQuery):
    session = get_session(callback.from_user.id)
    country = callback.data.split("_", 2)[2]
    if country in PHONE_COUNTRIES:
        if country in session["phone_countries"]:
            session["phone_countries"].remove(country)
        else:
            session["phone_countries"].add(country)
    await callback_filter_phone(callback)


@router.callback_query(F.data == "filter_phone_clear")
async def callback_filter_phone_clear(callback: CallbackQuery):
    session = get_session(callback.from_user.id)
    session["phone_countries"].clear()
    await callback_filter_phone(callback)


@router.callback_query(F.data == "filter_rating")
async def callback_filter_rating(callback: CallbackQuery):
    session = get_session(callback.from_user.id)
    await update_filters_message(
        callback,
        session,
        "⭐ <b>Поиск по рейтингу</b>\nВыберите диапазон",
        get_rating_menu(session),
    )


@router.callback_query(F.data.startswith("filter_rating_"))
async def callback_filter_rating_choice(callback: CallbackQuery):
    session = get_session(callback.from_user.id)
    key = callback.data.split("_", 2)[2].replace("plus", "+").replace("_", "-")
    session["rating"] = key
    await callback_filter_rating(callback)


@router.callback_query(F.data == "filter_rating_clear")
async def callback_filter_rating_clear(callback: CallbackQuery):
    session = get_session(callback.from_user.id)
    session["rating"] = None
    await callback_filter_rating(callback)


@router.callback_query(F.data == "filter_multi")
async def callback_filter_multi(callback: CallbackQuery):
    session = get_session(callback.from_user.id)
    await update_filters_message(
        callback,
        session,
        "🧩 <b>Несколько фильтров</b>\nВыберите сразу несколько условий",
        get_multi_menu(session),
    )


@router.callback_query(F.data.startswith("multi_toggle_"))
async def callback_multi_toggle(callback: CallbackQuery):
    session = get_session(callback.from_user.id)
    key = callback.data.split("_", 2)[2]
    if key == "girl":
        session["account_type"] = "girl" if session["account_type"] != "girl" else None
    elif key == "no_premium":
        session["premium"] = "no_premium" if session["premium"] != "no_premium" else None
    elif key == "rating_1_3":
        session["rating"] = "1-3" if session["rating"] != "1-3" else None
    elif key == "nft_1_3":
        session["nft_count"] = "1-3" if session["nft_count"] != "1-3" else None
    await callback_filter_multi(callback)


@router.callback_query(F.data == "filter_run")
async def callback_filter_run(callback: CallbackQuery):
    session = get_session(callback.from_user.id)
    results = filter_accounts(session)
    text = format_search_result_text(results, session)
    await update_filters_message(callback, session, text, get_after_search_menu())


@router.callback_query(F.data == "filter_reset")
async def callback_filter_reset(callback: CallbackQuery):
    user_sessions[callback.from_user.id] = {
        "background": None,
        "rare": False,
        "account_type": None,
        "gift_filter": None,
        "premium": None,
        "chat": None,
        "nft_count": None,
        "phone_countries": set(),
        "rating": None,
        "custom_text": None,
        "blacklist_users": [],
        "blacklist_gifts": [],
        "awaiting": None,
        "market_choice": None,
    }
    await callback_filters(callback)


@router.callback_query(F.data == "quick_easy")
async def callback_quick_easy(callback: CallbackQuery):
    session = get_session(callback.from_user.id)
    results = filter_accounts(session)[:3]
    text = format_search_result_text(results, session, mode="легкий")
    await update_filters_message(callback, session, text, get_after_search_menu())


@router.callback_query(F.data == "quick_medium")
async def callback_quick_medium(callback: CallbackQuery):
    session = get_session(callback.from_user.id)
    results = filter_accounts(session)[:5]
    text = format_search_result_text(results, session, mode="средний")
    await update_filters_message(callback, session, text, get_after_search_menu())


@router.callback_query(F.data == "quick_heavy")
async def callback_quick_heavy(callback: CallbackQuery):
    session = get_session(callback.from_user.id)
    results = filter_accounts(session)[:8]
    text = format_search_result_text(results, session, mode="жирный")
    await update_filters_message(callback, session, text, get_after_search_menu())


@router.callback_query(F.data == "blacklist_add_user")
async def callback_blacklist_add_user(callback: CallbackQuery):
    session = get_session(callback.from_user.id)
    session["awaiting"] = "blacklist_user"
    text = "👤 Отправьте username пользователя, которого хотите заблокировать в черном списке."
    await update_filters_message(callback, session, text, InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data="blacklist")]]
    ))


@router.callback_query(F.data == "blacklist_add_gift")
async def callback_blacklist_add_gift(callback: CallbackQuery):
    session = get_session(callback.from_user.id)
    session["awaiting"] = "blacklist_gift"
    text = "🎁 Отправьте название подарка, который хотите заблокировать."
    await update_filters_message(callback, session, text, InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data="blacklist")]]
    ))


@router.callback_query(F.data.startswith("market_category_"))
async def callback_market_category(callback: CallbackQuery):
    category = callback.data.split("_", 2)[2]
    category_text = {"cheap": "Дешевые", "medium": "Средние", "heavy": "Жирные"}.get(category, category)
    text = f"🛒 <b>Маркет — {category_text}</b>\nВыберите подарок"
    await update_filters_message(callback, get_session(callback.from_user.id), text, get_market_items_menu(category))


@router.callback_query(F.data.startswith("market_take_"))
async def callback_market_take(callback: CallbackQuery):
    item_id = int(callback.data.split("_", 2)[2])
    item = next((x for x in MARKET_ITEMS if x["id"] == item_id), None)
    if not item:
        await callback.answer("Ошибка: товар не найден", show_alert=True)
        return
    if item["taken_by"]:
        await callback.answer(f"Этот подарок уже занял {item['taken_by']}", show_alert=True)
        return
    username = callback.from_user.username or callback.from_user.full_name or "пользователь"
    item["taken_by"] = f"@{username}" if not username.startswith("@") else username
    await callback.answer(f"Подарок забрал {item['taken_by']}", show_alert=True)
    text = (
        f"✅ <b>{item['title']}</b>\n"
        f"Подарок занял {item['taken_by']}\n"
        f"Владелец: {item['owner']}\n\n"
        "Теперь напишите владельцу, чтобы договориться о передаче."
    )
    await update_filters_message(callback, get_session(callback.from_user.id), text, get_market_items_menu(item["category"]))


@router.message()
async def callback_text_handler(message: Message):
    session = get_session(message.from_user.id)
    if not session["awaiting"]:
        return

    if session["awaiting"] == "custom_text":
        session["custom_text"] = message.text.strip()
        session["awaiting"] = None
        await message.answer("✅ Текст для ЛС сохранён.", reply_markup=get_main_menu())
        return

    if session["awaiting"] == "blacklist_user":
        value = message.text.strip().lstrip("@")
        if value and value not in session["blacklist_users"]:
            session["blacklist_users"].append(value)
        session["awaiting"] = None
        await message.answer(f"🚫 Пользователь @{value} добавлен в чёрный список.", reply_markup=get_blacklist_menu(session))
        return

    if session["awaiting"] == "blacklist_gift":
        value = message.text.strip()
        if value and value not in session["blacklist_gifts"]:
            session["blacklist_gifts"].append(value)
        session["awaiting"] = None
        await message.answer(f"🚫 Подарок «{value}» добавлен в чёрный список.", reply_markup=get_blacklist_menu(session))
        return
