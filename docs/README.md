# OMR Detection & Autograding Microservice

REST API microservice for processing mobile photos of OMR sheets and automatic grading.

## Features

- 🚀 RESTful API with FastAPI
- 📸 Process mobile photos of OMR sheets
- ✅ Automatic answer extraction
- 🎯 Autograding with configurable scoring rules
- 📊 Batch processing support
- 🔑 Answer key management
- 📈 Grading statistics
- 🐳 Docker support
- 📚 Auto-generated API documentation

## Quick Start

### Method 1: Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Start server (Windows)
start.bat

# Start server (Linux/Mac)
chmod +x start.sh
./start.sh
```

Server will start at: `http://localhost:8000`

API Documentation: `http://localhost:8000/docs`

### Method 2: Docker

```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop service
docker-compose down
```

## API Endpoints

### Core Endpoints

#### 1. Process OMR Sheet

Extract answers from OMR sheet image.

**Endpoint:** `POST /api/v1/process`

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/process" \
  -F "file=@sheet.jpg" \
  -F "save_debug=true"
```

**Response:**
```json
{
  "success": true,
  "image_filename": "20240115_123045_sheet.jpg",
  "processed_at": "2024-01-15T12:30:45",
  "total_questions": 100,
  "answered": 97,
  "unanswered": 3,
  "multiple_fills": 0,
  "answers": {
    "1": "B",
    "2": "A",
    "3": "D",
    ...
  },
  "detection_count": 400
}
```

#### 2. Create Answer Key

Create a new answer key for grading.

**Endpoint:** `POST /api/v1/answer-keys`

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/answer-keys" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Math Exam 2024",
    "answers": {
      "1": "B",
      "2": "A",
      "3": "D",
      ...
      "100": "C"
    },
    "metadata": {
      "exam_date": "2024-01-15",
      "subject": "Mathematics"
    }
  }'
```

**Response:**
```json
{
  "id": "a1b2c3d4",
  "name": "Math Exam 2024",
  "answers": {...},
  "metadata": {...},
  "created_at": "2024-01-15T12:00:00",
  "total_questions": 100
}
```

#### 3. Grade OMR Sheet

Process and grade OMR sheet against answer key.

**Endpoint:** `POST /api/v1/grade`

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/grade" \
  -F "file=@student_sheet.jpg" \
  -F "answer_key_id=a1b2c3d4" \
  -F "correct_marks=1.0" \
  -F "wrong_marks=-0.25" \
  -F "unanswered_marks=0.0"
```

**Response:**
```json
{
  "success": true,
  "image_filename": "student_sheet.jpg",
  "answer_key_id": "a1b2c3d4",
  "answer_key_name": "Math Exam 2024",
  "graded_at": "2024-01-15T14:30:00",
  "total_questions": 100,
  "answered": 97,
  "correct": 85,
  "wrong": 12,
  "unanswered": 3,
  "score": 82.0,
  "max_score": 100.0,
  "percentage": 82.0,
  "grading_rules": {
    "correct_marks": 1.0,
    "wrong_marks": -0.25,
    "unanswered_marks": 0.0
  },
  "detailed_results": [...]
}
```

#### 4. List Answer Keys

Get all available answer keys.

**Endpoint:** `GET /api/v1/answer-keys`

**Request:**
```bash
curl "http://localhost:8000/api/v1/answer-keys"
```

#### 5. Batch Processing

Process multiple OMR sheets.

**Endpoint:** `POST /api/v1/batch-process`

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/batch-process" \
  -F "files=@sheet1.jpg" \
  -F "files=@sheet2.jpg" \
  -F "files=@sheet3.jpg"
```

#### 6. Batch Grading

Grade multiple sheets against same answer key.

**Endpoint:** `POST /api/v1/batch-grade`

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/batch-grade" \
  -F "files=@student1.jpg" \
  -F "files=@student2.jpg" \
  -F "files=@student3.jpg" \
  -F "answer_key_id=a1b2c3d4" \
  -F "correct_marks=1.0" \
  -F "wrong_marks=-0.25"
```

**Response:**
```json
{
  "total": 3,
  "successful": 3,
  "failed": 0,
  "statistics": {
    "total_graded": 3,
    "average_score": 78.5,
    "average_percentage": 78.5,
    "highest_score": 92.0,
    "lowest_score": 65.0
  },
  "results": [...]
}
```

## Python Client Example

```python
import requests

BASE_URL = "http://localhost:8000"

# 1. Create answer key
answer_key_data = {
    "name": "Science Exam 2024",
    "answers": {str(i): "A" for i in range(1, 101)},  # Example
}
response = requests.post(f"{BASE_URL}/api/v1/answer-keys", json=answer_key_data)
answer_key_id = response.json()["id"]

