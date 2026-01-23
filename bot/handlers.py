"""Обработчики команд Telegram бота."""

from infrastructure.api_client import BackendClient
from services.channel_service import ChannelService
from services.news_service import NewsService
from settings import get_backend_url
from telegram import ReplyKeyboardMarkup, Update
from telegram.error import BadRequest
from telegram.ext import ContextTypes
from utils.logger import get_logger

logger = get_logger(__name__)

# Максимальная длина сообщения Telegram (4096 символов)
MAX_MESSAGE_LENGTH = 4096

keyboard = [
    ["📰 Получить новости", "📋 Список каналов"],
    ["➕ Добавить канал", "➖ Удалить канал"],
]
reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Инициализация клиента и сервисов
_backend_url = get_backend_url()
logger.info(f"Инициализация бота с backend URL: {_backend_url}")
_backend_client = BackendClient(_backend_url)
_channel_service = ChannelService(_backend_client)
_news_service = NewsService(_backend_client)


async def _send_long_message(update: Update, text: str, reply_markup=None):
    """
    Отправить длинное сообщение, разбив его на части при необходимости.
    
    Args:
        update: объект Update
        text: текст для отправки
        reply_markup: клавиатура (опционально)
    """
    if len(text) <= MAX_MESSAGE_LENGTH:
        await update.message.reply_text(text, reply_markup=reply_markup)
        return
    
    # Разбиваем текст на части
    parts = []
    current_part = ""
    
    # Разбиваем по абзацам, чтобы не разрывать предложения
    paragraphs = text.split("\n\n")
    
    for paragraph in paragraphs:
        # Если текущая часть + новый абзац помещается
        if len(current_part) + len(paragraph) + 2 <= MAX_MESSAGE_LENGTH:
            if current_part:
                current_part += "\n\n" + paragraph
            else:
                current_part = paragraph
        else:
            # Сохраняем текущую часть и начинаем новую
            if current_part:
                parts.append(current_part)
            # Если абзац сам по себе слишком длинный, разбиваем его
            if len(paragraph) > MAX_MESSAGE_LENGTH:
                # Разбиваем по предложениям
                sentences = paragraph.split(". ")
                current_part = ""
                for sentence in sentences:
                    if len(current_part) + len(sentence) + 2 <= MAX_MESSAGE_LENGTH:
                        if current_part:
                            current_part += ". " + sentence
                        else:
                            current_part = sentence
                    else:
                        if current_part:
                            parts.append(current_part)
                        current_part = sentence
            else:
                current_part = paragraph
    
    if current_part:
        parts.append(current_part)
    
    # Отправляем все части
    for i, part in enumerate(parts):
        # Клавиатуру добавляем только к последнему сообщению
        markup = reply_markup if i == len(parts) - 1 else None
        await update.message.reply_text(part, reply_markup=markup)


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


async def list_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    logger.info(f"Запрос списка каналов от пользователя {user.id}")
    try:
        message = await _channel_service.list_channels()
        await update.message.reply_text(
            message, reply_markup=reply_markup, parse_mode="MarkdownV2"
        )
        logger.info(f"Список каналов успешно отправлен пользователю {user.id}")
    except Exception as e:
        logger.error(
            f"Ошибка при получении списка каналов для пользователя {user.id}: {e}"
        )
        await update.message.reply_text(
            "❌ Не удалось получить список каналов. Попробуйте позже.",
            reply_markup=reply_markup,
        )


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


async def handle_question(update: Update, context: ContextTypes.DEFAULT_TYPE, question: str):
    """Обработчик свободных вопросов пользователя (RAG completion)."""
    user = update.effective_user
    logger.info(f"Вопрос от пользователя {user.id}: '{question[:100]}...'")

    # Отправляем индикатор загрузки
    status_msg = await update.message.reply_text(
        "🤔 Ищу ответ на ваш вопрос...\nЭто может занять 10-30 секунд.",
        reply_markup=reply_markup,
    )

    try:
        answer = await _news_service.get_completion(user_id=user.id, question=question)
        
        # Пытаемся отредактировать сообщение
        try:
            await status_msg.edit_text(answer, reply_markup=reply_markup)
            logger.info(f"Ответ на вопрос успешно отправлен пользователю {user.id}")
        except BadRequest as e:
            # Если редактирование не удалось, удаляем старое сообщение и отправляем новое
            logger.warning(f"Не удалось отредактировать сообщение: {e}. Отправляю новое сообщение.")
            try:
                await status_msg.delete()
            except Exception:
                pass  # Игнорируем ошибки при удалении
            
            # Отправляем новое сообщение (с разбивкой на части, если нужно)
            await _send_long_message(update, answer, reply_markup)
            logger.info(f"Ответ на вопрос успешно отправлен пользователю {user.id} (новое сообщение)")
            
    except Exception as e:
        logger.error(f"Ошибка при получении ответа на вопрос для пользователя {user.id}: {e}")
        try:
            await status_msg.edit_text(
                "❌ Не удалось получить ответ на ваш вопрос. Попробуйте позже.",
                reply_markup=reply_markup,
            )
        except BadRequest:
            # Если не удалось отредактировать, отправляем новое сообщение
            try:
                await status_msg.delete()
            except Exception:
                pass
            await update.message.reply_text(
                "❌ Не удалось получить ответ на ваш вопрос. Попробуйте позже.",
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
        
        # Пытаемся отредактировать сообщение
        try:
            await status_msg.edit_text(summary, reply_markup=reply_markup)
            logger.info(f"Новости успешно отправлены пользователю {user.id} (отредактировано)")
        except BadRequest as e:
            # Если редактирование не удалось (например, текст слишком длинный),
            # удаляем старое сообщение и отправляем новое
            logger.warning(f"Не удалось отредактировать сообщение: {e}. Отправляю новое сообщение.")
            try:
                await status_msg.delete()
            except Exception:
                pass  # Игнорируем ошибки при удалении
            
            # Отправляем новое сообщение (с разбивкой на части, если нужно)
            await _send_long_message(update, summary, reply_markup)
            logger.info(f"Новости успешно отправлены пользователю {user.id} (новое сообщение)")
            
    except Exception as e:
        logger.error(f"Ошибка при получении новостей для пользователя {user.id}: {e}")
        try:
            await status_msg.edit_text(
                "❌ Не удалось получить новости. Попробуйте позже.",
                reply_markup=reply_markup,
            )
        except BadRequest:
            # Если не удалось отредактировать, отправляем новое сообщение
            try:
                await status_msg.delete()
            except Exception:
                pass
            await update.message.reply_text(
                "❌ Не удалось получить новости. Попробуйте позже.",
                reply_markup=reply_markup,
            )


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
            await update.message.reply_text(
                "❌ Не удалось добавить канал. Попробуйте позже.",
                reply_markup=reply_markup,
            )
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
            await update.message.reply_text(
                "❌ Не удалось удалить канал. Попробуйте позже.",
                reply_markup=reply_markup,
            )
        return

    if text == "📰 Получить новости" or text == "Новости":
        await get_news(update, context)

    elif text == "📋 Список каналов" or text == "Список каналов":
        await list_channels(update, context)

    elif text == "➕ Добавить канал" or text == "Добавить канал":
        await add_channel(update, context)

    elif text == "➖ Удалить канал" or text == "Удалить канал":
        await remove_channel(update, context)

    else:
        # Обрабатываем как свободный вопрос (RAG completion)
        await handle_question(update, context, text)
