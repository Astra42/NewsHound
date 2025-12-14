"""
Полный пайплайн оценки RAG системы с использованием DeepEval метрик.

Использует тестовый датасет постов для создания ground truth.
Метрики:
- AnswerRelevancyMetric: оценка релевантности ответа
- ContextualPrecisionMetric: оценка точности retrieval
"""

import asyncio
import json
import os
import pickle
import random
import time
from datetime import datetime
from typing import Any, Dict, List

import config as cfg
import httpx
from deepeval.metrics import AnswerRelevancyMetric, ContextualPrecisionMetric
from deepeval.models.base_model import DeepEvalBaseLLM
from deepeval.test_case import LLMTestCase
from langchain_mistralai import ChatMistralAI
from prompts import QUESTION_GEN_PROMPT
from retrieval import get_qdrant_client, retrieve_context
from vectorstore import VectorStore


class MistralJudgeModel(DeepEvalBaseLLM):
    """Обертка для Mistral модели для использования в DeepEval."""

    def __init__(self, model_name: str = None):
        self.model_name = model_name or cfg.JUDGE_MODEL
        self.model = ChatMistralAI(
            model=self.model_name,
            api_key=cfg.MISTRAL_API_KEY,
            max_retries=5,  # Увеличено количество повторных попыток
            timeout=60.0,  # Увеличен таймаут до 60 секунд
        )

    def load_model(self):
        return self.model

    def generate(self, prompt: str) -> str:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.model.invoke(prompt)
                return response.content
            except (
                httpx.RemoteProtocolError,
                httpx.ConnectError,
                httpx.TimeoutException,
            ) as e:
                if attempt < max_retries - 1:
                    wait_time = 2**attempt
                    time.sleep(wait_time)
                else:
                    return f"[Ошибка генерации judge: {type(e).__name__}]"
            except Exception as e:
                return f"[Ошибка judge: {type(e).__name__}]"

        return "[Не удалось сгенерировать ответ judge]"

    async def a_generate(self, prompt: str) -> str:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = await self.model.ainvoke(prompt)
                return response.content
            except (
                httpx.RemoteProtocolError,
                httpx.ConnectError,
                httpx.TimeoutException,
            ) as e:
                if attempt < max_retries - 1:
                    wait_time = 2**attempt
                    await asyncio.sleep(wait_time)
                else:
                    return f"[Ошибка генерации judge: {type(e).__name__}]"
            except Exception as e:
                return f"[Ошибка judge: {type(e).__name__}]"

        return "[Не удалось сгенерировать ответ judge]"

    def get_model_name(self) -> str:
        return self.model_name


def generate_answer(llm, question: str, context: list[str], max_retries: int = 3) -> str:
    """
    Генерация ответа на основе контекста с обработкой ошибок.
    
    Args:
        llm: модель для генерации
        question: вопрос
        context: список контекстных документов
        max_retries: максимальное количество попыток при ошибках
        
    Returns:
        сгенерированный ответ
    """
    context_str = "\n".join(context)
    prompt = f"Контекст: {context_str}\n\nВопрос: {question}\n\nОтвет:"
    
    for attempt in range(max_retries):
        try:
            response = llm.invoke(prompt)
            return response.content
        except (httpx.RemoteProtocolError, httpx.ConnectError, httpx.TimeoutException, ConnectionError) as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Экспоненциальная задержка: 1s, 2s, 4s
                print(f"    Попытка {attempt + 1}/{max_retries} не удалась, повтор через {wait_time}с... ({type(e).__name__})")
                time.sleep(wait_time)
            else:
                print(f"    Все попытки исчерпаны, ошибка: {e}")
                return f"[Ошибка генерации: {type(e).__name__}]"
        except Exception as e:
            print(f"    Неожиданная ошибка при генерации: {e}")
            return f"[Ошибка генерации: {type(e).__name__}]"
    
    return "[Не удалось сгенерировать ответ]"


