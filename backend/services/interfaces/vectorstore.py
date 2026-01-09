"""
Интерфейс для репозитория векторного хранилища.

Принцип SOLID:
- Interface Segregation: CRUD операции + поиск
- Dependency Inversion: сервисы зависят от абстракции
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from backend.domain.document import Document, SearchResult


class IVectorStoreRepository(ABC):
    """Абстрактный интерфейс для репозитория векторного хранилища."""
    
    # =========================================================================
    # CRUD операции
    # =========================================================================
    
    @abstractmethod
    def add_documents(
        self, 
        documents: List[Document], 
        batch_size: int = 100
    ) -> int:
        """
        Добавление документов в хранилище.
        
        Args:
            documents: список документов
            batch_size: размер батча
            
        Returns:
            количество добавленных документов
        """
        pass
    
    @abstractmethod
    async def aadd_documents(
        self, 
        documents: List[Document], 
        batch_size: int = 100
    ) -> int:
        """
        Асинхронное добавление документов.
        """
        pass
    
    @abstractmethod
    def delete_documents(
        self, 
        document_ids: Optional[List[str]] = None,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Удаление документов по ID или фильтру.
        
        Args:
            document_ids: список ID для удаления
            filter_dict: фильтр по метаданным
            
        Returns:
            количество удалённых документов
        """
        pass
    
    @abstractmethod
    def get_document(self, document_id: str) -> Optional[Document]:
        """
        Получение документа по ID.
        """
        pass
    
    # =========================================================================
    # Поиск
    # =========================================================================
    
    @abstractmethod
    def search(
        self, 
        query: str, 
        k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """
        Семантический поиск документов.
        
        Args:
            query: поисковый запрос
            k: количество результатов
            filter_dict: фильтр по метаданным
            
        Returns:
            список результатов поиска
        """
        pass
    
    @abstractmethod
    async def asearch(
        self, 
        query: str, 
        k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """
        Асинхронный семантический поиск.
        """
        pass
    
    @abstractmethod
    def search_by_vector(
        self, 
        vector: List[float], 
        k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """
        Поиск по вектору (если эмбеддинг уже создан).
        """
        pass
    
    # =========================================================================
    # Управление коллекцией
    # =========================================================================
    
    @abstractmethod
    def create_collection(self, recreate: bool = False) -> None:
        """
        Создание коллекции.
        
        Args:
            recreate: пересоздать если существует
        """
        pass
    
    @abstractmethod
    def delete_collection(self) -> None:
        """Удаление коллекции."""
        pass
    
    @abstractmethod
    def get_collection_info(self) -> Dict[str, Any]:
        """
        Информация о коллекции.
        
        Returns:
            словарь с информацией (points_count, status и т.д.)
        """
        pass
    
    @abstractmethod
    def collection_exists(self) -> bool:
        """Проверка существования коллекции."""
        pass

