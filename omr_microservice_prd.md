# OMR Evaluation Microservice - Product Requirements Document

## Executive Summary

The OMR (Optical Mark Recognition) Evaluation Microservice is a self-contained, API-first service designed to process scanned answer sheets and return structured evaluation results. The service accepts image uploads, performs automated bubble detection and scoring, and returns comprehensive results in JSON format.

## Product Overview

### Vision
To provide a reliable, scalable, and accurate automated scoring solution for standardized multiple-choice examinations through a simple API interface.

### Mission
Eliminate manual grading overhead while maintaining high accuracy and providing detailed analytics for educational institutions and examination bodies.

## Business Requirements

### Primary Objectives
- **Accuracy**: Achieve 99.5%+ bubble detection accuracy under optimal conditions
- **Performance**: Process standard OMR sheets within 3 seconds per image
- **Scalability**: Handle 1000+ concurrent requests during peak examination periods
- **Reliability**: Maintain 99.9% uptime with automatic failover capabilities

### Success Metrics
- Processing accuracy rate
- Average response time
- API uptime percentage
- User adoption rate
- Error rate per 1000 requests

## Target Users

### Primary Users
- **Educational Institutions**: Schools, colleges, universities
- **Examination Boards**: Standardized testing organizations
- **Training Centers**: Corporate training and certification bodies

### Secondary Users
- **EdTech Platforms**: Integration partners
- **System Integrators**: Third-party developers

## Functional Requirements

### Core Features

#### 1. Image Processing API
- **Endpoint**: `POST /api/v1/evaluate`
- **Accepts**: Image files (JPEG, PNG, PDF)
- **Max file size**: 10MB
- **Supported formats**: Standard OMR sheets (100 questions, 4 options)

#### 2. Stateless Processing
- **No persistent storage**: Each request contains all necessary data
- **Self-contained**: Answer key provided with each evaluation request
- **No state management**: Service doesn't store or remember previous requests

#### 3. Evaluation Results
- **Format**: Structured JSON response
- **Content**: Scores, individual answers, confidence levels, metadata
- **Real-time**: Synchronous processing and response

#### 4. Batch Processing
- **Endpoint**: `POST /api/v1/batch-evaluate`
- **Functionality**: Process multiple sheets simultaneously
- **Status tracking**: Async processing with status endpoints

### API Specifications

#### Authentication
```
Authorization: Bearer <jwt_token>
Content-Type: multipart/form-data
```

#### Request Format
```json
{
  "image": "<file_upload>",
  "answer_key": {
    "1": "A",
    "2": "B", 
    "3": "C",
    "4": "D",
    ...
    "100": "A"
  },
  "exam_metadata": {
    "exam_id": "GJP2025",
    "subject": "Physics",
    "total_questions": 100
  },
  "scoring_scheme": {
    "correct": 4,
    "incorrect": -1,
    "unanswered": 0
  },
  "options": {
    "confidence_threshold": 0.8,
    "strict_mode": true,
    "return_debug_info": false
  }
}
```

#### Response Format
```json
{
  "request_id": "req_abc123def456",
  "status": "success",
  "processing_time_ms": 2340,
  "results": {
    "student_info": {
      "student_id": "NAY14116",
      "exam_id": "GJP2025",
      "exam_date": "2025-12-12"
    },
    "scoring": {
      "total_score": 376,
      "max_possible_score": 400,
      "percentage": 94.0,
      "correct_answers": 97,
      "incorrect_answers": 2,
      "unanswered": 1,
      "invalid_marks": 0
    },
    "question_details": [
      {
        "question_number": 1,
        "student_answer": "B",
        "correct_answer": "B",
        "is_correct": true,
        "points_awarded": 4,
        "confidence": 0.95
      }
    ],
    "quality_assessment": {
      "image_quality": "good",
      "skew_angle": 1.2,
      "resolution": "adequate",
      "warnings": []
    }
  }
}
```

### Error Handling
```json
{
  "request_id": "req_abc123def456",
  "status": "error",
  "error": {
    "code": "PROCESSING_FAILED",
    "message": "Unable to detect answer sheet template",
    "details": {
      "image_quality": "poor",
      "suggested_actions": [
        "Ensure proper lighting",
        "Check image resolution",
        "Verify sheet alignment"
      ]
    }
  }
}
```

## Technical Requirements

### Architecture

#### Microservice Design
- **Container-based**: Docker deployment
- **Stateless**: No session storage, fully stateless operations
- **Self-contained**: All dependencies bundled
- **API-first**: RESTful interface with OpenAPI specification

#### Technology Stack
```yaml
Runtime: Python 3.11+
Framework: FastAPI
Image Processing: OpenCV, scikit-image
ML Libraries: NumPy, scipy
Caching: Redis (optional, for batch processing status only)
Monitoring: Prometheus + Grafana
Documentation: Swagger/OpenAPI
Storage: None (fully stateless)
```

