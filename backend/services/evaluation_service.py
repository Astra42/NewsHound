import json
import time
import logging
import re

from deepeval.metrics import FaithfulnessMetric, AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase
from deepeval.models.base_model import DeepEvalBaseLLM

from api.schemas.evaluation import (
    EvaluationResponse,
    EvaluationResult,
    EvaluationMetric,
    QuestionEvaluationRequest,
)
from services.interfaces.llm import ILLMService
from services.retrieval_service import RetrievalService

logger = logging.getLogger(__name__)

class MistralDeepEvalAdapter(DeepEvalBaseLLM):
    """Adapter to make our Mistral wrapper compatible with DeepEval."""
    def __init__(self, llm_service: ILLMService):
        self.llm_service = llm_service

    def load_model(self):
        return self.llm_service

    def generate(self, prompt: str) -> str:
        # DeepEval might call sync generate. We need to bridge it.
        # Since we are already in async context, calling this might be tricky 
        # unless deepeval supports a_generate (which it does, but we must implement it).
        # We'll implement a fallback just in case.
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # This is dangerous if loop is already running.
                # Hopefully deepeval uses a_generate when available.
                return "Error: Sync generate called in async context"
            return loop.run_until_complete(self.llm_service.agenerate(prompt))
        except Exception:
            # Fallback for when loop is not available (e.g. separate thread)
             return asyncio.run(self.llm_service.agenerate(prompt))

    async def a_generate(self, prompt: str) -> str:
        logger.info(f"[DeepEval] Prompt len: {len(prompt)}")
        logger.debug(f"[DeepEval] Prompt content: {prompt[:200]}...")
        
        response = await self.llm_service.agenerate(prompt)
        
        logger.info(f"[DeepEval] Response len: {len(response)}")
        logger.debug(f"[DeepEval] Response content: {response[:200]}...")
        return response

    def get_model_name(self):
        return "Mistral Custom"

class EvaluationService:
    def __init__(
        self,
        llm_service: ILLMService,
        retrieval_service: RetrievalService,
    ):
        self._llm = llm_service
        self._retrieval = retrieval_service
        # Initialize adapter once
        self._eval_model = MistralDeepEvalAdapter(llm_service)

    async def evaluate_questions(self, request: QuestionEvaluationRequest) -> EvaluationResponse:
        start_time = time.time()
        results = []
        total_faithfulness = 0.0
        total_relevance = 0.0
        count = 0
        
        # Helper to get score safely
        async def get_metric_score(metric) -> float:
            try:
                # Use a_measure if available for async execution
                if hasattr(metric, 'a_measure'):
                    await metric.a_measure(test_case)
                else:
                    metric.measure(test_case)
                return float(metric.score)
            except Exception as e:
                logger.error(f"Error calculating metric {metric.__class__.__name__}: {e}")
                return 0.0

        for q_text in request.questions:
            try:
                # 1. RAG Pipeline (Retrieve + Generate)
                search_results = await self._retrieval.aretrieve(query=q_text, k=5)
                context_texts = self._retrieval.get_context_texts(search_results)
                
                answer = ""
                if not context_texts:
                    answer = "Информация не найдена."
                    faithfulness = 1.0 
                    relevance = 1.0    
                else:
                    if hasattr(self._llm, 'agenerate_with_context'):
                        answer = await self._llm.agenerate_with_context(
                            question=q_text,
                            context=context_texts,
                        )
                    else:
                        # Fallback instructions
                        context_block = "\n\n".join(context_texts)
                        prompt = f"Контекст:\n{context_block}\n\nВопрос: {q_text}\n\nОтветь на вопрос, используя контекст."
                        answer = await self._llm.agenerate(prompt)
                    
                    # 2. Evaluate with DeepEval
                    test_case = LLMTestCase(
                        input=q_text,
                        actual_output=answer,
                        retrieval_context=context_texts
                    )
                    
                    # Faithfulness
                    faithfulness_metric = FaithfulnessMetric(
                        threshold=0.5, 
                        include_reason=False,
                        model=self._eval_model
                    )
                    faithfulness = await get_metric_score(faithfulness_metric)

                    # Relevance
                    relevance_metric = AnswerRelevancyMetric(
                        threshold=0.5, 
                        include_reason=False,
                        model=self._eval_model
                    )
                    relevance = await get_metric_score(relevance_metric)

                metrics = EvaluationMetric(
                    faithfulness=faithfulness,
                    answer_relevance=relevance
                )
                
                results.append(EvaluationResult(
                    question=q_text,
                    answer=answer,
                    metrics=metrics,
                    context=context_texts
                ))
                
                total_faithfulness += faithfulness
                total_relevance += relevance
                count += 1
            except Exception as e:
                logger.error(f"Error evaluating question '{q_text}': {e}", exc_info=True)
                continue
                
        processing_time = time.time() - start_time
        avg_faithfulness = total_faithfulness / count if count > 0 else 0.0
        avg_relevance = total_relevance / count if count > 0 else 0.0

        return EvaluationResponse(
            results=results,
            average_faithfulness=avg_faithfulness,
            average_answer_relevance=avg_relevance,
            processing_time=processing_time
        )


