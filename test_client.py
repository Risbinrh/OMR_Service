#!/usr/bin/env python3
"""
Test client for the OMR Evaluation Microservice.
This script demonstrates how to use the API to process OMR sheets.
"""

import requests
import json
import sys
import os
from pathlib import Path


class OMRClient:
    """Client for interacting with the OMR Evaluation Service"""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def check_health(self):
        """Check if the service is healthy"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Health check failed: {e}")
            return None
    
    def evaluate_sheet(self, image_path, answer_key, exam_metadata, 
                      scoring_scheme=None, options=None, use_advanced=True):
        """
        Evaluate an OMR sheet
        
        Args:
            image_path: Path to the OMR sheet image
            answer_key: Dictionary of correct answers
            exam_metadata: Exam information
            scoring_scheme: Optional scoring scheme
            options: Optional processing options
            use_advanced: Use advanced processing (default: True)
        
        Returns:
            Evaluation results or None if failed
        """
        
        # Choose endpoint based on advanced flag
        if use_advanced:
            url = f"{self.base_url}/api/v1/evaluate-with-fallback"
        else:
            url = f"{self.base_url}/api/v1/evaluate"
        
        # Prepare form data
        data = {
            'answer_key': json.dumps(answer_key),
            'exam_metadata': json.dumps(exam_metadata)
        }
        
        if scoring_scheme:
            data['scoring_scheme'] = json.dumps(scoring_scheme)
        if options:
            data['options'] = json.dumps(options)
        
        # Prepare file
        with open(image_path, 'rb') as f:
            files = {'image': (os.path.basename(image_path), f, 'image/png')}
            
            try:
                response = self.session.post(url, data=data, files=files)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                print(f"Evaluation failed: {e}")
                if hasattr(e, 'response') and e.response is not None:
                    print(f"Response: {e.response.text}")
                return None
    
    def print_results(self, results):
        """Pretty print evaluation results"""
        if not results:
            print("No results to display")
            return
        
        print("\n" + "="*60)
        print("OMR EVALUATION RESULTS")
        print("="*60)
        
        if results['status'] == 'success':
            eval_results = results['results']
            
            # Student Information
            student_info = eval_results['student_info']
            print(f"\nStudent ID: {student_info.get('student_id', 'Not detected')}")
            print(f"Exam ID: {student_info['exam_id']}")
            if student_info.get('exam_date'):
                print(f"Exam Date: {student_info['exam_date']}")
            
            # Scoring Summary
            scoring = eval_results['scoring']
            print(f"\n{'='*30}")
            print("SCORING SUMMARY")
            print(f"{'='*30}")
            print(f"Total Score: {scoring['total_score']}/{scoring['max_possible_score']}")
            print(f"Percentage: {scoring['percentage']:.1f}%")
            print(f"Correct Answers: {scoring['correct_answers']}")
            print(f"Incorrect Answers: {scoring['incorrect_answers']}")
            print(f"Unanswered: {scoring['unanswered']}")
            if scoring['invalid_marks'] > 0:
                print(f"Invalid Marks: {scoring['invalid_marks']}")
            
            # Quality Assessment
            quality = eval_results['quality_assessment']
            print(f"\n{'='*30}")
            print("QUALITY ASSESSMENT")
            print(f"{'='*30}")
            print(f"Image Quality: {quality['image_quality']}")
            print(f"Skew Angle: {quality['skew_angle']:.2f}°")
            print(f"Resolution: {quality['resolution']}")
            print(f"Brightness: {quality['brightness_level']}")
            print(f"Contrast: {quality['contrast_level']}")
            
            if quality['warnings']:
                print("\nWarnings:")
                for warning in quality['warnings']:
                    print(f"  - {warning}")
            
            # Processing Information
            print(f"\n{'='*30}")
            print("PROCESSING INFORMATION")
            print(f"{'='*30}")
            print(f"Request ID: {results['request_id']}")
            print(f"Processing Time: {results['processing_time_ms']}ms")
            
        else:
            # Error occurred
            error = results.get('error', {})
            print(f"\nERROR: {error.get('message', 'Unknown error')}")
            print(f"Error Code: {error.get('code', 'UNKNOWN')}")
            if error.get('details'):
                print("Details:")
                for key, value in error['details'].items():
                    print(f"  {key}: {value}")


def main():
    """Main function to demonstrate OMR service usage"""
    
    # Initialize client
    client = OMRClient()
    
    # Check service health
    print("Checking service health...")
    health = client.check_health()
    if health:
        print(f"Service is {health['status']} (v{health['version']})")
    else:
        print("Service is not available. Please ensure it's running.")
        sys.exit(1)
    
    # Generate sample answer key (for testing)
    answer_key = {}
    for i in range(1, 101):
        # Create a pattern: A, B, C, D, A, B, C, D...
        answer_key[str(i)] = ['A', 'B', 'C', 'D'][(i-1) % 4]
    
    # Exam metadata
    exam_metadata = {
        "exam_id": "TEST001",
        "subject": "Physics",
        "exam_date": "2025-01-15",
        "total_questions": 100
    }
    
    # Scoring scheme
    scoring_scheme = {
        "correct": 4,
        "incorrect": -1,
        "unanswered": 0
    }
    
    # Processing options
    options = {
        "confidence_threshold": 0.8,
        "strict_mode": True,
        "return_debug_info": False
    }
    
    # Check if sample OMR sheet exists
    sample_path = "sample_omr_sheet.png"
    if not os.path.exists(sample_path):
        print(f"\nSample OMR sheet not found at {sample_path}")
        print("Please run 'python generate_sample_omr.py' first to create sample sheets.")
        sys.exit(1)
    
    # Evaluate the sample sheet
    print(f"\nEvaluating OMR sheet: {sample_path}")
    results = client.evaluate_sheet(
        sample_path,
        answer_key,
        exam_metadata,
        scoring_scheme,
        options
    )
    
    # Display results
    client.print_results(results)
    
    # If there's an answer key file, load and use it
    answer_key_path = sample_path.replace('.png', '_answer_key.json')
    if os.path.exists(answer_key_path):
        print(f"\n{'='*60}")
        print("EVALUATION WITH ACTUAL ANSWER KEY")
        print("="*60)
        
        with open(answer_key_path, 'r') as f:
            actual_answer_key = json.load(f)
        
        print(f"Using actual answer key from: {answer_key_path}")
        results = client.evaluate_sheet(
            sample_path,
            actual_answer_key,
            exam_metadata,
            scoring_scheme,
            options
        )
        
        client.print_results(results)


if __name__ == "__main__":
    main()