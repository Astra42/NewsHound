import asyncio
import nest_asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from bot.settings import get_bot_token
from bot.handlers import start, set_mode, add_channel, remove_channel, list_channels, get_news, menu, handle_text

# Разрешаем повторное использование текущего цикла событий
nest_asyncio.apply()

async def main():
    app = Application.builder().token(get_bot_token()).build()

    # Регистрация обработчиков команд
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("set_mode", set_mode))
    app.add_handler(CommandHandler("add_channel", add_channel))
    app.add_handler(CommandHandler("remove_channel", remove_channel))
    app.add_handler(CommandHandler("list_channels", list_channels))
    app.add_handler(CommandHandler("get_news", get_news))
    app.add_handler(CommandHandler("menu", menu))  # Новый обработчик для меню

    # Обработчик текстовых сообщений
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("Бот запущен!")
    await app.run_polling()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен пользователем.")
