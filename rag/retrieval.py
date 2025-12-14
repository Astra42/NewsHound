import config as cfg
from vectorstore import VectorStore


def get_qdrant_client():
    """
    Получение клиента Qdrant.

    Returns:
        VectorStore instance или None при ошибке
    """
    try:
        return VectorStore(host=cfg.QDRANT_HOST, port=cfg.QDRANT_PORT)
    except Exception as e:
        print(f"Ошибка подключения к Qdrant: {e}")
        print("Убедитесь, что Qdrant запущен: docker-compose up -d")
        return None


def retrieve_context(vectorstore, question: str) -> list[str]:
    """
    Получение релевантного контекста из векторного хранилища.

    Args:
        vectorstore: VectorStore (Qdrant) или FAISS vectorstore
        question: поисковый запрос

    Returns:
        список текстов документов
    """
    if hasattr(vectorstore, "search"):
        # Qdrant VectorStore
        docs = vectorstore.search(question, k=cfg.RETRIEVAL_K)
        return [doc["content"] for doc in docs]
    else:
        # FAISS vectorstore
        docs = vectorstore.similarity_search(question, k=cfg.RETRIEVAL_K)
        return [doc.page_content for doc in docs]
