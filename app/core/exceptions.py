from typing import Any, Dict, Optional


class OMRProcessingError(Exception):
    """Base exception for OMR processing errors"""
    def __init__(
        self,
        message: str,
        error_code: str = "PROCESSING_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ImageQualityError(OMRProcessingError):
    """Raised when image quality is insufficient for processing"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="POOR_QUALITY",
            details=details
        )


class TemplateNotFoundError(OMRProcessingError):
    """Raised when OMR sheet template cannot be detected"""
    def __init__(self, message: str = "Could not detect OMR sheet template", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="TEMPLATE_NOT_FOUND",
            details=details
        )


class BubbleDetectionError(OMRProcessingError):
    """Raised when bubble detection fails"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="BUBBLE_DETECTION_ERROR",
            details=details
        )


class InvalidAnswerKeyError(OMRProcessingError):
    """Raised when answer key format is invalid"""
    def __init__(self, message: str = "Answer key format is invalid", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="INVALID_ANSWER_KEY",
            details=details
        )


class ProcessingTimeoutError(OMRProcessingError):
    """Raised when processing exceeds time limit"""
    def __init__(self, message: str = "Processing exceeded time limit", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="PROCESSING_TIMEOUT",
            details=details
        )


class InvalidFileFormatError(OMRProcessingError):
    """Raised when file format is not supported"""
    def __init__(self, message: str = "Unsupported file format", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="INVALID_FORMAT",
            details=details
        )


class FileSizeExceededError(OMRProcessingError):
    """Raised when file size exceeds limit"""
    def __init__(self, message: str = "File size exceeds maximum limit", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="FILE_TOO_LARGE",
            details=details
        )