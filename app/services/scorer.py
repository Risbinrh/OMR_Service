from typing import Dict, List, Any, Optional
from app.core.models import ScoringScheme, ScoringResult, QuestionDetail
from app.utils.logging import logger


class ScoringEngine:
    """Handles scoring logic for OMR evaluation"""
    
    def __init__(self, scoring_scheme: Optional[ScoringScheme] = None):
        self.scoring_scheme = scoring_scheme or ScoringScheme()
        self.results = None
    
    def calculate_score(
        self,
        question_details: List[Dict[str, Any]],
        scoring_scheme: Optional[ScoringScheme] = None
    ) -> ScoringResult:
        """
        Calculate total score based on answers and scoring scheme
        
        Args:
            question_details: List of question details with answers
            scoring_scheme: Optional custom scoring scheme
            
        Returns:
            ScoringResult with complete scoring information
        """
        scheme = scoring_scheme or self.scoring_scheme
        
        total_score = 0
        correct_answers = 0
        incorrect_answers = 0
        unanswered = 0
        invalid_marks = 0
        
        for detail in question_details:
            student_answer = detail.get("student_answer")
            is_correct = detail.get("is_correct", False)
            is_multiple_marked = detail.get("is_multiple_marked", False)
            
            # Calculate points for this question
            points = 0
            
            if is_multiple_marked:
                # Multiple marks typically result in no points
                invalid_marks += 1
                points = 0
            elif student_answer is None:
                # Unanswered question
                unanswered += 1
                points = scheme.unanswered
            elif is_correct:
                # Correct answer
                correct_answers += 1
                points = scheme.correct
            else:
                # Incorrect answer
                incorrect_answers += 1
                points = scheme.incorrect
            
            # Update the detail with points awarded
            detail["points_awarded"] = points
            total_score += points
        
        # Calculate maximum possible score
        total_questions = len(question_details)
        max_possible_score = total_questions * scheme.correct
        
        # Calculate percentage
        percentage = (total_score / max_possible_score * 100) if max_possible_score > 0 else 0
        
        # Ensure non-negative total score
        total_score = max(0, total_score)
        
        result = ScoringResult(
            total_score=total_score,
            max_possible_score=max_possible_score,
            percentage=round(percentage, 2),
            correct_answers=correct_answers,
            incorrect_answers=incorrect_answers,
            unanswered=unanswered,
            invalid_marks=invalid_marks
        )
        
        self.results = result
        
        logger.info(f"Scoring complete: {total_score}/{max_possible_score} "
                   f"({percentage:.1f}%) - C:{correct_answers} I:{incorrect_answers} U:{unanswered}")
        
        return result
    
    def apply_custom_rules(
        self,
        question_details: List[Dict[str, Any]],
        custom_rules: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Apply custom scoring rules (e.g., section-wise scoring, bonus questions)
        
        Args:
            question_details: List of question details
            custom_rules: Custom scoring rules
            
        Returns:
            Updated question details with custom scoring applied
        """
        # Example custom rules implementation
        for detail in question_details:
            question_num = detail["question_number"]
            
            # Apply bonus questions rule
            if "bonus_questions" in custom_rules:
                if question_num in custom_rules["bonus_questions"]:
                    if detail["is_correct"]:
                        # Double points for bonus questions
                        detail["points_awarded"] *= 2
                        detail["is_bonus"] = True
            
            # Apply section-wise scoring
            if "sections" in custom_rules:
                for section in custom_rules["sections"]:
                    start = section.get("start", 1)
                    end = section.get("end", 100)
                    
                    if start <= question_num <= end:
                        section_scheme = section.get("scoring_scheme", {})
                        if detail["student_answer"] is None:
                            detail["points_awarded"] = section_scheme.get("unanswered", 0)
                        elif detail["is_correct"]:
                            detail["points_awarded"] = section_scheme.get("correct", 4)
                        else:
                            detail["points_awarded"] = section_scheme.get("incorrect", -1)
            
            # Apply negative marking threshold
            if "negative_marking_threshold" in custom_rules:
                threshold = custom_rules["negative_marking_threshold"]
                if not detail["is_correct"] and detail["student_answer"]:
                    # Apply negative marking only if attempted questions exceed threshold
                    attempted = sum(1 for d in question_details if d["student_answer"])
                    if attempted < threshold:
                        detail["points_awarded"] = 0  # No negative marking
        
        return question_details
    
    def generate_analytics(
        self,
        question_details: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate detailed analytics from scoring results
        
        Args:
            question_details: List of question details
            
        Returns:
            Analytics dictionary with insights
        """
        total_questions = len(question_details)
        
        # Question-wise analysis
        correct_questions = [d["question_number"] for d in question_details if d["is_correct"]]
        incorrect_questions = [d["question_number"] for d in question_details 
                             if not d["is_correct"] and d["student_answer"]]
        unanswered_questions = [d["question_number"] for d in question_details 
                               if d["student_answer"] is None]
        
        # Confidence analysis
        confidence_scores = [d["confidence"] for d in question_details if d["student_answer"]]
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        
        # Section-wise performance (assuming 25 questions per section)
        section_size = 25
        num_sections = (total_questions + section_size - 1) // section_size
        section_performance = []
        
        for section in range(num_sections):
            start = section * section_size + 1
            end = min((section + 1) * section_size, total_questions)
            
            section_questions = [d for d in question_details 
                                if start <= d["question_number"] <= end]
            section_correct = sum(1 for d in section_questions if d["is_correct"])
            section_total = len(section_questions)
            
            section_performance.append({
                "section": section + 1,
                "questions": f"{start}-{end}",
                "correct": section_correct,
                "total": section_total,
                "percentage": (section_correct / section_total * 100) if section_total > 0 else 0
            })
        
        # Answer distribution
        answer_distribution = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0}
        for detail in question_details:
            if detail["student_answer"]:
                answer_distribution[detail["student_answer"]] = \
                    answer_distribution.get(detail["student_answer"], 0) + 1
        
        analytics = {
            "total_questions": total_questions,
            "attempted_questions": len([d for d in question_details if d["student_answer"]]),
            "accuracy_rate": (len(correct_questions) / total_questions * 100) if total_questions > 0 else 0,
            "average_confidence": round(avg_confidence, 3),
            "section_performance": section_performance,
            "answer_distribution": answer_distribution,
            "question_analysis": {
                "correct": correct_questions,
                "incorrect": incorrect_questions,
                "unanswered": unanswered_questions
            },
            "confidence_analysis": {
                "high_confidence_correct": len([d for d in question_details 
                                               if d["is_correct"] and d.get("confidence", 0) > 0.8]),
                "low_confidence_correct": len([d for d in question_details 
                                              if d["is_correct"] and d.get("confidence", 0) <= 0.8]),
                "high_confidence_incorrect": len([d for d in question_details 
                                                 if not d["is_correct"] and d["student_answer"] 
                                                 and d.get("confidence", 0) > 0.8])
            }
        }
        
        return analytics
    
    def validate_answer_key(self, answer_key: Dict[str, str]) -> bool:
        """
        Validate answer key format and completeness
        
        Args:
            answer_key: Dictionary of answers
            
        Returns:
            True if valid, raises exception otherwise
        """
        if not answer_key:
            raise ValueError("Answer key cannot be empty")
        
        # Check for valid question numbers and answers
        for question, answer in answer_key.items():
            # Validate question number
            try:
                q_num = int(question)
                if q_num < 1 or q_num > 300:  # Assuming max 300 questions
                    raise ValueError(f"Invalid question number: {q_num}")
            except ValueError:
                raise ValueError(f"Question number must be numeric: {question}")
            
            # Validate answer option
            if answer not in ['A', 'B', 'C', 'D', 'E']:
                raise ValueError(f"Invalid answer option: {answer}")
        
        logger.info(f"Answer key validated: {len(answer_key)} questions")
        return True