#### Infrastructure Requirements
```yaml
Compute:
  - CPU: 4+ cores per instance
  - Memory: 4GB+ RAM (reduced due to no persistent storage)
  - Storage: 10GB SSD (logs and temp files only)
  - GPU: Optional (CUDA support for acceleration)

Scaling:
  - Horizontal scaling via container orchestration
  - Load balancer with health checks
  - Auto-scaling based on CPU/memory usage

Dependencies:
  - Redis (optional, only for batch processing status tracking)
  - No persistent database required
  - No object storage required
```

### Performance Requirements

#### Response Times
- **Single image**: < 3 seconds (95th percentile)
- **Batch processing**: < 30 seconds for 10 images
- **API response**: < 100ms for status checks

#### Throughput
- **Concurrent requests**: 100+ simultaneous
- **Peak load**: 1000 requests/minute
- **Batch capacity**: 50 images per batch

#### Availability
- **Uptime**: 99.9% availability
- **Recovery time**: < 5 minutes for service restart
- **Data durability**: 99.999% for submitted images

### Security Requirements

#### Authentication & Authorization
- JWT-based authentication
- Role-based access control (RBAC)
- API key management for service accounts
- Rate limiting per client

#### Data Protection
- TLS 1.3 for all communications
- Image encryption at rest
- PII data anonymization options
- GDPR compliance for data handling

#### Audit & Compliance
- Request/response logging
- Processing audit trails
- Data retention policies
- Security scanning and vulnerability management

## Non-Functional Requirements

### Reliability
- **Error rate**: < 0.1% processing failures
- **Data integrity**: Checksums for all image uploads
- **Graceful degradation**: Partial results when possible

### Maintainability
- **Code coverage**: > 90% test coverage
- **Documentation**: Complete API documentation
- **Monitoring**: Comprehensive metrics and alerting
- **Deployment**: Blue-green deployment strategy

### Usability
- **API design**: RESTful, intuitive endpoints
- **Error messages**: Clear, actionable error descriptions
- **Status feedback**: Real-time processing status
- **Integration**: SDK/client libraries for popular languages

## API Endpoints Specification

### Core Endpoints

#### 1. Health Check
```
GET /health
Response: {"status": "healthy", "version": "1.0.0", "uptime": 3600}
```

#### 2. Process Single Image
```
POST /api/v1/evaluate
Content-Type: multipart/form-data
Parameters:
  - image: file (required)
  - answer_key_id: string (required)
  - scoring_scheme: object (optional)
  - options: object (optional)
```

#### 3. Batch Processing
```
POST /api/v1/batch-evaluate
Content-Type: multipart/form-data
Parameters:
  - images: file[] (required, max 50)
  - answer_key_id: string (required)
  - callback_url: string (optional)
```

#### 4. Check Batch Status
```
GET /api/v1/batch/{batch_id}/status
Response: {"status": "processing", "completed": 30, "total": 50}
```

#### 5. Answer Key Management
```
POST /api/v1/answer-keys
PUT /api/v1/answer-keys/{key_id}
GET /api/v1/answer-keys/{key_id}
DELETE /api/v1/answer-keys/{key_id}
```

#### 6. Processing History
```
GET /api/v1/history
Parameters:
  - limit: integer (default: 50)
  - offset: integer (default: 0)
  - date_from: date (optional)
  - date_to: date (optional)
```

### Administrative Endpoints

#### 1. Metrics
```
GET /metrics
Response: Prometheus-formatted metrics
```

#### 2. System Status
```
GET /admin/status
Response: Detailed system health information
```

## Data Models

### Request Schema
```json
{
  "image": "binary_file_data",
  "answer_key": {
    "1": "A",
    "2": "B",
    "3": "C",
    "4": "D",
    ...
    "100": "A"
  },
  "exam_metadata": {
    "exam_id": "GJP2025",
    "subject": "Physics", 
    "exam_date": "2025-12-12",
    "total_questions": 100
  },
  "scoring_scheme": {
    "correct": 4,
    "incorrect": -1,
    "unanswered": 0
  }
}
```

### Response Schema
```json
{
  "request_id": "req_abc123def456",
  "status": "success",
  "processing_time_ms": 2340,
  "results": {
    "student_info": {
      "student_id": "NAY14116",
      "exam_id": "GJP2025",
      "exam_date": "2025-12-12"
    },
    "scoring": {
      "total_score": 376,
      "max_possible_score": 400,
      "percentage": 94.0,
      "correct_answers": 97,
      "incorrect_answers": 2,
      "unanswered": 1,
      "invalid_marks": 0
    },
    "question_details": [
      {
        "question_number": 1,
        "student_answer": "B",
        "correct_answer": "B",
        "is_correct": true,
        "points_awarded": 4,
        "confidence": 0.95
      }
    ],
    "quality_assessment": {
      "image_quality": "good",
      "skew_angle": 1.2,
      "resolution": "adequate",
      "warnings": []
    }
  }
}
```

