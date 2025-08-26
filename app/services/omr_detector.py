import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from app.core.exceptions import BubbleDetectionError
from app.utils.logging import logger
from app.core.config import get_settings

settings = get_settings()


class OMRDetector:
    """Handles bubble detection and answer extraction from OMR sheets"""
    
    def __init__(self):
        self.settings = settings
        self.detected_answers = {}
        self.confidence_scores = {}
    
    def detect_bubbles_in_region(
        self, 
        region: np.ndarray, 
        num_options: int = 4
    ) -> Tuple[Optional[str], float, bool]:
        """
        Detect filled bubble in a single question region
        
        Args:
            region: Image region containing one question's answer bubbles
            num_options: Number of options (A, B, C, D)
            
        Returns:
            Tuple of (selected_answer, confidence, is_multiple_marked)
        """
        h, w = region.shape[:2]
        
        # Apply threshold
        _, thresh = cv2.threshold(region, self.settings.bubble_detection_threshold, 255, cv2.THRESH_BINARY_INV)
        
        # Divide region into option sections
        option_width = w // num_options
        options = ['A', 'B', 'C', 'D', 'E'][:num_options]
        
        fill_ratios = []
        detected_options = []
        
        for i, option in enumerate(options):
            # Extract option region
            x_start = i * option_width
            x_end = (i + 1) * option_width
            option_region = thresh[:, x_start:x_end]
            
            # Detect circles using Hough Transform
            circles = cv2.HoughCircles(
                option_region,
                cv2.HOUGH_GRADIENT,
                dp=1.2,
                minDist=20,
                param1=50,
                param2=25,
                minRadius=self.settings.min_circle_radius,
                maxRadius=self.settings.max_circle_radius
            )
            
            if circles is not None:
                circles = np.round(circles[0, :]).astype("int")
                
                # Calculate fill ratio for the most prominent circle
                max_fill_ratio = 0
                for (x, y, r) in circles:
                    # Create mask for circle
                    mask = np.zeros(option_region.shape, dtype=np.uint8)
                    cv2.circle(mask, (x, y), r, 255, -1)
                    
                    # Calculate fill ratio
                    masked = cv2.bitwise_and(option_region, mask)
                    total_pixels = cv2.countNonZero(mask)
                    filled_pixels = cv2.countNonZero(masked)
                    
                    if total_pixels > 0:
                        fill_ratio = filled_pixels / total_pixels
                        max_fill_ratio = max(max_fill_ratio, fill_ratio)
                
                fill_ratios.append(max_fill_ratio)
                
                # Check if bubble is filled
                if max_fill_ratio >= self.settings.min_bubble_fill_ratio:
                    detected_options.append((option, max_fill_ratio))
            else:
                fill_ratios.append(0)
        
        # Determine selected answer
        if not detected_options:
            return None, 0.0, False  # No answer marked
        
        # Check for multiple marks
        is_multiple_marked = len(detected_options) > 1
        
        if is_multiple_marked and self.settings.strict_mode:
            # In strict mode, multiple marks invalidate the answer
            return None, 0.0, True
        
        # Select option with highest fill ratio
        detected_options.sort(key=lambda x: x[1], reverse=True)
        selected_answer, confidence = detected_options[0]
        
        # Adjust confidence based on fill ratio difference
        if len(detected_options) > 1:
            confidence_diff = detected_options[0][1] - detected_options[1][1]
            if confidence_diff < 0.1:  # Very close fill ratios
                confidence *= 0.7  # Reduce confidence
        
        return selected_answer, confidence, is_multiple_marked
    
    def detect_all_answers(
        self, 
        answer_regions: Dict[int, np.ndarray]
    ) -> Dict[int, Tuple[Optional[str], float, bool]]:
        """
        Detect answers for all questions
        
        Args:
            answer_regions: Dictionary mapping question numbers to image regions
            
        Returns:
            Dictionary mapping question numbers to (answer, confidence, is_multiple)
        """
        results = {}
        
        for question_num, region in answer_regions.items():
            try:
                answer, confidence, is_multiple = self.detect_bubbles_in_region(region)
                results[question_num] = (answer, confidence, is_multiple)
                
                if answer:
                    logger.debug(f"Q{question_num}: {answer} (confidence: {confidence:.2f})")
                else:
                    logger.debug(f"Q{question_num}: No answer detected")
                    
            except Exception as e:
                logger.error(f"Error detecting answer for question {question_num}: {str(e)}")
                results[question_num] = (None, 0.0, False)
        
        self.detected_answers = results
        return results
    
    def detect_student_id(self, image: np.ndarray) -> Optional[str]:
        """
        Detect student ID from the OMR sheet
        
        Args:
            image: Processed OMR sheet image
            
        Returns:
            Detected student ID or None
        """
        h, w = image.shape[:2]
        
        # Student ID is typically in the top portion of the sheet
        id_region = image[int(h * 0.05):int(h * 0.12), int(w * 0.6):int(w * 0.95)]
        
        # Apply threshold
        _, thresh = cv2.threshold(id_region, 180, 255, cv2.THRESH_BINARY_INV)
        
        # Detect digit bubbles (10 digits, 0-9)
        id_digits = []
        num_id_positions = 8  # Assuming 8-digit student ID
        
        region_width = id_region.shape[1] // num_id_positions
        
        for pos in range(num_id_positions):
            x_start = pos * region_width
            x_end = (pos + 1) * region_width
            digit_region = thresh[:, x_start:x_end]
            
            # Divide into 10 rows for digits 0-9
            row_height = digit_region.shape[0] // 10
            max_fill_ratio = 0
            selected_digit = None
            
            for digit in range(10):
                y_start = digit * row_height
                y_end = (digit + 1) * row_height
                digit_bubble = digit_region[y_start:y_end, :]
                
                # Calculate fill ratio
                filled_pixels = cv2.countNonZero(digit_bubble)
                total_pixels = digit_bubble.size
                
                if total_pixels > 0:
                    fill_ratio = filled_pixels / total_pixels
                    
                    if fill_ratio > max_fill_ratio and fill_ratio >= self.settings.min_bubble_fill_ratio:
                        max_fill_ratio = fill_ratio
                        selected_digit = str(digit)
            
            if selected_digit:
                id_digits.append(selected_digit)
            else:
                id_digits.append('X')  # Unknown digit
        
        student_id = ''.join(id_digits)
        
        # Validate student ID
        if 'X' in student_id:
            logger.warning(f"Incomplete student ID detected: {student_id}")
            return None
        
        logger.info(f"Detected student ID: {student_id}")
        return student_id
    
    def validate_detection_results(
        self, 
        results: Dict[int, Tuple[Optional[str], float, bool]]
    ) -> Dict[str, Any]:
        """
        Validate and analyze detection results
        
        Args:
            results: Detection results
            
        Returns:
            Validation metrics
        """
        total_questions = len(results)
        answered = sum(1 for _, (ans, _, _) in results.items() if ans is not None)
        unanswered = total_questions - answered
        multiple_marked = sum(1 for _, (_, _, is_mult) in results.items() if is_mult)
        
        # Calculate average confidence for answered questions
        confidences = [conf for _, (ans, conf, _) in results.items() if ans is not None]
        avg_confidence = np.mean(confidences) if confidences else 0.0
        
        # Identify low confidence answers
        low_confidence = [
            q for q, (ans, conf, _) in results.items() 
            if ans is not None and conf < self.settings.confidence_threshold
        ]
        
        validation_metrics = {
            "total_questions": total_questions,
            "answered": answered,
            "unanswered": unanswered,
            "multiple_marked": multiple_marked,
            "average_confidence": avg_confidence,
            "low_confidence_questions": low_confidence,
            "detection_rate": (answered / total_questions) * 100 if total_questions > 0 else 0
        }
        
        logger.info(f"Detection summary: {answered}/{total_questions} answered, "
                   f"avg confidence: {avg_confidence:.2f}")
        
        return validation_metrics
    
    def apply_answer_key_mapping(
        self,
        detected_answers: Dict[int, Tuple[Optional[str], float, bool]],
        answer_key: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """
        Map detected answers against answer key
        
        Args:
            detected_answers: Detected answers with confidence
            answer_key: Correct answers
            
        Returns:
            List of question details with scoring
        """
        question_details = []
        
        for question_num, (student_answer, confidence, is_multiple) in detected_answers.items():
            question_str = str(question_num)
            correct_answer = answer_key.get(question_str, None)
            
            if correct_answer is None:
                logger.warning(f"No answer key entry for question {question_num}")
                continue
            
            is_correct = (student_answer == correct_answer) if student_answer else False
            
            detail = {
                "question_number": question_num,
                "student_answer": student_answer,
                "correct_answer": correct_answer,
                "is_correct": is_correct,
                "confidence": confidence,
                "is_multiple_marked": is_multiple
            }
            
            question_details.append(detail)
        
        return question_details