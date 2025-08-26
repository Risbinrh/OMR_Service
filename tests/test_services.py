import pytest
import numpy as np
from app.services.scorer import ScoringEngine
from app.services.validator import InputValidator
from app.core.models import ScoringScheme


class TestScoringEngine:
    """Test scoring engine functionality"""
    
    def test_basic_scoring(self):
        """Test basic scoring calculation"""
        scorer = ScoringEngine()
        
        question_details = [
            {"question_number": 1, "student_answer": "A", "correct_answer": "A", 
             "is_correct": True, "confidence": 0.9, "is_multiple_marked": False},
            {"question_number": 2, "student_answer": "B", "correct_answer": "C", 
             "is_correct": False, "confidence": 0.8, "is_multiple_marked": False},
            {"question_number": 3, "student_answer": None, "correct_answer": "D", 
             "is_correct": False, "confidence": 0.0, "is_multiple_marked": False},
        ]
        
        result = scorer.calculate_score(question_details)
        
        assert result.correct_answers == 1
        assert result.incorrect_answers == 1
        assert result.unanswered == 1
        assert result.total_score == 3  # 4 - 1 + 0
        assert result.max_possible_score == 12  # 3 * 4
        
    def test_custom_scoring_scheme(self):
        """Test custom scoring scheme"""
        custom_scheme = ScoringScheme(correct=5, incorrect=-2, unanswered=0)
        scorer = ScoringEngine(custom_scheme)
        
        question_details = [
            {"question_number": 1, "student_answer": "A", "correct_answer": "A", 
             "is_correct": True, "confidence": 0.9, "is_multiple_marked": False},
            {"question_number": 2, "student_answer": "B", "correct_answer": "C", 
             "is_correct": False, "confidence": 0.8, "is_multiple_marked": False},
        ]
        
        result = scorer.calculate_score(question_details)
        
        assert result.total_score == 3  # 5 - 2
        assert result.max_possible_score == 10  # 2 * 5
        
    def test_multiple_marked_handling(self):
        """Test handling of multiple marked answers"""
        scorer = ScoringEngine()
        
        question_details = [
            {"question_number": 1, "student_answer": "A", "correct_answer": "A", 
             "is_correct": True, "confidence": 0.9, "is_multiple_marked": True},
        ]
        
        result = scorer.calculate_score(question_details)
        
        assert result.invalid_marks == 1
        assert result.total_score == 0  # Multiple marks get 0 points
        
    def test_analytics_generation(self):
        """Test analytics generation"""
        scorer = ScoringEngine()
        
        question_details = [
            {"question_number": i, "student_answer": "A" if i % 2 == 0 else "B", 
             "correct_answer": "A", "is_correct": i % 2 == 0, 
             "confidence": 0.9, "is_multiple_marked": False, "points_awarded": 4 if i % 2 == 0 else -1}
            for i in range(1, 11)
        ]
        
        analytics = scorer.generate_analytics(question_details)
        
        assert analytics["total_questions"] == 10
        assert analytics["attempted_questions"] == 10
        assert "section_performance" in analytics
        assert "answer_distribution" in analytics


class TestInputValidator:
    """Test input validation functionality"""
    
    def test_validate_answer_key_valid(self):
        """Test validation of valid answer key"""
        answer_key = {"1": "A", "2": "B", "3": "C", "4": "D"}
        validated = InputValidator.validate_answer_key(answer_key)
        
        assert len(validated) == 4
        assert validated["1"] == "A"
        
    def test_validate_answer_key_invalid_option(self):
        """Test validation of answer key with invalid option"""
        answer_key = {"1": "Z"}
        
        with pytest.raises(ValueError, match="Invalid answer"):
            InputValidator.validate_answer_key(answer_key)
            
    def test_validate_answer_key_invalid_question_number(self):
        """Test validation of answer key with invalid question number"""
        answer_key = {"301": "A"}  # Over max limit
        
        with pytest.raises(ValueError, match="out of valid range"):
            InputValidator.validate_answer_key(answer_key)
            
    def test_validate_scoring_scheme_valid(self):
        """Test validation of valid scoring scheme"""
        scheme = {"correct": 5, "incorrect": -2, "unanswered": 0}
        validated = InputValidator.validate_scoring_scheme(scheme)
        
        assert validated["correct"] == 5
        assert validated["incorrect"] == -2
        assert validated["unanswered"] == 0
        
    def test_validate_scoring_scheme_invalid_correct(self):
        """Test validation of scoring scheme with invalid correct value"""
        scheme = {"correct": -1}  # Negative correct marks
        
        with pytest.raises(ValueError, match="must be positive"):
            InputValidator.validate_scoring_scheme(scheme)
            
    def test_validate_processing_options(self):
        """Test validation of processing options"""
        options = {
            "confidence_threshold": 0.7,
            "strict_mode": True,
            "return_debug_info": False
        }
        validated = InputValidator.validate_processing_options(options)
        
        assert validated["confidence_threshold"] == 0.7
        assert validated["strict_mode"] is True
        
    def test_validate_processing_options_invalid_threshold(self):
        """Test validation of processing options with invalid threshold"""
        options = {"confidence_threshold": 1.5}  # Over 1.0
        
        with pytest.raises(ValueError, match="between 0 and 1"):
            InputValidator.validate_processing_options(options)