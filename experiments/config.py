"""
Общая конфигурация для RAG системы NewsHound.
"""

import os

from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# API КЛЮЧИ
# =============================================================================

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
TELEGRAM_API_ID = os.getenv("APP_ID_TG")
TELEGRAM_API_HASH = os.getenv("API_HASH_TG")

# =============================================================================
# МОДЕЛИ
# =============================================================================

# LLM для генерации ответов
LLM_MODEL = "mistral-small-latest"

# LLM для оценки
JUDGE_MODEL = "mistral-small-latest"

# Модель эмбеддингов
EMBEDDING_MODEL = "sergeyzh/rubert-mini-frida"

# Устройство для эмбеддингов
EMBEDDING_DEVICE = "cpu"

# =============================================================================
# TELEGRAM КАНАЛЫ
# =============================================================================

TELEGRAM_CHANNELS = [
    "@tass_agency",
    "@rian_ru",
    "@kommersant",
    "@gazeta_ru",
    "@meduzalive",
    "@rbc_news",
]

# Лимит сообщений на канал
TELEGRAM_MESSAGE_LIMIT = 100

# =============================================================================
# RAG ПАРАМЕТРЫ
# =============================================================================

# Chunking
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# Retrieval
RETRIEVAL_K = 5

# =============================================================================
# QDRANT (Docker)
# =============================================================================

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "news")

# =============================================================================
# ПУТИ К ФАЙЛАМ
# =============================================================================

# Тестовые вопросы
QUESTIONS_FILE = "sample_questions.txt"

# Результаты оценки
EVAL_RESULTS_FILE = "eval_results.json"

# Тестовый датасет
TEST_DATASET_FILE = "test_dataset.json"

# Тестовые посты (pickle файл)
TEST_POSTS_FILE = "../test_data/test_posts.pkl"

# =============================================================================
# НАСТРОЙКИ ОЦЕНКИ (DeepEval)
# =============================================================================

# Пороги для метрик (0.0 - 1.0)
ANSWER_RELEVANCY_THRESHOLD = 0.7
CONTEXTUAL_PRECISION_THRESHOLD = 0.7

# Количество похожих документов для ground truth
GROUND_TRUTH_SIMILAR_DOCS = 3


