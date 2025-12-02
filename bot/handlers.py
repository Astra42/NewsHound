from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

# Определяем клавиатуру с кнопками
keyboard = [
    ["Новости", "Список каналов"],
    ["Добавить канал", "Удалить канал"],
    ["Выбрать режим"]
]
reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Команда /start вызвана")  # Отладочное сообщение
    await update.message.reply_text(
        "Добро пожаловать! Используйте команды для настройки бота.",
        reply_markup=reply_markup
    )

async def set_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Команда /set_mode вызвана")  # Отладочное сообщение
    await update.message.reply_text(
        "Выберите режим сбора новостей: ежедневный или еженедельный.",
        reply_markup=reply_markup
    )

async def add_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Команда /add_channel вызвана")  # Отладочное сообщение
    await update.message.reply_text(
        "Введите название канала для добавления.",
        reply_markup=reply_markup
    )

async def remove_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Команда /remove_channel вызвана")  # Отладочное сообщение
    await update.message.reply_text(
        "Введите название канала для удаления.",
        reply_markup=reply_markup
    )

async def list_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Команда /list_channels вызвана")  # Отладочное сообщение
    await update.message.reply_text(
        "Ваш список каналов пуст.",
        reply_markup=reply_markup
    )

async def get_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Команда /get_news вызвана")  # Отладочное сообщение
    await update.message.reply_text(
        "Здесь будут отображаться последние новости.",
        reply_markup=reply_markup
    )

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Команда /menu вызвана")  # Отладочное сообщение
    await update.message.reply_text(
        "Выберите действие:",
        reply_markup=reply_markup
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Получено сообщение: {update.message.text}")  # Отладочное сообщение
    if update.message.text == "Новости":
        await update.message.reply_text("Вот ваши последние новости!", reply_markup=reply_markup)
    elif update.message.text == "Список каналов":
        await update.message.reply_text("Ваш список каналов пуст.", reply_markup=reply_markup)
    elif update.message.text == "Добавить канал":
        await update.message.reply_text("Введите название канала для добавления.", reply_markup=reply_markup)
    elif update.message.text == "Удалить канал":
        await update.message.reply_text("Введите название канала для удаления.", reply_markup=reply_markup)
    elif update.message.text == "Выбрать режим":
        await update.message.reply_text("Выберите режим: ежедневный или еженедельный.", reply_markup=reply_markup)
    else:
        await update.message.reply_text("Неизвестная команда. Используйте кнопки ниже.", reply_markup=reply_markup)
