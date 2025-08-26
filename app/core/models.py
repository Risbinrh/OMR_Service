from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


class ProcessingStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    PROCESSING = "processing"
    PENDING = "pending"


class ImageQuality(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    ADEQUATE = "adequate"
    POOR = "poor"


class ScoringScheme(BaseModel):
    correct: int = Field(default=4, description="Points for correct answer")
    incorrect: int = Field(default=-1, description="Points for incorrect answer")
    unanswered: int = Field(default=0, description="Points for unanswered question")


class ProcessingOptions(BaseModel):
    confidence_threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    strict_mode: bool = Field(default=True, description="Reject ambiguous marks")
    return_debug_info: bool = Field(default=False)
    detect_multiple_marks: bool = Field(default=True)
    auto_rotate: bool = Field(default=True)


class ExamMetadata(BaseModel):
    exam_id: str = Field(..., min_length=1, max_length=100)
    subject: Optional[str] = Field(None, max_length=100)
    exam_date: Optional[str] = None
    total_questions: int = Field(default=100, ge=1, le=300)
    
    @validator('exam_date')
    def validate_date(cls, v):
        if v:
            try:
                datetime.fromisoformat(v)
            except ValueError:
                raise ValueError('Invalid date format. Use ISO format (YYYY-MM-DD)')
        return v


class AnswerKey(BaseModel):
    answers: Dict[str, str] = Field(..., description="Question number to answer mapping")
    
    @validator('answers')
    def validate_answers(cls, v):
        if not v:
            raise ValueError("Answer key cannot be empty")
        for question, answer in v.items():
            if not question.isdigit():
                raise ValueError(f"Question number must be numeric: {question}")
            if answer not in ['A', 'B', 'C', 'D', 'E']:
                raise ValueError(f"Invalid answer option: {answer}. Must be A, B, C, D, or E")
        return v


class EvaluationRequest(BaseModel):
    answer_key: Dict[str, str] = Field(..., description="Answer key mapping")
    exam_metadata: ExamMetadata
    scoring_scheme: Optional[ScoringScheme] = Field(default_factory=ScoringScheme)
    options: Optional[ProcessingOptions] = Field(default_factory=ProcessingOptions)


class StudentInfo(BaseModel):
    student_id: Optional[str] = None
    exam_id: str
    exam_date: Optional[str] = None


class ScoringResult(BaseModel):
    total_score: int
    max_possible_score: int
    percentage: float
    correct_answers: int
    incorrect_answers: int
    unanswered: int
    invalid_marks: int


class QuestionDetail(BaseModel):
    question_number: int
    student_answer: Optional[str]
    correct_answer: str
    is_correct: bool
    points_awarded: int
    confidence: float = Field(..., ge=0.0, le=1.0)
    is_multiple_marked: bool = False


class QualityAssessment(BaseModel):
    image_quality: ImageQuality
    skew_angle: float
    resolution: str
    brightness_level: str
    contrast_level: str
    warnings: List[str] = Field(default_factory=list)
    processing_notes: List[str] = Field(default_factory=list)


class EvaluationResult(BaseModel):
    student_info: StudentInfo
    scoring: ScoringResult
    question_details: List[QuestionDetail]
    quality_assessment: QualityAssessment


class EvaluationResponse(BaseModel):
    request_id: str
    status: ProcessingStatus
    processing_time_ms: int
    results: Optional[EvaluationResult] = None
    error: Optional[Dict[str, Any]] = None


class BatchEvaluationRequest(BaseModel):
    answer_key: Dict[str, str]
    exam_metadata: ExamMetadata
    scoring_scheme: Optional[ScoringScheme] = Field(default_factory=ScoringScheme)
    options: Optional[ProcessingOptions] = Field(default_factory=ProcessingOptions)
    callback_url: Optional[str] = None


class BatchStatus(BaseModel):
    batch_id: str
    status: ProcessingStatus
    total_images: int
    processed: int
    succeeded: int
    failed: int
    start_time: datetime
    end_time: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None


class HealthCheck(BaseModel):
    status: str
    version: str
    uptime: int
    timestamp: datetime


class ErrorResponse(BaseModel):
    request_id: str
    status: ProcessingStatus = ProcessingStatus.ERROR
    error: Dict[str, Any]
    
    class Config:
        json_schema_extra = {
            "example": {
                "request_id": "req_abc123def456",
                "status": "error",
                "error": {
                    "code": "PROCESSING_FAILED",
                    "message": "Unable to detect answer sheet template",
                    "details": {
                        "image_quality": "poor",
                        "suggested_actions": [
                            "Ensure proper lighting",
                            "Check image resolution",
                            "Verify sheet alignment"
                        ]
                    }
                }
            }
        }