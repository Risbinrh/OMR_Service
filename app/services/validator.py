import os
from typing import Any, Dict
from fastapi import UploadFile
from app.core.exceptions import InvalidFileFormatError, FileSizeExceededError
from app.core.config import get_settings
from app.utils.logging import logger

settings = get_settings()


class InputValidator:
    """Validates input files and parameters"""
    
    @staticmethod
    def validate_file(file: UploadFile) -> None:
        """
        Validate uploaded file
        
        Args:
            file: Uploaded file object
            
        Raises:
            InvalidFileFormatError: If file format is not supported
            FileSizeExceededError: If file size exceeds limit
        """
        # Check file extension
        if file.filename:
            _, ext = os.path.splitext(file.filename)
            if ext.lower() not in settings.allowed_extensions:
                raise InvalidFileFormatError(
                    f"File format {ext} not supported. Allowed formats: {settings.allowed_extensions}",
                    details={"filename": file.filename, "extension": ext}
                )
        
        # Check file size
        file.file.seek(0, os.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)  # Reset file pointer
        
        if file_size > settings.max_file_size:
            raise FileSizeExceededError(
                f"File size {file_size / 1024 / 1024:.2f}MB exceeds maximum allowed size "
                f"{settings.max_file_size / 1024 / 1024:.2f}MB",
                details={
                    "file_size": file_size,
                    "max_size": settings.max_file_size,
                    "filename": file.filename
                }
            )
        
        logger.info(f"File validated: {file.filename} ({file_size / 1024:.2f}KB)")
    
    @staticmethod
    def validate_answer_key(answer_key: Dict[str, str]) -> Dict[str, str]:
        """
        Validate and normalize answer key
        
        Args:
            answer_key: Dictionary mapping question numbers to answers
            
        Returns:
            Normalized answer key
            
        Raises:
            ValueError: If answer key is invalid
        """
        if not answer_key:
            raise ValueError("Answer key cannot be empty")
        
        normalized_key = {}
        
        for question, answer in answer_key.items():
            # Normalize question number
            try:
                q_num = int(question)
                if q_num < 1 or q_num > 300:
                    raise ValueError(f"Question number {q_num} out of valid range (1-300)")
            except ValueError as e:
                if "invalid literal" in str(e):
                    raise ValueError(f"Invalid question number format: {question}")
                raise
            
            # Normalize answer (convert to uppercase)
            normalized_answer = answer.upper().strip()
            
            if normalized_answer not in ['A', 'B', 'C', 'D', 'E']:
                raise ValueError(
                    f"Invalid answer '{answer}' for question {q_num}. "
                    "Valid options are: A, B, C, D, E"
                )
            
            normalized_key[str(q_num)] = normalized_answer
        
        logger.info(f"Answer key validated and normalized: {len(normalized_key)} questions")
        return normalized_key
    
    @staticmethod
    def validate_scoring_scheme(scoring_scheme: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate scoring scheme parameters
        
        Args:
            scoring_scheme: Scoring scheme dictionary
            
        Returns:
            Validated scoring scheme
            
        Raises:
            ValueError: If scoring scheme is invalid
        """
        # Default values
        defaults = {
            "correct": settings.default_correct_marks,
            "incorrect": settings.default_incorrect_marks,
            "unanswered": settings.default_unanswered_marks
        }
        
        validated_scheme = defaults.copy()
        
        if scoring_scheme:
            for key in ["correct", "incorrect", "unanswered"]:
                if key in scoring_scheme:
                    value = scoring_scheme[key]
                    
                    # Validate type
                    if not isinstance(value, (int, float)):
                        raise ValueError(f"Scoring value for '{key}' must be numeric")
                    
                    # Validate ranges
                    if key == "correct" and value <= 0:
                        raise ValueError("Points for correct answer must be positive")
                    
                    if key == "incorrect" and value > 0:
                        logger.warning("Positive marks for incorrect answer - unusual scoring scheme")
                    
                    validated_scheme[key] = value
        
        logger.info(f"Scoring scheme validated: {validated_scheme}")
        return validated_scheme
    
    @staticmethod
    def validate_processing_options(options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate processing options
        
        Args:
            options: Processing options dictionary
            
        Returns:
            Validated options
            
        Raises:
            ValueError: If options are invalid
        """
        defaults = {
            "confidence_threshold": settings.confidence_threshold,
            "strict_mode": settings.strict_mode,
            "return_debug_info": False,
            "detect_multiple_marks": True,
            "auto_rotate": True
        }
        
        validated_options = defaults.copy()
        
        if options:
            # Validate confidence threshold
            if "confidence_threshold" in options:
                threshold = options["confidence_threshold"]
                if not isinstance(threshold, (int, float)):
                    raise ValueError("Confidence threshold must be numeric")
                if not 0 <= threshold <= 1:
                    raise ValueError("Confidence threshold must be between 0 and 1")
                validated_options["confidence_threshold"] = threshold
            
            # Validate boolean options
            for key in ["strict_mode", "return_debug_info", "detect_multiple_marks", "auto_rotate"]:
                if key in options:
                    if not isinstance(options[key], bool):
                        raise ValueError(f"Option '{key}' must be boolean")
                    validated_options[key] = options[key]
        
        return validated_options