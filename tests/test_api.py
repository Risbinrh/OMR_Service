import pytest
import json
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "uptime" in data


def test_detailed_health_check():
    """Test detailed health check endpoint"""
    response = client.get("/health/detailed")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "system" in data
    assert "cpu" in data["system"]
    assert "memory" in data["system"]


def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert "version" in data
    assert data["status"] == "operational"


def test_evaluate_missing_file():
    """Test evaluation endpoint with missing file"""
    response = client.post(
        "/api/v1/evaluate",
        data={
            "answer_key": json.dumps({"1": "A", "2": "B"}),
            "exam_metadata": json.dumps({"exam_id": "TEST001", "total_questions": 2})
        }
    )
    assert response.status_code == 422  # Validation error


def test_evaluate_invalid_answer_key():
    """Test evaluation endpoint with invalid answer key"""
    # Create a dummy image file
    from io import BytesIO
    dummy_image = BytesIO(b"fake image data")
    
    response = client.post(
        "/api/v1/evaluate",
        files={"image": ("test.jpg", dummy_image, "image/jpeg")},
        data={
            "answer_key": json.dumps({"1": "Z"}),  # Invalid answer option
            "exam_metadata": json.dumps({"exam_id": "TEST001", "total_questions": 1})
        }
    )
    # Should fail with validation error
    assert response.status_code in [400, 422]


def test_evaluate_invalid_json():
    """Test evaluation endpoint with invalid JSON"""
    from io import BytesIO
    dummy_image = BytesIO(b"fake image data")
    
    response = client.post(
        "/api/v1/evaluate",
        files={"image": ("test.jpg", dummy_image, "image/jpeg")},
        data={
            "answer_key": "not a json",  # Invalid JSON
            "exam_metadata": json.dumps({"exam_id": "TEST001"})
        }
    )
    assert response.status_code == 400


def test_evaluate_file_too_large():
    """Test evaluation endpoint with file too large"""
    from io import BytesIO
    # Create a large dummy file (over 10MB)
    large_data = b"x" * (11 * 1024 * 1024)
    large_image = BytesIO(large_data)
    
    response = client.post(
        "/api/v1/evaluate",
        files={"image": ("large.jpg", large_image, "image/jpeg")},
        data={
            "answer_key": json.dumps({"1": "A"}),
            "exam_metadata": json.dumps({"exam_id": "TEST001", "total_questions": 1})
        }
    )
    # Should fail with file size error
    assert response.status_code == 422


def test_evaluate_unsupported_format():
    """Test evaluation endpoint with unsupported file format"""
    from io import BytesIO
    dummy_file = BytesIO(b"fake data")
    
    response = client.post(
        "/api/v1/evaluate",
        files={"image": ("test.txt", dummy_file, "text/plain")},
        data={
            "answer_key": json.dumps({"1": "A"}),
            "exam_metadata": json.dumps({"exam_id": "TEST001", "total_questions": 1})
        }
    )
    # Should fail with format error
    assert response.status_code == 422