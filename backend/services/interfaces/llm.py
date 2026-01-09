"""
Интерфейс для LLM сервиса.

Принцип SOLID:
- Interface Segregation: только методы для работы с LLM
- Dependency Inversion: сервисы зависят от этого интерфейса
"""

from abc import ABC, abstractmethod
from typing import List, Optional


class ILLMService(ABC):
    """Абстрактный интерфейс для LLM сервиса."""
    
    @abstractmethod
    def generate(
        self, 
        prompt: str, 
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> str:
        """
        Генерация текста на основе промпта.
        
        Args:
            prompt: входной промпт
            max_tokens: максимальное количество токенов
            temperature: температура генерации
            
        Returns:
            сгенерированный текст
        """
        pass
    
    @abstractmethod
    async def agenerate(
        self, 
        prompt: str, 
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> str:
        """
        Асинхронная генерация текста.
        
        Args:
            prompt: входной промпт
            max_tokens: максимальное количество токенов
            temperature: температура генерации
            
        Returns:
            сгенерированный текст
        """
        pass
    
    @abstractmethod
    def generate_with_context(
        self, 
        question: str, 
        context: List[str],
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Генерация ответа с учётом контекста (RAG).
        
        Args:
            question: вопрос пользователя
            context: список контекстных документов
            system_prompt: системный промпт
            
        Returns:
            сгенерированный ответ
        """
        pass
    
    @abstractmethod
    async def agenerate_with_context(
        self, 
        question: str, 
        context: List[str],
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Асинхронная генерация ответа с контекстом.
        """
        pass
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Название используемой модели."""
        pass

