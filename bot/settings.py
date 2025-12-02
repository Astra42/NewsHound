import os
from dotenv import load_dotenv

# Загрузка переменных из .env
load_dotenv()

def get_bot_token():
    return os.getenv("BOT_TOKEN")