# 2. Grade a student sheet
with open("student_sheet.jpg", "rb") as f:
    files = {"file": f}
    data = {
        "answer_key_id": answer_key_id,
        "correct_marks": 1.0,
        "wrong_marks": -0.25,
    }
    response = requests.post(f"{BASE_URL}/api/v1/grade", files=files, data=data)

result = response.json()
print(f"Score: {result['score']}/{result['max_score']}")
print(f"Percentage: {result['percentage']}%")
print(f"Correct: {result['correct']}, Wrong: {result['wrong']}")
```

## Grading Rules

The grading system supports flexible scoring:

- **correct_marks**: Marks for each correct answer (default: 1.0)
- **wrong_marks**: Marks for wrong answers (default: 0.0, use negative for penalty)
- **unanswered_marks**: Marks for unanswered questions (default: 0.0)

### Examples

**Standard Grading (1 mark per correct)**
```json
{
  "correct_marks": 1.0,
  "wrong_marks": 0.0,
  "unanswered_marks": 0.0
}
```

**Negative Marking (-0.25 for wrong)**
```json
{
  "correct_marks": 1.0,
  "wrong_marks": -0.25,
  "unanswered_marks": 0.0
}
```

**JEE/NEET Style (4 marks correct, -1 wrong)**
```json
{
  "correct_marks": 4.0,
  "wrong_marks": -1.0,
  "unanswered_marks": 0.0
}
```

## API Documentation

Interactive API documentation is automatically generated:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Architecture

```
┌─────────────────┐
│  Client Request │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   FastAPI App   │
│   (main.py)     │
└────────┬────────┘
         │
         ├──────────────────────┐
         │                      │
         ▼                      ▼
┌──────────────────┐   ┌───────────────┐
│ OMR Pipeline     │   │ Grading       │
│ (Detection &     │   │ Engine        │
│  Extraction)     │   │ (Scoring)     │
└──────────────────┘   └───────────────┘
         │                      │
         └──────────┬───────────┘
                    │
                    ▼
           ┌────────────────┐
           │  Answer Key    │
           │  Storage       │
           └────────────────┘
```

## File Structure

```
microservice/
├── main.py              # FastAPI application
├── models.py            # Pydantic models
├── grading.py           # Grading engine
├── storage.py           # Answer key storage
├── requirements.txt     # Python dependencies
├── Dockerfile           # Docker image
├── docker-compose.yml   # Docker Compose config
├── start.sh            # Linux/Mac startup script
├── start.bat           # Windows startup script
├── README.md           # This file
├── uploads/            # Uploaded images
├── results/            # Processing results
└── answer_keys/        # Answer key storage
```

## Environment Variables

Optional environment variables:

```bash
MODEL_PATH=../epoch20.pt          # Path to YOLO model
UPLOAD_DIR=uploads                # Upload directory
RESULTS_DIR=results               # Results directory
ANSWER_KEYS_DIR=answer_keys       # Answer keys directory
```

## Requirements

- Python 3.8+
- YOLO model (epoch20.pt or best.pt)
- 2GB+ RAM
- CPU or GPU (GPU recommended for batch processing)

## Performance

- **Single Image**: ~5-10 seconds
- **Batch (10 images)**: ~60-90 seconds
- **Concurrent Requests**: Supports multiple simultaneous requests

## Error Handling

The API provides detailed error responses:

```json
{
  "detail": "Corner detection failed: Only 2 corners found"
}
```

Common errors:
- `400 Bad Request`: Invalid input (file format, missing corners, etc.)
- `404 Not Found`: Answer key not found
- `500 Internal Server Error`: Processing failure

## Security Considerations

For production deployment:

1. **Enable authentication** (JWT, API keys)
2. **Configure CORS** properly (restrict origins)
3. **Add rate limiting** (prevent abuse)
4. **Use HTTPS** (secure transmission)
5. **Validate file uploads** (size limits, format validation)
6. **Set up monitoring** (logging, error tracking)

## Deployment

### Production Deployment

1. **Update CORS settings** in `main.py`
2. **Add authentication** middleware
3. **Set up reverse proxy** (Nginx)
4. **Configure SSL/TLS** certificates
5. **Use production WSGI server** (already using uvicorn)
6. **Set up monitoring** and logging

### Cloud Deployment

#### AWS

```bash
# Deploy to AWS EC2 or ECS
docker build -t omr-api .
docker tag omr-api:latest YOUR_ECR_REPO:latest
docker push YOUR_ECR_REPO:latest
```

#### Google Cloud

```bash
# Deploy to Cloud Run
gcloud builds submit --tag gcr.io/PROJECT_ID/omr-api
gcloud run deploy omr-api --image gcr.io/PROJECT_ID/omr-api
```

## License

Internal use - Educational/Research purposes

## Support

For issues and questions, refer to the main OMR pipeline documentation.
