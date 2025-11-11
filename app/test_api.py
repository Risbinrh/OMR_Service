"""
Test script for OMR Microservice API
Demonstrates all endpoints with real images
"""

import requests
import json
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"


def test_health():
    """Test health check endpoint"""
    print("\n" + "="*70)
    print("TEST 1: HEALTH CHECK")
    print("="*70)

    response = requests.get(f"{BASE_URL}/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    return response.status_code == 200


def test_process_omr():
    """Test OMR processing endpoint"""
    print("\n" + "="*70)
    print("TEST 2: PROCESS OMR SHEET")
    print("="*70)

    image_path = Path("../filled-sheet-1.jpeg")

    if not image_path.exists():
        print(f"ERROR: Test image not found: {image_path}")
        return None

    with open(image_path, "rb") as f:
        files = {"file": f}
        data = {"save_debug": True}
        response = requests.post(f"{BASE_URL}/api/v1/process", files=files, data=data)

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"\nProcessing Result:")
        print(f"  Image: {result['image_filename']}")
        print(f"  Total Questions: {result['total_questions']}")
        print(f"  Answered: {result['answered']}")
        print(f"  Unanswered: {result['unanswered']}")
        print(f"  Detection Count: {result['detection_count']}")
        print(f"\n  First 10 Answers:")
        for i in range(1, min(11, len(result['answers']) + 1)):
            if i in result['answers']:
                print(f"    Q{i}: {result['answers'][str(i)]}")

        return result
    else:
        print(f"ERROR: {response.text}")
        return None


def test_create_answer_key():
    """Test creating answer key"""
    print("\n" + "="*70)
    print("TEST 3: CREATE ANSWER KEY")
    print("="*70)

    # Create a sample answer key (first 100 questions)
    answer_key_data = {
        "name": "Sample Test Answer Key",
        "answers": {str(i): ["A", "B", "C", "D"][i % 4] for i in range(1, 101)},
        "metadata": {
            "exam_date": "2024-01-15",
            "subject": "General Test",
            "total_marks": 100
        }
    }

    response = requests.post(f"{BASE_URL}/api/v1/answer-keys", json=answer_key_data)

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"\nAnswer Key Created:")
        print(f"  ID: {result['id']}")
        print(f"  Name: {result['name']}")
        print(f"  Total Questions: {result['total_questions']}")
        print(f"  Created At: {result['created_at']}")

        return result['id']
    else:
        print(f"ERROR: {response.text}")
        return None


def test_list_answer_keys():
    """Test listing answer keys"""
    print("\n" + "="*70)
    print("TEST 4: LIST ANSWER KEYS")
    print("="*70)

    response = requests.get(f"{BASE_URL}/api/v1/answer-keys")

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"\nFound {len(result)} answer key(s):")
        for key in result:
            print(f"  - ID: {key['id']}, Name: {key['name']}, Questions: {key['total_questions']}")

        return result
    else:
        print(f"ERROR: {response.text}")
        return None


def test_grade_omr(answer_key_id):
    """Test grading OMR sheet"""
    print("\n" + "="*70)
    print("TEST 5: GRADE OMR SHEET")
    print("="*70)

    image_path = Path("../filled-sheet-1.jpeg")

    if not image_path.exists():
        print(f"ERROR: Test image not found: {image_path}")
        return None

    with open(image_path, "rb") as f:
        files = {"file": f}
        data = {
            "answer_key_id": answer_key_id,
            "correct_marks": 1.0,
            "wrong_marks": -0.25,  # Negative marking
            "unanswered_marks": 0.0,
        }
        response = requests.post(f"{BASE_URL}/api/v1/grade", files=files, data=data)

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"\nGrading Result:")
        print(f"  Image: {result['image_filename']}")
        print(f"  Answer Key: {result['answer_key_name']}")
        print(f"  Total Questions: {result['total_questions']}")
        print(f"  Answered: {result['answered']}")
        print(f"  Correct: {result['correct']}")
        print(f"  Wrong: {result['wrong']}")
        print(f"  Unanswered: {result['unanswered']}")
        print(f"  Score: {result['score']}/{result['max_score']}")
        print(f"  Percentage: {result['percentage']}%")
        print(f"\n  Grading Rules:")
        print(f"    Correct: +{result['grading_rules']['correct_marks']}")
        print(f"    Wrong: {result['grading_rules']['wrong_marks']}")
        print(f"    Unanswered: {result['grading_rules']['unanswered_marks']}")

        return result
    else:
        print(f"ERROR: {response.text}")
        return None


def test_batch_process():
    """Test batch processing"""
    print("\n" + "="*70)
    print("TEST 6: BATCH PROCESSING")
    print("="*70)

    images = [
        "../filled-sheet-1.jpeg",
        "../fully-filled-sheet.jpeg",
    ]

    files = []
    for img_path in images:
        if Path(img_path).exists():
            files.append(("files", open(img_path, "rb")))

    if not files:
        print("ERROR: No test images found")
        return None

    response = requests.post(f"{BASE_URL}/api/v1/batch-process", files=files)

    # Close files
    for _, f in files:
        f.close()

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"\nBatch Processing Result:")
        print(f"  Total: {result['total']}")
        print(f"  Successful: {result['successful']}")
        print(f"  Failed: {result['failed']}")

        return result
    else:
        print(f"ERROR: {response.text}")
        return None


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("OMR MICROSERVICE API TESTING")
    print("="*70)
    print(f"\nBase URL: {BASE_URL}")
    print(f"API Docs: {BASE_URL}/docs")

    try:
        # Test 1: Health check
        if not test_health():
            print("\nERROR: Health check failed. Is the server running?")
            return

        # Test 2: Process OMR
        process_result = test_process_omr()

        # Test 3: Create answer key
        answer_key_id = test_create_answer_key()

        # Test 4: List answer keys
        test_list_answer_keys()

        # Test 5: Grade OMR (if answer key created)
        if answer_key_id:
            test_grade_omr(answer_key_id)

        # Test 6: Batch processing
        test_batch_process()

        print("\n" + "="*70)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("="*70)
        print(f"\nAPI Documentation: {BASE_URL}/docs")
        print(f"ReDoc: {BASE_URL}/redoc")

    except requests.exceptions.ConnectionError:
        print("\nERROR: Could not connect to server. Is it running on http://127.0.0.1:8000?")
    except Exception as e:
        print(f"\nERROR: {e}")


if __name__ == "__main__":
    main()
