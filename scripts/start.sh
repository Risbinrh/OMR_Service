#!/bin/bash
# Start OMR Microservice (Linux/Mac)

echo "Starting OMR Detection & Autograding Microservice..."

# Check if model exists
if [ ! -f "../epoch20.pt" ]; then
    echo "ERROR: Model file not found: ../epoch20.pt"
    exit 1
fi

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Create directories
mkdir -p uploads results answer_keys

# Start server
echo "Starting server on http://localhost:8000"
echo "API Documentation: http://localhost:8000/docs"
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
