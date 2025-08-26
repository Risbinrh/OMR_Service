import cv2
import numpy as np
from typing import Tuple, Dict, Any, Optional
from app.utils import image_utils
from app.core.exceptions import ImageQualityError, TemplateNotFoundError
from app.utils.logging import logger
from app.core.config import get_settings

settings = get_settings()


class ImageProcessor:
    """Handles image preprocessing for OMR sheet detection"""
    
    def __init__(self):
        self.settings = settings
        self.processed_image = None
        self.original_image = None
        self.quality_metrics = {}
    
    def process_image(self, image_data: bytes) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Main processing pipeline for OMR sheet images
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Processed image and quality metrics
        """
        try:
            # Load image
            self.original_image = image_utils.load_image(image_data)
            logger.info(f"Image loaded: {self.original_image.shape}")
            
            # Assess initial quality
            quality, skew_angle, brightness, contrast = image_utils.assess_image_quality(self.original_image)
            self.quality_metrics = {
                "image_quality": quality,
                "skew_angle": skew_angle,
                "brightness_level": brightness,
                "contrast_level": contrast,
                "original_dimensions": self.original_image.shape[:2]
            }
            
            # Check if quality is acceptable
            if quality == "poor" and self.settings.strict_mode:
                raise ImageQualityError(
                    "Image quality too poor for accurate processing",
                    details=self.quality_metrics
                )
            
            # Resize for consistent processing
            image = image_utils.resize_image(self.original_image, width=1000)
            
            # Enhance contrast if needed
            if contrast == "low":
                image = image_utils.enhance_contrast(image)
                logger.info("Applied contrast enhancement")
            
            # Try to detect document corners for perspective correction
            corners = image_utils.find_document_corners(image)
            if corners is not None:
                image = image_utils.four_point_transform(image, corners)
                logger.info("Applied perspective correction")
                self.quality_metrics["perspective_corrected"] = True
            else:
                self.quality_metrics["perspective_corrected"] = False
            
            # Correct skew if significant
            if abs(skew_angle) > 1.0:
                image = image_utils.rotate_image(image, -skew_angle)
                logger.info(f"Corrected skew angle: {skew_angle:.2f} degrees")
                self.quality_metrics["skew_corrected"] = True
            else:
                self.quality_metrics["skew_corrected"] = False
            
            # Convert to grayscale for processing
            gray = image_utils.convert_to_grayscale(image)
            
            # Apply denoising
            denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
            
            # Store processed image
            self.processed_image = denoised
            self.quality_metrics["processed_dimensions"] = denoised.shape
            
            # Detect reference marks
            reference_marks = image_utils.detect_reference_marks(denoised)
            self.quality_metrics["reference_marks_found"] = len(reference_marks)
            
            # Add warnings if necessary
            warnings = []
            if quality == "poor":
                warnings.append("Image quality is poor, results may be less accurate")
            if abs(skew_angle) > 5:
                warnings.append(f"High skew angle detected: {skew_angle:.1f} degrees")
            if not corners:
                warnings.append("Could not detect document boundaries")
            if len(reference_marks) < 4:
                warnings.append(f"Only {len(reference_marks)} reference marks detected (expected 4)")
            
            self.quality_metrics["warnings"] = warnings
            
            return self.processed_image, self.quality_metrics
            
        except Exception as e:
            logger.error(f"Image processing failed: {str(e)}")
            if isinstance(e, (ImageQualityError, TemplateNotFoundError)):
                raise
            raise ImageQualityError(
                f"Failed to process image: {str(e)}",
                details={"error": str(e)}
            )
    
    def extract_answer_regions(self, image: np.ndarray) -> Dict[int, np.ndarray]:
        """
        Extract individual answer regions from the processed image
        
        Args:
            image: Processed OMR sheet image
            
        Returns:
            Dictionary mapping question numbers to answer region images
        """
        h, w = image.shape[:2]
        
        # Define grid parameters (adjust based on standard OMR layout)
        # Assuming 100 questions in 4 columns of 25 questions each
        questions_per_column = 25
        num_columns = 4
        options_per_question = 4
        
        # Define margins and spacing
        top_margin = int(h * 0.15)  # Top 15% for headers
        bottom_margin = int(h * 0.05)  # Bottom 5% margin
        left_margin = int(w * 0.05)  # Left 5% margin
        right_margin = int(w * 0.05)  # Right 5% margin
        
        # Calculate dimensions
        usable_height = h - top_margin - bottom_margin
        usable_width = w - left_margin - right_margin
        
        row_height = usable_height // questions_per_column
        col_width = usable_width // num_columns
        
        answer_regions = {}
        
        for col in range(num_columns):
            for row in range(questions_per_column):
                question_num = col * questions_per_column + row + 1
                
                # Calculate region coordinates
                x = left_margin + col * col_width
                y = top_margin + row * row_height
                
                # Extract region with some padding
                padding = 2
                region = image[
                    max(0, y - padding):min(h, y + row_height + padding),
                    max(0, x - padding):min(w, x + col_width + padding)
                ]
                
                answer_regions[question_num] = region
        
        logger.info(f"Extracted {len(answer_regions)} answer regions")
        return answer_regions
    
    def validate_omr_template(self, image: np.ndarray) -> bool:
        """
        Validate if the image contains a valid OMR sheet template
        
        Args:
            image: Processed image
            
        Returns:
            True if valid OMR template detected
        """
        # Check image dimensions
        h, w = image.shape[:2]
        aspect_ratio = w / h
        
        # Standard OMR sheets are typically portrait oriented
        if not (0.6 <= aspect_ratio <= 0.85):
            logger.warning(f"Unusual aspect ratio: {aspect_ratio:.2f}")
            return False
        
        # Check for presence of bubble patterns
        # Apply threshold to detect dark regions
        _, thresh = cv2.threshold(image, 180, 255, cv2.THRESH_BINARY_INV)
        
        # Find contours
        contours = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = contours[0] if len(contours) == 2 else contours[1]
        
        # Count circular contours (potential bubbles)
        circular_contours = 0
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 50 or area > 500:  # Filter by size
                continue
            
            perimeter = cv2.arcLength(contour, True)
            if perimeter == 0:
                continue
            
            circularity = 4 * np.pi * area / (perimeter * perimeter)
            if circularity > 0.7:  # Reasonably circular
                circular_contours += 1
        
        # Expect at least 100 bubbles (minimum for valid OMR sheet)
        if circular_contours < 100:
            logger.warning(f"Insufficient circular regions detected: {circular_contours}")
            return False
        
        logger.info(f"Template validation passed with {circular_contours} potential bubbles")
        return True
    
    def get_quality_assessment(self) -> Dict[str, Any]:
        """Get comprehensive quality assessment of the processed image"""
        return self.quality_metrics