def load_test_posts(filepath: str = None) -> List[Dict[str, Any]]:
    """
    Загрузка тестовых постов из pickle файла.

    Args:
        filepath: путь к файлу test_posts.pkl

    Returns:
        список постов в формате {"content": str, "metadata": dict}
    """
    filepath = filepath or cfg.TEST_POSTS_FILE

    # Пробуем разные пути
    possible_paths = [
        filepath,
        os.path.join("rag", filepath),
        os.path.join("test_data", "test_posts.pkl"),
        os.path.join("..", "test_data", "test_posts.pkl"),
    ]

    for path in possible_paths:
        if os.path.exists(path):
            print(f"Загрузка тестовых постов из {path}...")
            with open(path, "rb") as f:
                posts = pickle.load(f)

            # Преобразуем в стандартный формат
            if isinstance(posts, list):
                # Если это список словарей
                formatted_posts = []
                for post in posts:
                    if isinstance(post, dict):
                        formatted_posts.append(
                            {
                                "content": post.get("text", post.get("content", "")),
                                "metadata": {
                                    "source": "telegram",
                                    "channel": post.get("channel", ""),
                                    "date": post.get("date", ""),
                                    "id": post.get("id", ""),
                                },
                            }
                        )
                print(f"Загружено {len(formatted_posts)} постов")
                return formatted_posts
            else:
                print(f"Неожиданный формат данных в {path}")
                return []

    print(f"Файл test_posts.pkl не найден по путям: {possible_paths}")
    return []


def generate_ground_truth_documents(
    vectorstore: VectorStore, source_document: str, k: int = None
) -> List[str]:
    """
    Генерация ground truth документов для вопроса.

    Ground truth включает:
    1. Исходный документ (source_document)
    2. Похожие документы через semantic search

    Args:
        vectorstore: VectorStore для поиска
        source_document: исходный документ
        k: количество похожих документов для поиска

    Returns:
        список текстов документов (ground truth)
    """
    k = k or cfg.GROUND_TRUTH_SIMILAR_DOCS

    # Ищем похожие документы (используем сам документ как запрос)
    similar_docs_result = vectorstore.search(source_document, k=k + 1)

    # Извлекаем контент из результатов
    similar_docs = [
        doc["content"] if isinstance(doc, dict) else doc for doc in similar_docs_result
    ]

    # Собираем ground truth: source + похожие (исключая дубликаты)
    ground_truth = [source_document]

    for content in similar_docs:
        # Добавляем только если это не сам source document и еще нет в списке
        if content != source_document and content not in ground_truth:
            ground_truth.append(content)
            if len(ground_truth) >= k + 1:  # +1 для source
                break

    return ground_truth


def generate_test_cases_with_ground_truth(
    vectorstore: VectorStore, test_posts: List[Dict[str, Any]], num_cases: int = 10
) -> List[Dict[str, Any]]:
    """
    Генерация тест-кейсов с ground truth из тестовых постов.

    Args:
        vectorstore: VectorStore с индексированными документами
        test_posts: список тестовых постов
        num_cases: количество тест-кейсов

    Returns:
        список тест-кейсов с ground truth
    """
    print(f"Генерация {num_cases} тест-кейсов с ground truth...")

    # LLM для генерации вопросов
    llm = ChatMistralAI(
        model=cfg.JUDGE_MODEL, api_key=cfg.MISTRAL_API_KEY, max_retries=5, timeout=60.0
    )

    # Выбираем случайные посты
    selected_posts = random.sample(test_posts, min(num_cases, len(test_posts)))

    test_cases = []
    for i, post in enumerate(selected_posts, 1):
        print(f"[{i}/{len(selected_posts)}] Генерация тест-кейса...")

        source_content = post["content"]

        # Генерируем вопрос из документа
        prompt = QUESTION_GEN_PROMPT.format(document=source_content)

        try:
            response = llm.invoke(prompt)
            question = response.content.strip().strip("\"'")

            # Генерируем ground truth документы
            ground_truth_docs = generate_ground_truth_documents(
                vectorstore, source_content, k=cfg.GROUND_TRUTH_SIMILAR_DOCS
            )

            test_case = {
                "question": question,
                "source_document": source_content,
                "ground_truth_documents": ground_truth_docs,
                "metadata": post.get("metadata", {}),
            }

            test_cases.append(test_case)
            print(f"    Вопрос: {question[:60]}...")
            print(f"    Ground truth документов: {len(ground_truth_docs)}")

        except Exception as e:
            print(f"    Ошибка: {e}")
            continue

    print(f"\nСгенерировано {len(test_cases)} тест-кейсов")
    return test_cases


