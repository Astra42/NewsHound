"""Настройка логирования для бота."""

import logging
import sys
from pathlib import Path


def setup_logging(log_level: str = "INFO", log_file: str = None) -> logging.Logger:
    """
    Настройка логирования.

    Args:
        log_level: уровень логирования (DEBUG, INFO, WARNING, ERROR)
        log_file: путь к файлу для логирования (опционально)

    Returns:
        настроенный logger
    """
    logger = logging.getLogger("newshound_bot")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Получить logger с указанным именем.

    Args:
        name: имя logger (обычно __name__)

    Returns:
        logger
    """
    return logging.getLogger(f"newshound_bot.{name}")
