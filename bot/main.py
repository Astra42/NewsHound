import asyncio
import os

import nest_asyncio
from handlers import (
    add_channel,
    get_news,
    handle_text,
    list_channels,
    menu,
    remove_channel,
    start,
)
from settings import get_bot_token
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from utils.logger import setup_logging

nest_asyncio.apply()

logger = setup_logging(
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    log_file=os.getenv("LOG_FILE", "logs/bot.log"),
)


async def main():
    logger.info("Запуск NewsHound бота...")

    bot_token = get_bot_token()
    app = Application.builder().token(bot_token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add_channel", add_channel))
    app.add_handler(CommandHandler("remove_channel", remove_channel))
    app.add_handler(CommandHandler("list_channels", list_channels))
    app.add_handler(CommandHandler("get_news", get_news))
    app.add_handler(CommandHandler("menu", menu))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info("Обработчики зарегистрированы")

    bot_info = await app.bot.get_me()
    logger.info(
        f"Бот запущен: @{bot_info.username} (ID: {bot_info.id}, "
        f"Имя: {bot_info.first_name})"
    )

    await app.run_polling()


if __name__ == "__main__":
    try:
        # Проверяем токен до запуска async функции
        try:
            get_bot_token()
        except ValueError as e:
            logger.error(f"Ошибка конфигурации: {e}")
            print(f"\n❌ Ошибка: {e}\n")
            print("Для запуска бота необходимо:")
            print("1. Создать бота через @BotFather в Telegram")
            print("2. Получить токен бота")
            print("3. Добавить BOT_TOKEN=ваш_токен в файл .env")
            exit(1)
        
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.exception(f"Критическая ошибка: {e}")
        raise
