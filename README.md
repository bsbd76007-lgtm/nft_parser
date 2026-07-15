# NFT Gift Parser Bot

Telegram бот для поиска NFT подарков с Telegram владельцами в реальном времени.

## Возможности

- 🔍 Поиск NFT подарков по 100+ коллекциям
- 👤 Только Telegram владельцы (исключение TON кошельков)
- 💰 Цены и статусы с Fragment.com
- 🎯 Фильтры: Model, Backdrop, Symbol
- 🎲 Случайный поиск по всем коллекциям
- 📥 CSV экспорт результатов
- 👁 Слежение за подарками с уведомлениями (BETA возможно не стабильная работа)
- ⭐ Premium система с расширенными лимитами
- 📣 Рассылка с фото и HTML
- 📢 Обязательная подписка на канал

## Установка

### 1. Клонируйте репозиторий

```bash
git clone https://github.com/your-repo/nft-gift-bot.git
cd nft-gift-bot
```

### 2. Установите зависимости

```bash
pip install -r requirements.txt
```

### 3. Настройте переменные окружения

Скопируйте `.env.example` в `.env` и заполните:

```bash
cp .env.example .env
```

Отредактируйте `.env`:

```env
BOT_TOKEN=ваш_токен_бота
DATABASE_URL=postgresql://user:password@localhost:5432/nft_bot
ADMINS=ваш_telegram_id
```

### 4. Создайте базу данных PostgreSQL

```bash
createdb nft_bot
```

### 5. Запустите бота

```bash
python main.py
```

## Структура проекта

```
├── main.py                 # Запуск
├── src/
│   ├── config.py          # Конфигурация
│   ├── database/
│   │   ├── models.py      # SQLAlchemy модели
│   │   └── connection.py  # Подключение к БД
│   ├── services/
│   │   ├── fragment_parser.py  # Парсер
│   │   ├── tracking_service.py # Сервис слежения
│   │   └── user_service.py     # Сервис пользователей
│   ├── handlers/
│   │   ├── start.py       # /start, /help
│   │   ├── search.py      # Поиск подарков
│   │   ├── tools.py       # Инструменты (BETA)
│   │   └── admin.py       # Админ-панель
│   └── keyboards/
│       └── inline.py      # Inline клавиатуры
├── requirements.txt
└── .env.example
```

## Команды бота

- `/start` — Главное меню
- `/find` — Поиск подарков
- `/stats` — Статистика
- `/help` — Справка
- `/admin` — Админ-панель (только для админов)

## Premium система

| Функция | Обычный | Premium | Админ |
|---------|---------|---------|-------|
| Слежение | 1 шт | 5 шт | ∞ |
| Интервал проверки | 1 час | от 10 мин | от 10 мин |

## Требования

- Python 3.11+
- PostgreSQL 14+


## Bot Info
- Bot: @SureParserBot
- Name: Sure Parser Nft
- Owner: @Iizargenov (5780645031)
