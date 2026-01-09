"""Обработчики команд Telegram бота."""

from infrastructure.api_client import BackendClient
from services.channel_service import ChannelService
from services.news_service import NewsService
from settings import get_backend_url
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes
from utils.logger import get_logger

logger = get_logger(__name__)

keyboard = [
    ["📰 Получить новости", "📋 Список каналов"],
    ["➕ Добавить канал", "➖ Удалить канал"],
    ["⚙️ Выбрать режим"],
]
reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

_backend_client = BackendClient(get_backend_url())
_channel_service = ChannelService(_backend_client)
_news_service = NewsService(_backend_client)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    logger.info(
        f"Команда /start от пользователя {user.id} (@{user.username}, {user.first_name})"
    )
    await update.message.reply_text(
        "Добро пожаловать в NewsHound! 🐶\nИспользуйте кнопки меню для управления.",
        reply_markup=reply_markup,
    )


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    logger.info(f"Команда /menu от пользователя {user.id}")
    await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)


async def set_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    logger.info(f"Команда /set_mode от пользователя {user.id}")
    await update.message.reply_text(
        "Выберите режим сбора новостей: ежедневный или еженедельный.",
        reply_markup=reply_markup,
    )


async def list_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    logger.info(f"Запрос списка каналов от пользователя {user.id}")
    try:
        message = await _channel_service.list_channels()
        await update.message.reply_text(
            message, reply_markup=reply_markup, parse_mode="Markdown"
        )
        logger.info(f"Список каналов успешно отправлен пользователю {user.id}")
    except Exception as e:
        logger.error(
            f"Ошибка при получении списка каналов для пользователя {user.id}: {e}"
        )
        raise


async def add_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    logger.info(f"Запрос на добавление канала от пользователя {user.id}")
    context.user_data["awaiting_channel_add"] = True
    await update.message.reply_text(
        "Введите название канала для добавления (например: @rbc_news или https://t.me/rbc_news).",
        reply_markup=reply_markup,
    )


async def remove_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    logger.info(f"Запрос на удаление канала от пользователя {user.id}")
    context.user_data["awaiting_channel_remove"] = True
    await update.message.reply_text(
        "Введите название канала для удаления (например: rbc_news или @rbc_news).",
        reply_markup=reply_markup,
    )


async def get_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    logger.info(f"Запрос новостей от пользователя {user.id}")

    status_msg = await update.message.reply_text(
        "⏳ Связываюсь с сервером новостей...\nЭто может занять 10-30 секунд.",
        reply_markup=reply_markup,
    )

    try:
        summary = await _news_service.get_summary(user_id=user.id, days=7)
        await status_msg.edit_text(summary)
        logger.info(f"Новости успешно отправлены пользователю {user.id}")
    except Exception as e:
        logger.error(f"Ошибка при получении новостей для пользователя {user.id}: {e}")
        raise


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений от кнопок."""
    user = update.effective_user
    text = update.message.text
    logger.info(
        f"Текстовое сообщение от пользователя {user.id} (@{user.username}): {text}"
    )

    user_data = context.user_data

    if user_data.get("awaiting_channel_add"):
        user_data.pop("awaiting_channel_add", None)
        channel_link = text.strip()
        logger.info(f"Добавление канала '{channel_link}' пользователем {user.id}")
        try:
            message = await _channel_service.add_channel(channel_link)
            await update.message.reply_text(message, reply_markup=reply_markup)
            logger.info(
                f"Канал '{channel_link}' успешно добавлен пользователем {user.id}"
            )
        except Exception as e:
            logger.error(
                f"Ошибка при добавлении канала '{channel_link}' пользователем {user.id}: {e}"
            )
            raise
        return

    if user_data.get("awaiting_channel_remove"):
        user_data.pop("awaiting_channel_remove", None)
        channel_username = text.strip().lstrip("@")
        logger.info(f"Удаление канала '{channel_username}' пользователем {user.id}")
        try:
            message = await _channel_service.remove_channel(channel_username)
            await update.message.reply_text(message, reply_markup=reply_markup)
            logger.info(
                f"Канал '{channel_username}' успешно удален пользователем {user.id}"
            )
        except Exception as e:
            logger.error(
                f"Ошибка при удалении канала '{channel_username}' пользователем {user.id}: {e}"
            )
            raise
        return

    if text == "📰 Получить новости" or text == "Новости":
        await get_news(update, context)

    elif text == "📋 Список каналов" or text == "Список каналов":
        await list_channels(update, context)

    elif text == "➕ Добавить канал" or text == "Добавить канал":
        await add_channel(update, context)

    elif text == "➖ Удалить канал" or text == "Удалить канал":
        await remove_channel(update, context)

    elif text == "⚙️ Выбрать режим" or text == "Выбрать режим":
        await set_mode(update, context)

    else:
        logger.warning(f"Неизвестная команда от пользователя {user.id}: {text}")
        await update.message.reply_text(
            "Неизвестная команда. Используйте кнопки ниже.", reply_markup=reply_markup
        )
