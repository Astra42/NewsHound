"""
Интерфейс для сервиса эмбеддингов.

Принцип SOLID:
- Interface Segregation: только методы для работы с эмбеддингами
- Single Responsibility: только создание векторных представлений
"""

from abc import ABC, abstractmethod
from typing import List


class IEmbeddingService(ABC):
    """Абстрактный интерфейс для сервиса эмбеддингов."""
    
    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """
        Создание эмбеддинга для поискового запроса.
        
        Args:
            text: текст запроса
            
        Returns:
            вектор эмбеддинга
        """
        pass
    
    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Создание эмбеддингов для списка документов.
        
        Args:
            texts: список текстов
            
        Returns:
            список векторов эмбеддингов
        """
        pass
    
    @abstractmethod
    async def aembed_query(self, text: str) -> List[float]:
        """
        Асинхронное создание эмбеддинга для запроса.
        """
        pass
    
    @abstractmethod
    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Асинхронное создание эмбеддингов для документов.
        """
        pass
    
    @property
    @abstractmethod
    def vector_size(self) -> int:
        """Размерность вектора эмбеддинга."""
        pass
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Название модели эмбеддингов."""
        pass

