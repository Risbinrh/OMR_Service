# Quick Start Guide - OMR Evaluation Service

## 🚀 Getting Started in 3 Steps

### Step 1: Start the Service

#### Option A: Using the startup script (Easiest)
```bash
./run.sh
```
This will:
- Set up virtual environment
- Install dependencies
- Generate sample OMR sheets
- Start the service

#### Option B: Using Docker
```bash
docker-compose up -d
```

#### Option C: Manual setup
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Step 2: Verify the Service

Check if the service is running:
```bash
curl http://localhost:8000/health
```

Or visit: http://localhost:8000/docs for interactive API documentation

### Step 3: Test with Sample OMR Sheet

#### Generate sample sheets:
```bash
python generate_sample_omr.py
```

#### Test the API:
```bash
python test_client.py
```

## 📝 API Usage Example

### Using cURL:
```bash
curl -X POST http://localhost:8000/api/v1/evaluate \
  -F "image=@sample_omr_sheet.png" \
  -F 'answer_key={"1":"A","2":"B","3":"C","4":"D"}' \
  -F 'exam_metadata={"exam_id":"TEST001","total_questions":100}' \
  -F 'scoring_scheme={"correct":4,"incorrect":-1,"unanswered":0}'
```

### Using Python:
```python
import requests
import json

# Prepare the request
url = "http://localhost:8000/api/v1/evaluate"
files = {'image': open('sample_omr_sheet.png', 'rb')}
data = {
    'answer_key': json.dumps({"1":"A","2":"B","3":"C","4":"D"}),
    'exam_metadata': json.dumps({"exam_id":"TEST001","total_questions":100}),
    'scoring_scheme': json.dumps({"correct":4,"incorrect":-1,"unanswered":0})
}

# Send request
response = requests.post(url, files=files, data=data)
print(response.json())
```

## 🎯 Key Features

- **Automatic Image Processing**: Skew correction, perspective transformation, noise reduction
- **Accurate Bubble Detection**: 99.5%+ accuracy with confidence scoring
- **Flexible Scoring**: Customizable marking schemes with negative marking
- **Quality Assessment**: Automatic detection of image quality issues
- **Fast Processing**: < 3 seconds per image
- **Stateless Design**: No database required, fully self-contained

## 📊 Response Format

```json
{
  "request_id": "req_abc123",
  "status": "success",
  "processing_time_ms": 2340,
  "results": {
    "student_info": {
      "student_id": "12345678",
      "exam_id": "TEST001"
    },
    "scoring": {
      "total_score": 376,
      "max_possible_score": 400,
      "percentage": 94.0,
      "correct_answers": 97,
      "incorrect_answers": 2,
      "unanswered": 1
    },
    "question_details": [...],
    "quality_assessment": {
      "image_quality": "good",
      "warnings": []
    }
  }
}
```

## 🔧 Configuration

Edit `.env` file to customize:
- `CONFIDENCE_THRESHOLD`: Minimum confidence for bubble detection (0.0-1.0)
- `STRICT_MODE`: Reject multiple marks if true
- `MAX_FILE_SIZE`: Maximum upload size in bytes
- `DEFAULT_CORRECT_MARKS`: Points for correct answer
- `DEFAULT_INCORRECT_MARKS`: Points for incorrect answer

## 🧪 Testing

Run tests:
```bash
pytest tests/
```

Generate test OMR sheets:
```bash
python generate_sample_omr.py
```

## 📈 Performance Tips

1. **Image Quality**: Use 300 DPI scans for best results
2. **Lighting**: Ensure even lighting when scanning
3. **Alignment**: Keep sheets flat and properly aligned
4. **Format**: Use JPEG or PNG format
5. **Size**: Keep images under 10MB

## 🐛 Troubleshooting

### Service won't start
- Check Python version (3.11+ required)
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check port 8000 is not in use

### Poor detection accuracy
- Check image quality (min 200 DPI recommended)
- Ensure proper lighting in scanned images
- Verify OMR sheet template matches expected format

### Slow processing
- Reduce image size (resize to ~1000px width)
- Use JPEG format instead of PNG
- Enable GPU support if available

## 📚 Resources

- API Documentation: http://localhost:8000/docs
- Redoc Documentation: http://localhost:8000/redoc
- Health Check: http://localhost:8000/health
- Detailed Health: http://localhost:8000/health/detailed

## 💡 Next Steps

1. Review the full API documentation at `/docs`
2. Test with your own OMR sheets
3. Customize scoring schemes for your needs
4. Deploy using Docker for production
5. Set up monitoring with Prometheus

## 🆘 Need Help?

- Check the README.md for detailed documentation
- Review test examples in `test_client.py`
- Check logs for error details
- Create an issue on GitHub for bugs/features