def evaluate_with_deepeval(
    vectorstore: VectorStore,
    test_cases: List[Dict[str, Any]],
    llm_generation: ChatMistralAI,
    judge_model: MistralJudgeModel,
) -> List[Dict[str, Any]]:
    """
    Оценка RAG системы с использованием DeepEval метрик.

    Args:
        vectorstore: VectorStore для retrieval
        test_cases: список тест-кейсов с ground truth
        llm_generation: LLM для генерации ответов
        judge_model: LLM для оценки (Judge)

    Returns:
        список результатов оценки
    """
    print(f"\nОценка {len(test_cases)} тест-кейсов с DeepEval метриками...\n")

    # Инициализация метрик
    answer_relevancy_metric = AnswerRelevancyMetric(
        threshold=cfg.ANSWER_RELEVANCY_THRESHOLD, model=judge_model, include_reason=True
    )

    contextual_precision_metric = ContextualPrecisionMetric(
        threshold=cfg.CONTEXTUAL_PRECISION_THRESHOLD,
        model=judge_model,
        include_reason=True,
    )

    results = []

    for i, test_case in enumerate(test_cases, 1):
        question = test_case["question"]
        ground_truth_docs = test_case["ground_truth_documents"]

        print(f"[{i}/{len(test_cases)}] {question[:50]}...")

        # Добавляем небольшую задержку между запросами для снижения нагрузки на API
        if i > 1:
            time.sleep(2)  # 2 секунды между запросами

        # 1. Retrieval
        retrieved_contexts = retrieve_context(vectorstore, question)

        # 2. Generation (с обработкой ошибок)
        try:
            answer = generate_answer(
                llm_generation, question, retrieved_contexts, max_retries=3
            )
        except Exception as e:
            print(f"    Критическая ошибка при генерации ответа: {e}")
            answer = f"[Ошибка: {type(e).__name__}]"

        # 3. Оценка AnswerRelevancy
        test_case_ar = LLMTestCase(
            input=question,
            actual_output=answer,
            retrieval_context=retrieved_contexts,
            expected_output=None,
        )

        try:
            answer_relevancy_metric.measure(test_case_ar)
            answer_relevancy_score = answer_relevancy_metric.score
            answer_relevancy_passed = answer_relevancy_metric.is_successful()
            answer_relevancy_reason = getattr(answer_relevancy_metric, "reason", None)
        except Exception as e:
            print(f"    Ошибка AnswerRelevancy: {e}")
            answer_relevancy_score = None
            answer_relevancy_passed = False
            answer_relevancy_reason = str(e)

        # 4. Оценка ContextualPrecision
        test_case_cp = LLMTestCase(
            input=question,
            actual_output=answer,
            retrieval_context=retrieved_contexts,
            expected_output=ground_truth_docs,
        )

        try:
            contextual_precision_metric.measure(test_case_cp)
            contextual_precision_score = contextual_precision_metric.score
            contextual_precision_passed = contextual_precision_metric.is_successful()
            contextual_precision_reason = getattr(
                contextual_precision_metric, "reason", None
            )
        except Exception as e:
            print(f"    Ошибка ContextualPrecision: {e}")
            contextual_precision_score = None
            contextual_precision_passed = False
            contextual_precision_reason = str(e)

        result = {
            "question": question,
            "source_document": test_case["source_document"],
            "ground_truth_documents": ground_truth_docs,
            "retrieved_documents": retrieved_contexts,
            "answer": answer,
            "scores": {
                "answer_relevancy": {
                    "score": answer_relevancy_score,
                    "passed": answer_relevancy_passed,
                    "reason": answer_relevancy_reason,
                },
                "contextual_precision": {
                    "score": contextual_precision_score,
                    "passed": contextual_precision_passed,
                    "reason": contextual_precision_reason,
                },
            },
        }

        results.append(result)

        print(
            f"    AnswerRelevancy: {answer_relevancy_score:.3f} {'✓' if answer_relevancy_passed else '✗'}"
        )
        print(
            f"    ContextualPrecision: {contextual_precision_score:.3f} {'✓' if contextual_precision_passed else '✗'}"
        )

    return results


