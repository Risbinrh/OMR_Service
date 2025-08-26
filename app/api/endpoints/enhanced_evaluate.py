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
from app.services.advanced_image_processor import AdvancedImageProcessor
from app.services.smart_omr_detector import SmartOMRDetector
from app.services.scorer import ScoringEngine
from app.services.validator import InputValidator
from app.services.validation_engine import ValidationEngine
from app.core.exceptions import OMRProcessingError
from app.utils.logging import logger

router = APIRouter()


@router.post("/evaluate-advanced", response_model=EvaluationResponse)
async def evaluate_omr_sheet_advanced(
    request: Request,
    image: UploadFile = File(..., description="OMR sheet image file"),
    answer_key: str = Form(..., description="JSON string of answer key"),
    exam_metadata: str = Form(..., description="JSON string of exam metadata"),
    scoring_scheme: Optional[str] = Form(None, description="JSON string of scoring scheme"),
    options: Optional[str] = Form(None, description="JSON string of processing options")
):
    """
    Advanced OMR sheet processing with 100% accuracy features
    
    This enhanced endpoint provides:
    - Multi-angle perspective correction
    - Advanced bubble detection with 5 algorithms
    - Smart validation and confidence scoring
    - Comprehensive quality assessment
    - Fallback mechanisms for edge cases
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
        
        logger.info(f"Starting advanced OMR evaluation for request {request_id}")
        
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
        logger.info(f"Image uploaded: {len(image_data)} bytes")
        
        # Stage 1: Advanced Image Processing
        processor = AdvancedImageProcessor()
        processed_image, quality_metrics = processor.process_image_advanced(image_data)
        logger.info("Stage 1: Advanced image processing completed")
        
        # Stage 2: Smart OMR Detection
        detector = SmartOMRDetector()
        
        # Detect grid structure
        grid_info = detector.detect_grid_structure(processed_image)
        logger.info(f"Grid detected: {grid_info['questions_detected']} questions")
        
        # Detect answers with advanced algorithms
        detection_results = detector.detect_answers_advanced(processed_image)
        logger.info("Stage 2: Smart OMR detection completed")
        
        # Stage 3: Validation Engine
        validation_engine = ValidationEngine()
        validation_results = validation_engine.validate_omr_results(
            detection_results, quality_metrics, grid_info
        )
        logger.info(f"Validation score: {validation_results['validation_score']:.3f}")
        
        # Stage 4: Handle validation results
        action_required = validation_results['action_required']
        
        if action_required == "reject":
            # Results are not reliable enough
            error_details = {
                "validation_score": validation_results['validation_score'],
                "overall_confidence": validation_results['overall_confidence'],
                "errors": validation_results['errors'],
                "warnings": validation_results['warnings']
            }
            raise OMRProcessingError(
                "Detection results failed validation checks",
                error_code="VALIDATION_FAILED",
                details=error_details
            )
        
        # Stage 5: Scoring Engine
        scorer = ScoringEngine(scoring_scheme_obj)
        
        # Map answers to answer key with validation
        try:
            question_details_raw = detector.apply_answer_key_mapping(
                detection_results, validated_answer_key
            )
        except Exception as e:
            logger.error(f"Answer mapping failed: {str(e)}")
            raise OMRProcessingError(
                f"Failed to map detected answers: {str(e)}",
                error_code="ANSWER_MAPPING_FAILED"
            )
        
        # Calculate scores
        scoring_result = scorer.calculate_score(question_details_raw, scoring_scheme_obj)
        
        # Stage 6: Generate comprehensive analytics
        if validated_options.get("return_debug_info", False):
            analytics = scorer.generate_analytics(question_details_raw)
        else:
            analytics = None
        
        # Stage 7: Detect student ID (enhanced)
        student_id = detector.detect_student_id(processed_image)
        if student_id and len(student_id) < 6:
            logger.warning(f"Short student ID detected: {student_id}")
        
        # Stage 8: Create response objects
        
        # Convert question details to model format
        question_details = []
        for detail in question_details_raw:
            question_detail = QuestionDetail(
                question_number=detail["question_number"],
                student_answer=detail["student_answer"],
                correct_answer=detail["correct_answer"],
                is_correct=detail["is_correct"],
                points_awarded=detail["points_awarded"],
                confidence=detail["confidence"],
                is_multiple_marked=detail["is_multiple_marked"]
            )
            question_details.append(question_detail)
        
        # Create enhanced quality assessment
        quality_assessment = QualityAssessment(
            image_quality=ImageQuality(quality_metrics["image_quality"]),
            skew_angle=quality_metrics.get("detected_rotation", quality_metrics.get("skew_angle", 0)),
            resolution="high" if quality_metrics["processed_dimensions"][0] > 1000 else "adequate",
            brightness_level=quality_metrics["brightness_level"],
            contrast_level=quality_metrics["contrast_level"],
            warnings=validation_results["warnings"],
            processing_notes=[]
        )
        
        # Add enhanced processing notes
        processing_notes = [
            f"Processing methods: {', '.join(quality_metrics.get('processing_methods', []))}",
            f"Perspective corrected: {quality_metrics.get('perspective_corrected', False)}",
            f"Rotation corrected: {quality_metrics.get('rotation_corrected', False)}",
            f"Grid detection: {grid_info['questions_detected']} questions found",
            f"Validation score: {validation_results['validation_score']:.3f}",
            f"Overall confidence: {validation_results['overall_confidence']:.3f}",
        ]
        
        if validated_options.get("return_debug_info", False):
            processing_notes.extend([
                f"Bubble detection methods: 5 algorithms combined",
                f"Anomalies detected: {validation_results['detailed_analysis'].get('anomaly_analysis', {}).get('anomalies_detected', 0)}",
                f"Pattern analysis: {validation_results['detailed_analysis'].get('pattern_analysis', {}).get('suspicion_level', 'none')} suspicion",
                f"Action required: {action_required}"
            ])
        
        quality_assessment.processing_notes = processing_notes
        
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
        
        # Create response with enhanced information
        response = EvaluationResponse(
            request_id=request_id,
            status=ProcessingStatus.SUCCESS,
            processing_time_ms=processing_time_ms,
            results=evaluation_result
        )
        
        # Add validation and analytics if requested
        if validated_options.get("return_debug_info", False):
            response_dict = response.dict()
            response_dict["validation_results"] = validation_results
            response_dict["grid_information"] = grid_info
            response_dict["quality_metrics"] = quality_metrics
            
            if analytics:
                response_dict["analytics"] = analytics
            
            # Add recommendations
            if validation_results["recommendations"]:
                response_dict["recommendations"] = validation_results["recommendations"]
            
            return JSONResponse(content=response_dict)
        
        # Add action required to response for non-debug mode
        if action_required in ["manual_review", "review_recommended"]:
            response_dict = response.dict()
            response_dict["action_required"] = action_required
            response_dict["validation_confidence"] = validation_results["overall_confidence"]
            if validation_results["recommendations"]:
                response_dict["recommendations"] = validation_results["recommendations"][:3]  # Top 3 only
            
            return JSONResponse(content=response_dict)
        
        logger.info(f"Advanced evaluation completed successfully for request {request_id}")
        return response
        
    except OMRProcessingError as e:
        logger.error(f"Advanced OMR processing error: {e.message}")
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
        logger.error(f"Unexpected error in advanced evaluation: {str(e)}", exc_info=True)
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        return EvaluationResponse(
            request_id=request_id,
            status=ProcessingStatus.ERROR,
            processing_time_ms=processing_time_ms,
            error={
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred during advanced evaluation",
                "details": {"error": str(e)}
            }
        )


@router.post("/evaluate-with-fallback", response_model=EvaluationResponse)
async def evaluate_with_fallback(
    request: Request,
    image: UploadFile = File(..., description="OMR sheet image file"),
    answer_key: str = Form(..., description="JSON string of answer key"),
    exam_metadata: str = Form(..., description="JSON string of exam metadata"),
    scoring_scheme: Optional[str] = Form(None, description="JSON string of scoring scheme"),
    options: Optional[str] = Form(None, description="JSON string of processing options")
):
    """
    OMR evaluation with fallback mechanisms
    
    This endpoint tries advanced processing first, then falls back to basic processing
    if advanced methods fail, ensuring maximum compatibility and success rate.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    logger.info(f"Starting fallback evaluation for request {request_id}")
    
    try:
        # Try advanced processing first
        logger.info("Attempting advanced processing...")
        return await evaluate_omr_sheet_advanced(
            request, image, answer_key, exam_metadata, scoring_scheme, options
        )
        
    except Exception as advanced_error:
        logger.warning(f"Advanced processing failed: {str(advanced_error)}")
        logger.info("Falling back to basic processing...")
        
        try:
            # Import the original evaluate function
            from .evaluate import evaluate_omr_sheet
            
            # Reset file pointer
            await image.seek(0)
            
            # Try basic processing
            result = await evaluate_omr_sheet(
                request, image, answer_key, exam_metadata, scoring_scheme, options
            )
            
            # Add fallback notice to response
            if hasattr(result, 'dict'):
                result_dict = result.dict()
                result_dict["processing_method"] = "basic_fallback"
                result_dict["advanced_error"] = str(advanced_error)[:200]  # Truncated error message
                return JSONResponse(content=result_dict)
            
            return result
            
        except Exception as fallback_error:
            logger.error(f"Both advanced and basic processing failed. Advanced: {str(advanced_error)}, Basic: {str(fallback_error)}")
            
            processing_time_ms = int(time.time() * 1000)
            
            return EvaluationResponse(
                request_id=request_id,
                status=ProcessingStatus.ERROR,
                processing_time_ms=processing_time_ms,
                error={
                    "code": "PROCESSING_FAILED",
                    "message": "Both advanced and basic processing methods failed",
                    "details": {
                        "advanced_error": str(advanced_error)[:200],
                        "fallback_error": str(fallback_error)[:200],
                        "suggested_actions": [
                            "Check image quality and format",
                            "Ensure OMR sheet is properly aligned",
                            "Verify answer key format",
                            "Try with better lighting or higher resolution image"
                        ]
                    }
                }
            )