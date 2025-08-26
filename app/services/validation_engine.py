import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from sklearn.ensemble import IsolationForest
from scipy import stats
from app.utils.logging import logger
from app.core.config import get_settings

settings = get_settings()


class ValidationEngine:
    """Advanced validation engine for 100% accurate OMR results"""
    
    def __init__(self):
        self.settings = settings
        self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
        self.validation_rules = self._load_validation_rules()
    
    def _load_validation_rules(self) -> Dict[str, Any]:
        """Load validation rules and thresholds"""
        return {
            "min_confidence_threshold": 0.75,
            "max_same_answer_ratio": 0.85,  # Max 85% same answers
            "min_answer_rate": 0.3,  # At least 30% questions answered
            "max_multiple_mark_ratio": 0.15,  # Max 15% multiple marks
            "suspicious_pattern_threshold": 0.9,  # Pattern suspicion threshold
            "min_spatial_consistency": 0.7,  # Minimum spatial consistency
            "confidence_variance_threshold": 0.3,  # Max confidence variance
        }
    
    def validate_omr_results(
        self, 
        detection_results: Dict[int, Tuple[Optional[str], float, bool]],
        image_quality_metrics: Dict[str, Any],
        grid_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Comprehensive validation of OMR detection results
        
        Returns validation results with confidence score and recommendations
        """
        logger.info("Starting comprehensive OMR validation")
        
        validation_results = {
            "overall_confidence": 0.0,
            "is_valid": False,
            "validation_score": 0.0,
            "warnings": [],
            "errors": [],
            "recommendations": [],
            "detailed_analysis": {},
            "action_required": None
        }
        
        try:
            # 1. Basic statistics validation
            basic_stats = self._validate_basic_statistics(detection_results)
            validation_results["detailed_analysis"]["basic_stats"] = basic_stats
            
            # 2. Confidence analysis
            confidence_analysis = self._analyze_confidence_distribution(detection_results)
            validation_results["detailed_analysis"]["confidence_analysis"] = confidence_analysis
            
            # 3. Pattern analysis
            pattern_analysis = self._analyze_answer_patterns(detection_results)
            validation_results["detailed_analysis"]["pattern_analysis"] = pattern_analysis
            
            # 4. Image quality correlation
            quality_correlation = self._correlate_with_image_quality(detection_results, image_quality_metrics)
            validation_results["detailed_analysis"]["quality_correlation"] = quality_correlation
            
            # 5. Spatial consistency analysis
            spatial_analysis = self._analyze_spatial_consistency(detection_results, grid_info)
            validation_results["detailed_analysis"]["spatial_analysis"] = spatial_analysis
            
            # 6. Anomaly detection
            anomaly_analysis = self._detect_anomalies(detection_results)
            validation_results["detailed_analysis"]["anomaly_analysis"] = anomaly_analysis
            
            # 7. Cross-validation checks
            cross_validation = self._perform_cross_validation(detection_results)
            validation_results["detailed_analysis"]["cross_validation"] = cross_validation
            
            # Calculate overall validation score
            validation_score = self._calculate_overall_validation_score(validation_results["detailed_analysis"])
            validation_results["validation_score"] = validation_score
            
            # Determine overall confidence and validity
            overall_confidence = self._calculate_overall_confidence(validation_results["detailed_analysis"])
            validation_results["overall_confidence"] = overall_confidence
            validation_results["is_valid"] = overall_confidence >= self.validation_rules["min_confidence_threshold"]
            
            # Generate warnings, errors, and recommendations
            validation_results["warnings"] = self._generate_warnings(validation_results["detailed_analysis"])
            validation_results["errors"] = self._generate_errors(validation_results["detailed_analysis"])
            validation_results["recommendations"] = self._generate_recommendations(validation_results["detailed_analysis"])
            
            # Determine required action
            validation_results["action_required"] = self._determine_required_action(validation_results)
            
            logger.info(f"Validation complete: Score={validation_score:.3f}, Confidence={overall_confidence:.3f}")
            
        except Exception as e:
            logger.error(f"Validation failed: {str(e)}")
            validation_results["errors"].append(f"Validation engine error: {str(e)}")
            validation_results["action_required"] = "manual_review"
        
        return validation_results
    
    def _validate_basic_statistics(self, results: Dict) -> Dict[str, Any]:
        """Validate basic statistics of detection results"""
        total_questions = len(results)
        answered = sum(1 for _, (ans, _, _) in results.items() if ans is not None)
        unanswered = total_questions - answered
        multiple_marked = sum(1 for _, (_, _, is_mult) in results.items() if is_mult)
        
        answer_rate = answered / total_questions if total_questions > 0 else 0
        multiple_mark_rate = multiple_marked / total_questions if total_questions > 0 else 0
        
        # Collect all answers for distribution analysis
        answers = [ans for _, (ans, _, _) in results.items() if ans is not None]
        answer_distribution = {opt: answers.count(opt) for opt in ['A', 'B', 'C', 'D', 'E']}
        
        # Calculate distribution uniformity (entropy)
        if answers:
            total_answers = len(answers)
            entropy = -sum((count / total_answers) * np.log2(count / total_answers) 
                          for count in answer_distribution.values() if count > 0)
            max_entropy = np.log2(len([v for v in answer_distribution.values() if v > 0]))
            normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0
        else:
            entropy = 0
            normalized_entropy = 0
        
        return {
            "total_questions": total_questions,
            "answered": answered,
            "unanswered": unanswered,
            "multiple_marked": multiple_marked,
            "answer_rate": answer_rate,
            "multiple_mark_rate": multiple_mark_rate,
            "answer_distribution": answer_distribution,
            "entropy": entropy,
            "normalized_entropy": normalized_entropy,
            "is_answer_rate_valid": answer_rate >= self.validation_rules["min_answer_rate"],
            "is_multiple_mark_rate_valid": multiple_mark_rate <= self.validation_rules["max_multiple_mark_ratio"]
        }
    
    def _analyze_confidence_distribution(self, results: Dict) -> Dict[str, Any]:
        """Analyze confidence score distribution"""
        confidences = [conf for _, (ans, conf, _) in results.items() if ans is not None]
        
        if not confidences:
            return {
                "mean_confidence": 0.0,
                "std_confidence": 0.0,
                "min_confidence": 0.0,
                "max_confidence": 0.0,
                "confidence_variance": 0.0,
                "high_confidence_rate": 0.0,
                "low_confidence_count": 0,
                "is_confidence_distribution_valid": False
            }
        
        confidences = np.array(confidences)
        
        mean_conf = np.mean(confidences)
        std_conf = np.std(confidences)
        min_conf = np.min(confidences)
        max_conf = np.max(confidences)
        conf_variance = np.var(confidences)
        
        high_confidence_count = np.sum(confidences >= 0.8)
        high_confidence_rate = high_confidence_count / len(confidences)
        
        low_confidence_count = np.sum(confidences < 0.6)
        
        is_valid = (
            mean_conf >= self.validation_rules["min_confidence_threshold"] and
            conf_variance <= self.validation_rules["confidence_variance_threshold"] and
            low_confidence_count <= len(confidences) * 0.2  # Max 20% low confidence
        )
        
        return {
            "mean_confidence": mean_conf,
            "std_confidence": std_conf,
            "min_confidence": min_conf,
            "max_confidence": max_conf,
            "confidence_variance": conf_variance,
            "high_confidence_rate": high_confidence_rate,
            "low_confidence_count": low_confidence_count,
            "confidence_histogram": np.histogram(confidences, bins=10)[0].tolist(),
            "is_confidence_distribution_valid": is_valid
        }
    
    def _analyze_answer_patterns(self, results: Dict) -> Dict[str, Any]:
        """Analyze answer patterns for suspicious behavior"""
        answers = [ans for _, (ans, _, _) in results.items() if ans is not None]
        
        if not answers:
            return {"is_pattern_valid": False, "reason": "No answers detected"}
        
        # Calculate answer distribution
        answer_counts = {opt: answers.count(opt) for opt in ['A', 'B', 'C', 'D', 'E']}
        total_answers = len(answers)
        
        # Check for dominant answer pattern
        max_count = max(answer_counts.values()) if answer_counts else 0
        dominant_ratio = max_count / total_answers if total_answers > 0 else 0
        
        # Sequential pattern analysis
        sequences = self._find_sequential_patterns(results)
        
        # Alternating pattern analysis
        alternating_score = self._calculate_alternating_pattern_score(answers)
        
        # Random pattern test (Chi-square test)
        expected_count = total_answers / 4  # Assuming 4 options (A, B, C, D)
        observed_counts = [answer_counts.get(opt, 0) for opt in ['A', 'B', 'C', 'D']]
        
        if total_answers >= 20:  # Need minimum sample size
            chi_square, p_value = stats.chisquare(observed_counts)
        else:
            chi_square, p_value = 0, 1
        
        # Pattern validity check
        is_valid = (
            dominant_ratio <= self.validation_rules["max_same_answer_ratio"] and
            len(sequences["long_sequences"]) <= 3 and  # Max 3 long sequences
            alternating_score < 0.8 and  # Not too alternating
            (p_value > 0.05 or total_answers < 20)  # Not significantly non-random
        )
        
        return {
            "answer_distribution": answer_counts,
            "dominant_ratio": dominant_ratio,
            "dominant_answer": max(answer_counts, key=answer_counts.get) if answer_counts else None,
            "sequential_patterns": sequences,
            "alternating_score": alternating_score,
            "chi_square_stat": chi_square,
            "chi_square_p_value": p_value,
            "randomness_score": min(1.0, p_value * 2),  # Scale to 0-1
            "is_pattern_valid": is_valid,
            "suspicion_level": self._calculate_pattern_suspicion_level(dominant_ratio, sequences, alternating_score)
        }
    
    def _find_sequential_patterns(self, results: Dict) -> Dict[str, Any]:
        """Find sequential answer patterns"""
        sequences = {"long_sequences": [], "repeated_patterns": []}
        
        # Get answers in question order
        ordered_answers = []
        for q_num in sorted(results.keys()):
            ans, _, _ = results[q_num]
            ordered_answers.append(ans)
        
        # Find sequences of same answer
        current_seq = []
        current_answer = None
        
        for answer in ordered_answers:
            if answer == current_answer and answer is not None:
                current_seq.append(answer)
            else:
                if len(current_seq) >= 5:  # Sequence of 5 or more
                    sequences["long_sequences"].append({
                        "answer": current_answer,
                        "length": len(current_seq),
                        "suspicious": len(current_seq) >= 8
                    })
                current_seq = [answer] if answer is not None else []
                current_answer = answer
        
        # Check final sequence
        if len(current_seq) >= 5:
            sequences["long_sequences"].append({
                "answer": current_answer,
                "length": len(current_seq),
                "suspicious": len(current_seq) >= 8
            })
        
        return sequences
    
    def _calculate_alternating_pattern_score(self, answers: List[str]) -> float:
        """Calculate how alternating the answer pattern is"""
        if len(answers) < 4:
            return 0.0
        
        alternations = 0
        for i in range(1, len(answers)):
            if answers[i] != answers[i-1]:
                alternations += 1
        
        max_alternations = len(answers) - 1
        return alternations / max_alternations if max_alternations > 0 else 0.0
    
    def _calculate_pattern_suspicion_level(self, dominant_ratio: float, sequences: Dict, alternating_score: float) -> str:
        """Calculate overall pattern suspicion level"""
        suspicion_score = 0
        
        # High dominance is suspicious
        if dominant_ratio > 0.8:
            suspicion_score += 2
        elif dominant_ratio > 0.7:
            suspicion_score += 1
        
        # Long sequences are suspicious
        long_seq_count = len(sequences["long_sequences"])
        if long_seq_count >= 3:
            suspicion_score += 2
        elif long_seq_count >= 1:
            suspicion_score += 1
        
        # Very high alternation is suspicious
        if alternating_score > 0.9:
            suspicion_score += 1
        
        if suspicion_score >= 3:
            return "high"
        elif suspicion_score >= 2:
            return "medium"
        elif suspicion_score >= 1:
            return "low"
        else:
            return "none"
    
    def _correlate_with_image_quality(self, results: Dict, quality_metrics: Dict) -> Dict[str, Any]:
        """Correlate detection results with image quality"""
        confidences = [conf for _, (ans, conf, _) in results.items() if ans is not None]
        
        if not confidences:
            return {"correlation_valid": False, "reason": "No confidence data"}
        
        mean_confidence = np.mean(confidences)
        
        # Get image quality indicators
        image_quality = quality_metrics.get("image_quality", "unknown")
        skew_angle = abs(quality_metrics.get("skew_angle", 0))
        
        # Expected confidence based on image quality
        quality_confidence_map = {
            "excellent": (0.9, 0.95),
            "good": (0.8, 0.9),
            "adequate": (0.7, 0.85),
            "poor": (0.5, 0.7)
        }
        
        expected_min, expected_max = quality_confidence_map.get(image_quality, (0.5, 0.9))
        
        # Check correlation
        confidence_matches_quality = expected_min <= mean_confidence <= expected_max
        
        # Skew impact analysis
        high_skew_impact = skew_angle > 5 and mean_confidence < 0.7
        
        return {
            "mean_confidence": mean_confidence,
            "image_quality": image_quality,
            "skew_angle": skew_angle,
            "expected_confidence_range": (expected_min, expected_max),
            "confidence_matches_quality": confidence_matches_quality,
            "high_skew_impact": high_skew_impact,
            "correlation_score": 0.9 if confidence_matches_quality and not high_skew_impact else 0.6
        }
    
    def _analyze_spatial_consistency(self, results: Dict, grid_info: Dict) -> Dict[str, Any]:
        """Analyze spatial consistency of detections"""
        # This is a simplified spatial analysis
        # In a full implementation, you would analyze the actual bubble positions
        
        total_bubbles = grid_info.get("total_bubbles", 0)
        questions_detected = grid_info.get("questions_detected", 0)
        
        # Calculate detection consistency
        if total_bubbles > 0:
            expected_questions = total_bubbles // 4  # Assuming 4 options per question
            detection_rate = questions_detected / expected_questions if expected_questions > 0 else 0
        else:
            detection_rate = 0
        
        # Spatial consistency score (placeholder - would need actual spatial analysis)
        spatial_consistency_score = min(1.0, detection_rate * 1.2)
        
        return {
            "total_bubbles": total_bubbles,
            "questions_detected": questions_detected,
            "detection_rate": detection_rate,
            "spatial_consistency_score": spatial_consistency_score,
            "is_spatially_consistent": spatial_consistency_score >= self.validation_rules["min_spatial_consistency"]
        }
    
    def _detect_anomalies(self, results: Dict) -> Dict[str, Any]:
        """Detect anomalies in the detection results"""
        # Prepare data for anomaly detection
        features = []
        for q_num, (ans, conf, is_mult) in results.items():
            if ans is not None:
                # Convert answer to numeric
                ans_numeric = ord(ans) - ord('A') if ans else -1
                features.append([q_num, ans_numeric, conf, int(is_mult)])
        
        if len(features) < 5:  # Need minimum data points
            return {"anomalies_detected": 0, "anomaly_score": 0.0, "anomalous_questions": []}
        
        features = np.array(features)
        
        try:
            # Fit isolation forest
            anomaly_scores = self.anomaly_detector.fit_predict(features)
            anomalies = np.where(anomaly_scores == -1)[0]
            
            anomalous_questions = [int(features[i][0]) for i in anomalies]
            
            return {
                "anomalies_detected": len(anomalies),
                "anomaly_rate": len(anomalies) / len(features),
                "anomalous_questions": anomalous_questions,
                "has_significant_anomalies": len(anomalies) > len(features) * 0.15  # More than 15%
            }
            
        except Exception as e:
            logger.warning(f"Anomaly detection failed: {str(e)}")
            return {"anomalies_detected": 0, "anomaly_score": 0.0, "error": str(e)}
    
    def _perform_cross_validation(self, results: Dict) -> Dict[str, Any]:
        """Perform cross-validation checks"""
        # Check consistency across question ranges
        ranges = [
            (1, 25, "Section 1"),
            (26, 50, "Section 2"),
            (51, 75, "Section 3"),
            (76, 100, "Section 4")
        ]
        
        range_stats = []
        for start, end, section in ranges:
            section_results = {q: results[q] for q in results if start <= q <= end}
            if section_results:
                confidences = [conf for _, (ans, conf, _) in section_results.items() if ans is not None]
                answered_rate = len([ans for _, (ans, _, _) in section_results.items() if ans is not None]) / len(section_results)
                mean_conf = np.mean(confidences) if confidences else 0
                
                range_stats.append({
                    "section": section,
                    "answered_rate": answered_rate,
                    "mean_confidence": mean_conf,
                    "question_count": len(section_results)
                })
        
        # Check for consistency across sections
        if len(range_stats) >= 2:
            conf_variance = np.var([stat["mean_confidence"] for stat in range_stats])
            rate_variance = np.var([stat["answered_rate"] for stat in range_stats])
            
            is_consistent = conf_variance < 0.1 and rate_variance < 0.2
        else:
            is_consistent = True
            conf_variance = 0
            rate_variance = 0
        
        return {
            "section_statistics": range_stats,
            "confidence_variance": conf_variance,
            "answer_rate_variance": rate_variance,
            "is_cross_validation_consistent": is_consistent
        }
    
    def _calculate_overall_validation_score(self, detailed_analysis: Dict) -> float:
        """Calculate overall validation score from all analyses"""
        scores = []
        weights = []
        
        # Basic statistics score
        basic_stats = detailed_analysis.get("basic_stats", {})
        if basic_stats.get("is_answer_rate_valid", False) and basic_stats.get("is_multiple_mark_rate_valid", False):
            scores.append(0.9)
        else:
            scores.append(0.5)
        weights.append(0.2)
        
        # Confidence analysis score
        conf_analysis = detailed_analysis.get("confidence_analysis", {})
        if conf_analysis.get("is_confidence_distribution_valid", False):
            scores.append(conf_analysis.get("mean_confidence", 0.5))
        else:
            scores.append(0.4)
        weights.append(0.3)
        
        # Pattern analysis score
        pattern_analysis = detailed_analysis.get("pattern_analysis", {})
        if pattern_analysis.get("is_pattern_valid", False):
            suspicion = pattern_analysis.get("suspicion_level", "high")
            if suspicion == "none":
                scores.append(0.9)
            elif suspicion == "low":
                scores.append(0.8)
            elif suspicion == "medium":
                scores.append(0.6)
            else:
                scores.append(0.3)
        else:
            scores.append(0.3)
        weights.append(0.2)
        
        # Quality correlation score
        quality_corr = detailed_analysis.get("quality_correlation", {})
        scores.append(quality_corr.get("correlation_score", 0.5))
        weights.append(0.15)
        
        # Spatial consistency score
        spatial = detailed_analysis.get("spatial_analysis", {})
        scores.append(spatial.get("spatial_consistency_score", 0.5))
        weights.append(0.1)
        
        # Anomaly score (inverted - fewer anomalies = better)
        anomaly = detailed_analysis.get("anomaly_analysis", {})
        anomaly_rate = anomaly.get("anomaly_rate", 0.2)
        scores.append(max(0, 1 - anomaly_rate * 2))  # Convert to positive score
        weights.append(0.05)
        
        # Calculate weighted average
        weighted_score = sum(s * w for s, w in zip(scores, weights)) / sum(weights)
        return min(1.0, max(0.0, weighted_score))
    
    def _calculate_overall_confidence(self, detailed_analysis: Dict) -> float:
        """Calculate overall confidence from all analyses"""
        conf_analysis = detailed_analysis.get("confidence_analysis", {})
        mean_confidence = conf_analysis.get("mean_confidence", 0.0)
        
        # Adjust based on other factors
        adjustments = 0
        
        # Pattern analysis adjustment
        pattern_analysis = detailed_analysis.get("pattern_analysis", {})
        suspicion = pattern_analysis.get("suspicion_level", "none")
        if suspicion == "high":
            adjustments -= 0.2
        elif suspicion == "medium":
            adjustments -= 0.1
        
        # Quality correlation adjustment
        quality_corr = detailed_analysis.get("quality_correlation", {})
        if not quality_corr.get("confidence_matches_quality", True):
            adjustments -= 0.1
        
        # Anomaly adjustment
        anomaly = detailed_analysis.get("anomaly_analysis", {})
        if anomaly.get("has_significant_anomalies", False):
            adjustments -= 0.15
        
        final_confidence = max(0.0, min(1.0, mean_confidence + adjustments))
        return final_confidence
    
    def _generate_warnings(self, detailed_analysis: Dict) -> List[str]:
        """Generate warnings based on analysis results"""
        warnings = []
        
        # Basic statistics warnings
        basic_stats = detailed_analysis.get("basic_stats", {})
        if basic_stats.get("answer_rate", 0) < 0.5:
            warnings.append(f"Low answer rate: {basic_stats.get('answer_rate', 0):.1%}")
        
        if basic_stats.get("multiple_mark_rate", 0) > 0.1:
            warnings.append(f"High multiple mark rate: {basic_stats.get('multiple_mark_rate', 0):.1%}")
        
        # Confidence warnings
        conf_analysis = detailed_analysis.get("confidence_analysis", {})
        if conf_analysis.get("low_confidence_count", 0) > 10:
            warnings.append(f"Many low confidence answers: {conf_analysis.get('low_confidence_count', 0)}")
        
        # Pattern warnings
        pattern_analysis = detailed_analysis.get("pattern_analysis", {})
        suspicion = pattern_analysis.get("suspicion_level", "none")
        if suspicion in ["medium", "high"]:
            warnings.append(f"Suspicious answer pattern detected (level: {suspicion})")
        
        # Quality warnings
        quality_corr = detailed_analysis.get("quality_correlation", {})
        if quality_corr.get("high_skew_impact", False):
            warnings.append("High skew angle may have affected detection accuracy")
        
        # Anomaly warnings
        anomaly = detailed_analysis.get("anomaly_analysis", {})
        if anomaly.get("has_significant_anomalies", False):
            warnings.append(f"Significant anomalies detected in {len(anomaly.get('anomalous_questions', []))} questions")
        
        return warnings
    
    def _generate_errors(self, detailed_analysis: Dict) -> List[str]:
        """Generate errors based on analysis results"""
        errors = []
        
        # Critical validation failures
        basic_stats = detailed_analysis.get("basic_stats", {})
        if basic_stats.get("answer_rate", 0) < 0.1:
            errors.append("Critical: Very low answer detection rate - possible processing failure")
        
        conf_analysis = detailed_analysis.get("confidence_analysis", {})
        if conf_analysis.get("mean_confidence", 0) < 0.3:
            errors.append("Critical: Very low mean confidence - results unreliable")
        
        return errors
    
    def _generate_recommendations(self, detailed_analysis: Dict) -> List[str]:
        """Generate recommendations based on analysis results"""
        recommendations = []
        
        # Image quality recommendations
        quality_corr = detailed_analysis.get("quality_correlation", {})
        image_quality = quality_corr.get("image_quality", "unknown")
        
        if image_quality == "poor":
            recommendations.append("Improve image quality: better lighting, higher resolution")
        
        if quality_corr.get("high_skew_impact", False):
            recommendations.append("Ensure proper alignment when scanning OMR sheets")
        
        # Pattern recommendations
        pattern_analysis = detailed_analysis.get("pattern_analysis", {})
        suspicion = pattern_analysis.get("suspicion_level", "none")
        
        if suspicion == "high":
            recommendations.append("Manual review recommended due to suspicious answer patterns")
        
        # Confidence recommendations
        conf_analysis = detailed_analysis.get("confidence_analysis", {})
        if conf_analysis.get("mean_confidence", 0) < 0.7:
            recommendations.append("Consider lowering detection threshold or improving image preprocessing")
        
        return recommendations
    
    def _determine_required_action(self, validation_results: Dict) -> str:
        """Determine what action is required based on validation results"""
        overall_confidence = validation_results.get("overall_confidence", 0)
        errors = validation_results.get("errors", [])
        warnings = validation_results.get("warnings", [])
        
        if errors:
            return "reject"  # Results should be rejected
        elif overall_confidence < 0.5:
            return "manual_review"  # Require manual review
        elif overall_confidence < 0.8 or len(warnings) >= 3:
            return "review_recommended"  # Review recommended but not required
        else:
            return "accept"  # Results can be accepted