## Deployment Strategy

### Container Configuration
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables
```bash
# Optional Redis (only for batch processing)
REDIS_URL=redis://redis:6379/0

# Security
JWT_SECRET=your_jwt_secret

# Performance
MAX_WORKERS=4
PROCESSING_TIMEOUT=30
TEMP_DIR=/tmp/omr_processing

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: omr-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: omr-service
  template:
    metadata:
      labels:
        app: omr-service
    spec:
      containers:
      - name: omr-service
        image: omr-service:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
```

## Testing Strategy

### Test Categories

#### 1. Unit Tests
- Image processing algorithms
- Scoring calculations
- API endpoint handlers
- Data validation logic

#### 2. Integration Tests
- End-to-end API workflows
- Database operations
- External service integrations
- Error handling scenarios

#### 3. Performance Tests
- Load testing with realistic image sizes
- Concurrent request handling
- Memory usage optimization
- Response time benchmarks

#### 4. Accuracy Tests
- Controlled test sets with known answers
- Various image quality conditions
- Edge cases and error scenarios
- Regression testing for model updates

### Test Data Requirements
- Sample OMR sheets (various conditions)
- Ground truth answer sets
- Performance benchmark datasets
- Edge case scenarios

## Monitoring & Observability

### Metrics Collection
```yaml
Business Metrics:
  - processing_accuracy_rate
  - total_sheets_processed
  - average_processing_time
  - error_rate_by_type

Technical Metrics:
  - request_rate
  - response_time_percentiles
  - memory_usage
  - cpu_utilization
  - queue_depth

Custom Metrics:
  - image_quality_distribution
  - confidence_score_distribution
  - answer_pattern_anomalies
```

### Alerting Rules
- Processing time > 5 seconds
- Error rate > 1%
- Queue depth > 100
- Memory usage > 90%
- Disk space < 10% free

### Logging Strategy
- Structured JSON logging
- Request/response correlation IDs
- Processing pipeline trace logs
- Error stack traces with context

## Risk Management

### Technical Risks
| Risk | Impact | Mitigation |
|------|--------|------------|
| Image quality variations | High | Multi-threshold detection, quality assessment |
| Processing time spikes | Medium | Auto-scaling, request queuing |
| Memory leaks | High | Regular restarts, memory monitoring |
| Model accuracy degradation | High | Continuous testing, model versioning |

### Business Risks
| Risk | Impact | Mitigation |
|------|--------|------------|
| High false positive rate | High | Confidence scoring, manual review flags |
| Service unavailability | High | Load balancing, redundancy |
| Data privacy concerns | Medium | Encryption, data anonymization |
| Scalability limitations | Medium | Horizontal scaling design |

## Success Criteria

### Launch Criteria
- [ ] 99%+ accuracy on test dataset
- [ ] < 3 second processing time
- [ ] Complete API documentation
- [ ] Security audit passed
- [ ] Load testing completed
- [ ] Monitoring dashboards active

### Post-Launch KPIs
- Processing accuracy > 99.5%
- Average response time < 2 seconds
- 99.9% uptime
- < 0.1% error rate
- Customer satisfaction > 4.5/5

## Timeline & Milestones

### Phase 1: Core Development (8 weeks)
- Week 1-2: Architecture setup and image processing pipeline
- Week 3-4: API development and database design
- Week 5-6: Scoring engine and validation logic
- Week 7-8: Testing and documentation

### Phase 2: Production Readiness (4 weeks)
- Week 9-10: Performance optimization and monitoring
- Week 11-12: Security hardening and deployment

### Phase 3: Launch & Support (2 weeks)
- Week 13: Production deployment and user onboarding
- Week 14: Post-launch monitoring and issue resolution

## Implementation Guidelines for Claude Code

### Project Structure
```
omr-microservice/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── api/
│   │   ├── __init__.py
│   │   ├── endpoints/
│   │   │   ├── __init__.py
│   │   │   ├── health.py       # Health check endpoint
│   │   │   └── evaluate.py     # Main evaluation endpoints
│   │   └── deps.py             # Dependencies and middleware
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # Configuration settings
│   │   ├── models.py           # Pydantic models
│   │   └── exceptions.py       # Custom exceptions
│   ├── services/
│   │   ├── __init__.py
│   │   ├── image_processor.py  # Image preprocessing
│   │   ├── omr_detector.py     # Bubble detection logic
│   │   ├── scorer.py           # Scoring engine
│   │   └── validator.py        # Input validation
│   └── utils/
│       ├── __init__.py
│       ├── image_utils.py      # Image utility functions
│       └── logging.py          # Logging configuration
├── tests/
│   ├── __init__.py
│   ├── test_api.py
│   ├── test_services.py
│   └── sample_images/          # Test OMR sheets
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

### Key Dependencies (requirements.txt)
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
pydantic==2.5.0
opencv-python==4.8.1.78
numpy==1.24.3
scikit-image==0.21.0
pillow==10.1.0
python-jose[cryptography]==3.3.0
redis==5.0.1
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.2
```

