from typing import List, Optional
from pydantic import BaseModel, Field

class QuestionEvaluationItem(BaseModel):
    question: str = Field(..., description="Вопрос для оценки")

class QuestionEvaluationRequest(BaseModel):
    questions: List[str] = Field(..., description="Список вопросов для оценки")

class EvaluationMetric(BaseModel):
    faithfulness: float = Field(..., description="Соответствие контексту (0.0 - 1.0)")
    answer_relevance: float = Field(..., description="Релевантность ответа вопросу (0.0 - 1.0)")

class EvaluationResult(BaseModel):
    question: str
    answer: str
    metrics: EvaluationMetric
    context: List[str] = Field(default_factory=list, description="Использованный контекст")

class EvaluationResponse(BaseModel):
    results: List[EvaluationResult]
    average_faithfulness: float
    average_answer_relevance: float
    processing_time: float
    results: List[EvaluationResult]
    average_faithfulness: float
    average_answer_relevance: float
    processing_time: float
