"""
Grading Engine for OMR Autograding
"""

from typing import Dict, Optional
from models import GradingRules


class GradingEngine:
    """Engine for grading OMR sheets against answer keys"""

    def grade(
        self,
        student_answers: Dict[int, str],
        answer_key: Dict[int, str],
        rules: GradingRules,
        multiple_fills: Optional[list] = None,
    ) -> Dict:
        """
        Grade student answers against answer key

        Args:
            student_answers: Dictionary of question -> answer
            answer_key: Dictionary of question -> correct answer
            rules: Grading rules (marks for correct/wrong/unanswered)
            multiple_fills: List of question numbers with multiple fills (treated as wrong)

        Returns:
            Dictionary with grading results
        """

        correct_count = 0
        wrong_count = 0
        unanswered_count = 0
        multiple_fills_count = 0
        total_score = 0.0
        detailed_results = []

        # Create set of questions with multiple fills for quick lookup
        multiple_fill_questions = set()
        if multiple_fills:
            multiple_fill_questions = {q["question"] for q in multiple_fills}

        # Iterate through all questions in answer key
        for question_num, correct_answer in answer_key.items():
            student_answer = student_answers.get(question_num)

            # Check if this question has multiple fills
            if question_num in multiple_fill_questions:
                # Multiple fills - always 0 marks
                multiple_fills_count += 1
                wrong_count += 1
                marks_awarded = 0.0
                is_correct = False
                status = "multiple_fills"
            elif student_answer is None:
                # Unanswered
                unanswered_count += 1
                marks_awarded = rules.unanswered_marks
                is_correct = False
                status = "unanswered"
            elif student_answer == correct_answer:
                # Correct
                correct_count += 1
                marks_awarded = rules.correct_marks
                is_correct = True
                status = "correct"
            else:
                # Wrong
                wrong_count += 1
                marks_awarded = rules.wrong_marks
                is_correct = False
                status = "wrong"

            total_score += marks_awarded

            detailed_results.append({
                "question": question_num,
                "student_answer": student_answer,
                "correct_answer": correct_answer,
                "is_correct": is_correct,
                "status": status,
                "marks_awarded": marks_awarded,
            })

        # Calculate maximum possible score
        max_score = len(answer_key) * rules.correct_marks

        # Calculate percentage
        percentage = (total_score / max_score * 100) if max_score > 0 else 0.0

        return {
            "correct": correct_count,
            "wrong": wrong_count,
            "unanswered": unanswered_count,
            "multiple_fills": multiple_fills_count,
            "score": round(total_score, 2),
            "max_score": max_score,
            "percentage": round(percentage, 2),
            "details": detailed_results,
        }

    def calculate_statistics(self, grading_results: list) -> Dict:
        """
        Calculate statistics from multiple grading results

        Args:
            grading_results: List of grading result dictionaries

        Returns:
            Dictionary with statistics
        """

        if not grading_results:
            return {}

        scores = [r["score"] for r in grading_results]
        percentages = [r["percentage"] for r in grading_results]

        return {
            "count": len(grading_results),
            "average_score": round(sum(scores) / len(scores), 2),
            "average_percentage": round(sum(percentages) / len(percentages), 2),
            "highest_score": max(scores),
            "lowest_score": min(scores),
            "median_score": sorted(scores)[len(scores) // 2],
        }