### Essential Implementation Notes

#### 1. Image Processing Pipeline
- Use OpenCV for preprocessing (grayscale, threshold, skew correction)
- Implement template matching for answer sheet detection
- Apply Hough Circle Transform for bubble detection
- Calculate fill ratio for each detected circle

#### 2. Error Handling Strategy
```python
# Custom exception classes needed:
class OMRProcessingError(Exception): pass
class ImageQualityError(OMRProcessingError): pass
class TemplateNotFoundError(OMRProcessingError): pass
class BubbleDetectionError(OMRProcessingError): pass
```

#### 3. Key Algorithms to Implement
- **Skew detection and correction**: Using Hough Line Transform
- **Reference point detection**: Corner markers (black dots) identification
- **Perspective correction**: Homography transformation
- **Bubble detection**: Circular Hough Transform with fill ratio calculation
- **Answer validation**: Multi-mark detection and confidence scoring

#### 4. Configuration Management
```python
# Use Pydantic Settings for configuration
class Settings(BaseSettings):
    app_name: str = "OMR Evaluation Service"
    version: str = "1.0.0"
    debug: bool = False
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    processing_timeout: int = 30
    confidence_threshold: float = 0.8
    redis_url: Optional[str] = None
    jwt_secret: str
    log_level: str = "INFO"
```

#### 5. Docker Configuration
```dockerfile
FROM python:3.11-slim

# Install system dependencies for OpenCV
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libglib2.0-0 \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Testing Requirements

#### Sample Data Needed
- Create test OMR sheets with known answers
- Include various quality conditions (good, poor lighting, skewed)
- Provide ground truth answer keys for validation

#### Test Coverage Areas
- Image preprocessing accuracy
- Bubble detection precision/recall
- Scoring calculation correctness
- API endpoint functionality
- Error handling scenarios

### Performance Considerations

#### Memory Management
- Process images in chunks for large files
- Clean up temporary files after processing
- Use generators for batch processing

#### Processing Optimization
- Implement early exit for poor quality images
- Cache template matching results within request scope
- Use NumPy vectorized operations for scoring

### Security Implementation
- Validate file types and sizes
- Implement rate limiting
- Add request timeout handling
- Sanitize all user inputs

## Implementation Priority Order

### Phase 1: Core MVP (Week 1-2)
1. Basic FastAPI setup with health endpoint
2. Image upload and validation
3. Simple bubble detection algorithm
4. Basic scoring logic
5. JSON response formatting

### Phase 2: Production Features (Week 3-4)
1. Advanced image preprocessing
2. Robust error handling
3. Confidence scoring
4. Batch processing
5. Comprehensive testing

### Phase 3: Optimization (Week 5-6)
1. Performance tuning
2. Docker containerization
3. Monitoring and logging
4. Documentation completion
5. Deployment preparation

## Claude Code Specific Instructions

When implementing this project:

1. **Start with the FastAPI skeleton** - Set up the basic app structure first
2. **Implement endpoints incrementally** - Begin with health check, then single evaluation
3. **Use test-driven development** - Write tests for each component before implementation
4. **Focus on the image processing pipeline** - This is the core complexity
5. **Handle edge cases early** - Poor image quality, multiple marks, etc.
6. **Add comprehensive logging** - Essential for debugging image processing issues
7. **Create sample test data** - Generate or find sample OMR sheets for testing

## Appendices

### A. API Schema Definitions
[Complete OpenAPI specification will be generated by FastAPI automatically]

### B. Error Code Reference
```python
ERROR_CODES = {
    "IMAGE_TOO_LARGE": "Image file exceeds maximum size limit",
    "INVALID_FORMAT": "Unsupported image format",
    "POOR_QUALITY": "Image quality too poor for processing",
    "TEMPLATE_NOT_FOUND": "Could not detect OMR sheet template",
    "PROCESSING_TIMEOUT": "Processing exceeded time limit",
    "INVALID_ANSWER_KEY": "Answer key format is invalid"
}
```

### C. Configuration Reference
[All environment variables and their purposes documented in code]

### D. Performance Benchmarks
[Target metrics for testing against after implementation]