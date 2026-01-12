from fastapi import APIRouter, Depends, HTTPException
from typing import List

from api.dependencies import get_evaluation_service
from api.schemas.evaluation import QuestionEvaluationRequest, EvaluationResponse
from services.evaluation_service import EvaluationService

router = APIRouter(prefix="/evaluation", tags=["Evaluation"])

@router.post("/test_questions", response_model=EvaluationResponse, description="Evaluate retrieval and generation quality on a list of questions")
async def evaluate_questions(
    request: QuestionEvaluationRequest,
    service: EvaluationService = Depends(get_evaluation_service)
):
    """
    Запуск оценки качества RAG (Retrieval-Augmented Generation).
    
    Метрики:
    1. Faithfulness (Соответствие контексту): Насколько ответ основан на найденных документах.
    2. Answer Relevance (Релевантность): Насколько ответ соответствует вопросу.
    """
    try:
        return await service.evaluate_questions(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))