def aggregate_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Агрегация результатов оценки."""
    answer_relevancy_scores = [
        r["scores"]["answer_relevancy"]["score"]
        for r in results
        if r["scores"]["answer_relevancy"]["score"] is not None
    ]

    contextual_precision_scores = [
        r["scores"]["contextual_precision"]["score"]
        for r in results
        if r["scores"]["contextual_precision"]["score"] is not None
    ]

    answer_relevancy_passed = sum(
        1 for r in results if r["scores"]["answer_relevancy"].get("passed", False)
    )

    contextual_precision_passed = sum(
        1 for r in results if r["scores"]["contextual_precision"].get("passed", False)
    )

    summary = {
        "answer_relevancy": {
            "average_score": sum(answer_relevancy_scores) / len(answer_relevancy_scores)
            if answer_relevancy_scores
            else None,
            "min_score": min(answer_relevancy_scores)
            if answer_relevancy_scores
            else None,
            "max_score": max(answer_relevancy_scores)
            if answer_relevancy_scores
            else None,
            "pass_rate": answer_relevancy_passed / len(results) if results else 0,
            "passed": answer_relevancy_passed,
            "total": len(results),
        },
        "contextual_precision": {
            "average_score": sum(contextual_precision_scores)
            / len(contextual_precision_scores)
            if contextual_precision_scores
            else None,
            "min_score": min(contextual_precision_scores)
            if contextual_precision_scores
            else None,
            "max_score": max(contextual_precision_scores)
            if contextual_precision_scores
            else None,
            "pass_rate": contextual_precision_passed / len(results) if results else 0,
            "passed": contextual_precision_passed,
            "total": len(results),
        },
    }

    return summary


def print_detailed_summary(summary: Dict[str, Any], results: List[Dict[str, Any]]):
    """Вывод детального отчета."""
    print("\n" + "=" * 70)
    print("ДЕТАЛЬНЫЙ ОТЧЕТ ПО ОЦЕНКЕ RAG СИСТЕМЫ")
    print("=" * 70)

    # Answer Relevancy
    ar = summary["answer_relevancy"]
    print("\n📊 Answer Relevancy (Релевантность ответа):")
    print(
        f"  Средний балл: {ar['average_score']:.3f}"
        if ar["average_score"]
        else "  Средний балл: N/A"
    )
    print(
        f"  Мин/Макс: {ar['min_score']:.3f} / {ar['max_score']:.3f}"
        if ar["min_score"]
        else "  Мин/Макс: N/A"
    )
    print(f"  Pass Rate: {ar['pass_rate'] * 100:.1f}% ({ar['passed']}/{ar['total']})")
    print(f"  Порог: {cfg.ANSWER_RELEVANCY_THRESHOLD}")

    cp = summary["contextual_precision"]
    print("\n📊 Contextual Precision (Точность Retrieval):")
    print(
        f"  Средний балл: {cp['average_score']:.3f}"
        if cp["average_score"]
        else "  Средний балл: N/A"
    )
    print(
        f"  Мин/Макс: {cp['min_score']:.3f} / {cp['max_score']:.3f}"
        if cp["min_score"]
        else "  Мин/Макс: N/A"
    )
    print(f"  Pass Rate: {cp['pass_rate'] * 100:.1f}% ({cp['passed']}/{cp['total']})")
    print(f"  Порог: {cfg.CONTEXTUAL_PRECISION_THRESHOLD}")

    failed_cases = [
        r
        for r in results
        if not r["scores"]["answer_relevancy"].get("passed", True)
        or not r["scores"]["contextual_precision"].get("passed", True)
    ]

    if failed_cases:
        print(f"\n⚠️  Неуспешных тест-кейсов: {len(failed_cases)}")
        print("\nПримеры неуспешных тест-кейсов:")
        for i, case in enumerate(failed_cases[:3], 1):
            print(f"\n  {i}. Вопрос: {case['question'][:60]}...")
            if not case["scores"]["answer_relevancy"]["passed"]:
                print(
                    f"     AnswerRelevancy: {case['scores']['answer_relevancy']['score']:.3f}"
                )
            if not case["scores"]["contextual_precision"]["passed"]:
                print(
                    f"     ContextualPrecision: {case['scores']['contextual_precision']['score']:.3f}"
                )

    print("\n" + "=" * 70)


def save_detailed_report(
    results: List[Dict[str, Any]], summary: Dict[str, Any], filepath: str = None
):
    """Сохранение детального отчета."""
    filepath = (
        filepath or f"full_eval_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )

    report = {
        "timestamp": datetime.now().isoformat(),
        "num_test_cases": len(results),
        "config": {
            "judge_model": cfg.JUDGE_MODEL,
            "llm_model": cfg.LLM_MODEL,
            "embedding_model": cfg.EMBEDDING_MODEL,
            "retrieval_k": cfg.RETRIEVAL_K,
            "answer_relevancy_threshold": cfg.ANSWER_RELEVANCY_THRESHOLD,
            "contextual_precision_threshold": cfg.CONTEXTUAL_PRECISION_THRESHOLD,
        },
        "summary": summary,
        "detailed_results": results,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\nДетальный отчет сохранен: {filepath}")


def run_full_evaluation(
    vectorstore: VectorStore = None,
    test_posts: List[Dict[str, Any]] = None,
    num_test_cases: int = 10,
    save_report: bool = True,
) -> Dict[str, Any]:
    """
    Запуск полного пайплайна оценки RAG системы.

    Args:
        vectorstore: VectorStore (если None - подключается к Qdrant)
        test_posts: список тестовых постов (если None - загружается из файла)
        num_test_cases: количество тест-кейсов для генерации
        save_report: сохранять ли отчет

    Returns:
        словарь с результатами оценки
    """
    print("=" * 70)
    print("ПОЛНЫЙ ПАЙПЛАЙН ОЦЕНКИ RAG СИСТЕМЫ")
    print("=" * 70)

    # 1. Подключение к vectorstore
    if vectorstore is None:
        vectorstore = get_qdrant_client()
        if vectorstore is None:
            return {}

    info = vectorstore.get_collection_info()
    print(f"\nКоллекция: {info}")

    # 2. Загрузка тестовых постов
    if test_posts is None:
        test_posts = load_test_posts()
        if not test_posts:
            print("Не удалось загрузить тестовые посты из файла.")
            print("Попытка получить документы из Qdrant...")

            # Альтернатива: получаем документы напрямую из Qdrant
            try:
                scroll_result = vectorstore.client.scroll(
                    collection_name=vectorstore.collection_name,
                    limit=num_test_cases * 2,
                    with_payload=True,
                    with_vectors=False,
                )
                points = (
                    scroll_result[0]
                    if isinstance(scroll_result, tuple)
                    else scroll_result
                )
                test_posts = [
                    {
                        "content": p.payload.get("content", "") if p.payload else "",
                        "metadata": {
                            k: v
                            for k, v in (p.payload.items() if p.payload else {})
                            if k != "content"
                        },
                    }
                    for p in points
                ]
                print(f"Получено {len(test_posts)} документов из Qdrant")
            except Exception as e:
                print(f"Ошибка получения документов из Qdrant: {e}")
                return {}

    # 3. Генерация тест-кейсов с ground truth
    test_cases = generate_test_cases_with_ground_truth(
        vectorstore, test_posts, num_cases=num_test_cases
    )

    if not test_cases:
        print("Не удалось сгенерировать тест-кейсы")
        return {}

    # 4. Инициализация LLM с увеличенными таймаутами и повторными попытками
    llm_generation = ChatMistralAI(
        model=cfg.LLM_MODEL, api_key=cfg.MISTRAL_API_KEY, max_retries=5, timeout=60.0
    )

    judge_model = MistralJudgeModel()

    # 5. Оценка с DeepEval метриками
    results = evaluate_with_deepeval(
        vectorstore, test_cases, llm_generation, judge_model
    )

    # 6. Агрегация результатов
    summary = aggregate_results(results)

    # 7. Вывод отчета
    print_detailed_summary(summary, results)

    # 8. Сохранение отчета
    if save_report:
        save_detailed_report(results, summary)

    return {"summary": summary, "results": results}


def main():
    """Запуск пайплайна оценки."""
    results = run_full_evaluation(num_test_cases=10)
    return results


if __name__ == "__main__":
    main()
