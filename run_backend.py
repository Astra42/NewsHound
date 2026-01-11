#!/usr/bin/env python3
"""
Скрипт для локального запуска NewsHound Backend API.

Устанавливает PYTHONPATH и запускает приложение через uvicorn.
"""

import os
import sys
from pathlib import Path

# Добавляем корень проекта в PYTHONPATH
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# Устанавливаем PYTHONPATH для дочерних процессов
os.environ["PYTHONPATH"] = str(project_root)

if __name__ == "__main__":
    import uvicorn
    from core.config import settings

    uvicorn.run(
        "app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_debug,
    )
