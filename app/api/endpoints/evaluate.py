import time
import json
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, Request, HTTPException
from fastapi.responses import JSONResponse

from app.core.models import (
    EvaluationResponse, EvaluationResult, ProcessingStatus,
    StudentInfo, QuestionDetail, QualityAssessment, ImageQuality,
    ScoringScheme, ProcessingOptions, ExamMetadata
)
from app.services.image_processor import ImageProcessor
from app.services.omr_detector import OMRDetector
from app.services.scorer import ScoringEngine
from app.services.validator import InputValidator
from app.core.exceptions import OMRProcessingError
from app.utils.logging import logger

router = APIRouter()


@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_omr_sheet(
    request: Request,
    image: UploadFile = File(..., description="OMR sheet image file"),
    answer_key: str = Form(..., description="JSON string of answer key"),
    exam_metadata: str = Form(..., description="JSON string of exam metadata"),
    scoring_scheme: Optional[str] = Form(None, description="JSON string of scoring scheme"),
    options: Optional[str] = Form(None, description="JSON string of processing options")
):
    """
    Process a single OMR sheet and return evaluation results
    
    This endpoint accepts an image file of an OMR answer sheet along with
    the answer key and scoring parameters, then returns detailed evaluation results.
    """
    start_time = time.time()
    request_id = getattr(request.state, "request_id", "unknown")
    
    try:
        # Parse JSON strings from form data
        try:
            answer_key_dict = json.loads(answer_key)
            exam_metadata_dict = json.loads(exam_metadata)
            scoring_scheme_dict = json.loads(scoring_scheme) if scoring_scheme else {}
            options_dict = json.loads(options) if options else {}
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON format: {str(e)}")
        
        # Validate input file
        InputValidator.validate_file(image)
        
        # Validate and normalize answer key
        validated_answer_key = InputValidator.validate_answer_key(answer_key_dict)
        
        # Validate scoring scheme
        validated_scoring = InputValidator.validate_scoring_scheme(scoring_scheme_dict)
        scoring_scheme_obj = ScoringScheme(**validated_scoring)
        
        # Validate processing options
        validated_options = InputValidator.validate_processing_options(options_dict)
        
        # Read image file
        image_data = await image.read()
        
        # Process image
        processor = ImageProcessor()
        processed_image, quality_metrics = processor.process_image(image_data)
        
        # Validate OMR template
        if not processor.validate_omr_template(processed_image):
            raise OMRProcessingError(
                "Could not validate OMR sheet template",
                error_code="TEMPLATE_NOT_FOUND",
                details=quality_metrics
            )
        
        # Extract answer regions
        answer_regions = processor.extract_answer_regions(processed_image)
        
        # Detect answers
        detector = OMRDetector()
        detection_results = detector.detect_all_answers(answer_regions)
        
        # Detect student ID (optional)
        student_id = detector.detect_student_id(processed_image)
        
        # Validate detection results
        validation_metrics = detector.validate_detection_results(detection_results)
        
        # Map answers to answer key
        question_details_raw = detector.apply_answer_key_mapping(
            detection_results, validated_answer_key
        )
        
        # Score the results
        scorer = ScoringEngine(scoring_scheme_obj)
        scoring_result = scorer.calculate_score(question_details_raw, scoring_scheme_obj)
        
        # Generate analytics (optional)
        analytics = scorer.generate_analytics(question_details_raw) if validated_options.get("return_debug_info") else None
        
        # Convert question details to model format
        question_details = [
            QuestionDetail(
                question_number=detail["question_number"],
                student_answer=detail["student_answer"],
                correct_answer=detail["correct_answer"],
                is_correct=detail["is_correct"],
                points_awarded=detail["points_awarded"],
                confidence=detail["confidence"],
                is_multiple_marked=detail["is_multiple_marked"]
            )
            for detail in question_details_raw
        ]
        
        # Create quality assessment
        quality_assessment = QualityAssessment(
            image_quality=ImageQuality(quality_metrics["image_quality"]),
            skew_angle=quality_metrics["skew_angle"],
            resolution="adequate" if quality_metrics["processed_dimensions"][0] > 800 else "low",
            brightness_level=quality_metrics["brightness_level"],
            contrast_level=quality_metrics["contrast_level"],
            warnings=quality_metrics.get("warnings", []),
            processing_notes=[]
        )
        
        # Add processing notes if debug info requested
        if validated_options.get("return_debug_info"):
            quality_assessment.processing_notes = [
                f"Original dimensions: {quality_metrics['original_dimensions']}",
                f"Processed dimensions: {quality_metrics['processed_dimensions']}",
                f"Perspective corrected: {quality_metrics.get('perspective_corrected', False)}",
                f"Skew corrected: {quality_metrics.get('skew_corrected', False)}",
                f"Reference marks found: {quality_metrics.get('reference_marks_found', 0)}",
                f"Detection rate: {validation_metrics['detection_rate']:.1f}%",
                f"Average confidence: {validation_metrics['average_confidence']:.3f}"
            ]
        
        # Create student info
        student_info = StudentInfo(
            student_id=student_id,
            exam_id=exam_metadata_dict.get("exam_id", ""),
            exam_date=exam_metadata_dict.get("exam_date")
        )
        
        # Create evaluation result
        evaluation_result = EvaluationResult(
            student_info=student_info,
            scoring=scoring_result,
            question_details=question_details,
            quality_assessment=quality_assessment
        )
        
        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # Create response
        response = EvaluationResponse(
            request_id=request_id,
            status=ProcessingStatus.SUCCESS,
            processing_time_ms=processing_time_ms,
            results=evaluation_result
        )
        
        # Add analytics to response if requested
        if analytics and validated_options.get("return_debug_info"):
            response_dict = response.dict()
            response_dict["analytics"] = analytics
            return JSONResponse(content=response_dict)
        
        logger.info(f"Evaluation completed successfully for request {request_id}")
        return response
        
    except OMRProcessingError as e:
        logger.error(f"OMR processing error: {e.message}")
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        return EvaluationResponse(
            request_id=request_id,
            status=ProcessingStatus.ERROR,
            processing_time_ms=processing_time_ms,
            error={
                "code": e.error_code,
                "message": e.message,
                "details": e.details
            }
        )
        
    except Exception as e:
        logger.error(f"Unexpected error in evaluation: {str(e)}", exc_info=True)
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        return EvaluationResponse(
            request_id=request_id,
            status=ProcessingStatus.ERROR,
            processing_time_ms=processing_time_ms,
            error={
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred during evaluation",
                "details": {"error": str(e)}
            }
        )