#!/usr/bin/env python3
"""
Generate a sample OMR sheet for testing the OMR evaluation service.
This creates a simple OMR sheet with filled bubbles that can be used for testing.
"""

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import random


def create_sample_omr_sheet(
    output_path="sample_omr_sheet.png",
    num_questions=100,
    filled_answers=None,
    student_id="12345678"
):
    """
    Generate a sample OMR sheet with filled answers
    
    Args:
        output_path: Path to save the generated OMR sheet
        num_questions: Number of questions (default 100)
        filled_answers: Dictionary of question numbers to answers (A, B, C, D)
        student_id: Student ID to mark on the sheet
    """
    
    # Sheet dimensions (A4 size at 300 DPI)
    width = 2480  # 210mm at 300 DPI
    height = 3508  # 297mm at 300 DPI
    
    # Create white background
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    # Add borders
    border_width = 5
    draw.rectangle(
        [border_width, border_width, width-border_width, height-border_width],
        outline='black',
        width=border_width
    )
    
    # Add header
    header_height = 300
    draw.rectangle([50, 50, width-50, header_height], outline='black', width=2)
    
    # Add title
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
        font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    draw.text((width//2 - 200, 80), "OMR ANSWER SHEET", fill='black', font=font_large)
    draw.text((width//2 - 150, 140), "SAMPLE EXAMINATION", fill='black', font=font_medium)
    draw.text((100, 200), f"Student ID: {student_id}", fill='black', font=font_medium)
    draw.text((100, 240), "Subject: Physics", fill='black', font=font_small)
    draw.text((width - 400, 200), "Exam Code: TEST001", fill='black', font=font_small)
    draw.text((width - 400, 240), "Date: 2025-01-15", fill='black', font=font_small)
    
    # Add corner markers (reference points)
    marker_size = 15
    corners = [
        (100, 350),  # Top-left
        (width - 100, 350),  # Top-right
        (100, height - 100),  # Bottom-left
        (width - 100, height - 100)  # Bottom-right
    ]
    
    for x, y in corners:
        draw.ellipse([x-marker_size, y-marker_size, x+marker_size, y+marker_size], 
                    fill='black')
    
    # Questions area
    start_y = 400
    questions_per_column = 25
    num_columns = 4
    column_width = (width - 200) // num_columns
    
    # Generate random answers if not provided
    if filled_answers is None:
        filled_answers = {}
        for i in range(1, num_questions + 1):
            # Randomly fill 90% of questions
            if random.random() < 0.9:
                filled_answers[i] = random.choice(['A', 'B', 'C', 'D'])
    
    # Draw questions and bubbles
    for col in range(num_columns):
        column_x = 100 + col * column_width
        
        for row in range(questions_per_column):
            question_num = col * questions_per_column + row + 1
            if question_num > num_questions:
                break
            
            y = start_y + row * 110
            
            # Draw question number
            draw.text((column_x, y), f"{question_num:3d}.", fill='black', font=font_small)
            
            # Draw answer bubbles
            options = ['A', 'B', 'C', 'D']
            bubble_radius = 12
            bubble_spacing = 50
            
            for i, option in enumerate(options):
                bubble_x = column_x + 80 + i * bubble_spacing
                bubble_y = y + 15
                
                # Check if this bubble should be filled
                is_filled = filled_answers.get(question_num) == option
                
                if is_filled:
                    # Fill the bubble
                    draw.ellipse(
                        [bubble_x - bubble_radius, bubble_y - bubble_radius,
                         bubble_x + bubble_radius, bubble_y + bubble_radius],
                        fill='black'
                    )
                else:
                    # Draw empty bubble
                    draw.ellipse(
                        [bubble_x - bubble_radius, bubble_y - bubble_radius,
                         bubble_x + bubble_radius, bubble_y + bubble_radius],
                        outline='black',
                        width=2
                    )
                
                # Draw option letter
                draw.text((bubble_x - 5, bubble_y + bubble_radius + 5), 
                         option, fill='black', font=font_small)
    
    # Add instructions at the bottom
    instructions_y = height - 80
    draw.text((100, instructions_y), 
             "Instructions: Fill the bubble completely. Use dark pencil/pen only.",
             fill='black', font=font_small)
    
    # Save the image
    img.save(output_path)
    print(f"Sample OMR sheet saved to: {output_path}")
    
    # Also save the answer key
    answer_key_path = output_path.replace('.png', '_answer_key.json')
    import json
    answer_key = {str(k): v for k, v in filled_answers.items()}
    with open(answer_key_path, 'w') as f:
        json.dump(answer_key, f, indent=2)
    print(f"Answer key saved to: {answer_key_path}")
    
    return output_path, answer_key


def create_test_cases():
    """Create multiple test cases with different scenarios"""
    
    # Test case 1: Perfect sheet with all answers
    filled_answers_1 = {i: random.choice(['A', 'B', 'C', 'D']) for i in range(1, 101)}
    create_sample_omr_sheet(
        "tests/sample_images/perfect_sheet.png",
        filled_answers=filled_answers_1,
        student_id="12345678"
    )
    
    # Test case 2: Sheet with some unanswered questions
    filled_answers_2 = {}
    for i in range(1, 101):
        if random.random() < 0.8:  # 80% answered
            filled_answers_2[i] = random.choice(['A', 'B', 'C', 'D'])
    create_sample_omr_sheet(
        "tests/sample_images/partial_sheet.png",
        filled_answers=filled_answers_2,
        student_id="87654321"
    )
    
    # Test case 3: Mostly A answers (pattern test)
    filled_answers_3 = {i: 'A' if i % 4 == 0 else random.choice(['B', 'C', 'D']) 
                       for i in range(1, 101)}
    create_sample_omr_sheet(
        "tests/sample_images/pattern_sheet.png",
        filled_answers=filled_answers_3,
        student_id="11111111"
    )
    
    print("\nTest cases created successfully!")
    print("You can now test the OMR service with these sample sheets.")


if __name__ == "__main__":
    import os
    
    # Create directory for sample images
    os.makedirs("tests/sample_images", exist_ok=True)
    
    # Generate main sample
    print("Generating sample OMR sheet...")
    create_sample_omr_sheet()
    
    # Generate test cases
    print("\nGenerating test cases...")
    create_test_cases()
    
    print("\nDone! Sample OMR sheets have been generated.")