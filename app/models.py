"""
Pydantic Models for API Request/Response
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime


class ProcessResponse(BaseModel):
    """Response model for OMR processing"""
    success: bool
    image_filename: str
    processed_at: str
    total_questions: int
    answered: int
    unanswered: int
    multiple_fills: int
    answers: Dict[int, str]  # Question number -> Answer (A/B/C/D)
    multiple_fills_details: List[Dict[str, Any]] = []
    detection_count: int


class GradingRules(BaseModel):
    """Grading rules configuration"""
    correct_marks: float = Field(1.0, description="Marks for correct answer")
    wrong_marks: float = Field(0.0, description="Marks for wrong answer (use negative for penalty)")
    unanswered_marks: float = Field(0.0, description="Marks for unanswered question")


class DetailedResult(BaseModel):
    """Detailed result for a single question"""
    question: int
    student_answer: Optional[str]
    correct_answer: str
    is_correct: bool
    marks_awarded: float


class GradeResponse(BaseModel):
    """Response model for grading"""
    success: bool
    image_filename: str
    answer_key_id: str
    answer_key_name: str
    graded_at: str
    total_questions: int
    answered: int
    correct: int
    wrong: int
    unanswered: int
    score: float
    max_score: float
    percentage: float
    grading_rules: GradingRules
    detailed_results: List[Dict[str, Any]]


class AnswerKeyCreate(BaseModel):
    """Request model for creating answer key"""
    name: str = Field(..., description="Name/description of the answer key")
    answers: Dict[int, str] = Field(..., description="Question number to answer mapping")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata")


class AnswerKey(BaseModel):
    """Answer key model"""
    id: str
    name: str
    answers: Dict[int, str]
    metadata: Optional[Dict[str, Any]] = None
    created_at: str
    total_questions: int


class GradeRequest(BaseModel):
    """Request model for grading"""
    answer_key_id: str
    grading_rules: Optional[GradingRules] = None
