"""
Пользовательские исключения для NewsHound.

Принцип SOLID:
- Single Responsibility: каждое исключение для конкретной ошибки
- Open/Closed: легко добавить новые исключения наследованием
"""


class NewsHoundException(Exception):
    """Базовое исключение для NewsHound."""

    def __init__(self, message: str = "Произошла ошибка в NewsHound"):
        self.message = message
        super().__init__(self.message)


class ChannelNotFoundException(NewsHoundException):
    """Исключение: канал не найден."""

    def __init__(self, channel_id: str):
        self.channel_id = channel_id
        super().__init__(f"Канал не найден: {channel_id}")


class ChannelAlreadyExistsException(NewsHoundException):
    """Исключение: канал уже существует."""

    def __init__(self, channel_id: str):
        self.channel_id = channel_id
        super().__init__(f"Канал уже добавлен: {channel_id}")


class VectorStoreException(NewsHoundException):
    """Исключение при работе с векторным хранилищем."""

    def __init__(self, message: str = "Ошибка векторного хранилища"):
        super().__init__(message)


class VectorStoreConnectionException(VectorStoreException):
    """Исключение: ошибка подключения к векторному хранилищу."""

    def __init__(self, host: str, port: int):
        super().__init__(f"Не удалось подключиться к Qdrant: {host}:{port}")


class LLMException(NewsHoundException):
    """Исключение при работе с LLM."""

    def __init__(self, message: str = "Ошибка LLM"):
        super().__init__(message)


class LLMTimeoutException(LLMException):
    """Исключение: таймаут LLM."""

    def __init__(self, timeout: float):
        super().__init__(f"LLM не ответила в течение {timeout} секунд")


class LLMRateLimitException(LLMException):
    """Исключение: превышен лимит запросов к LLM."""

    def __init__(self):
        super().__init__("Превышен лимит запросов к LLM API")


class RetrievalException(NewsHoundException):
    """Исключение при поиске документов."""

    def __init__(self, message: str = "Ошибка поиска документов"):
        super().__init__(message)


class DocumentNotFoundException(RetrievalException):
    """Исключение: документы не найдены."""

    def __init__(self, query: str):
        super().__init__(f"Не найдено документов по запросу: {query[:50]}...")


class TelegramParserException(NewsHoundException):
    """Исключение при парсинге Telegram."""

    def __init__(self, message: str = "Ошибка парсинга Telegram"):
        super().__init__(message)


class InvalidChannelLinkException(TelegramParserException):
    """Исключение: невалидная ссылка на канал."""

    def __init__(self, link: str):
        super().__init__(f"Невалидная ссылка на канал: {link}")


class TelegramAuthException(TelegramParserException):
    """Исключение: ошибка авторизации в Telegram."""

    def __init__(self, message: str = "Ошибка авторизации в Telegram"):
        super().__init__(message)
