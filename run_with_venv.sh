#!/bin/bash

# OMR Service with Virtual Environment

echo "🎯 Starting 100% Accurate OMR Service with omr_venv"
echo "================================================="

# Activate virtual environment
echo "📦 Activating virtual environment..."
source omr_venv/bin/activate

# Check if packages are installed
python -c "import cv2, numpy, fastapi, uvicorn, requests, sklearn" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Some packages missing. Please reinstall."
    exit 1
fi

echo "✅ All packages available"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
fi

# Create necessary directories
mkdir -p logs
mkdir -p tests/sample_images

# Generate sample OMR sheets if they don't exist
if [ ! -f "sample_omr_sheet.png" ]; then
    echo "🖼️ Generating sample OMR sheets..."
    python generate_sample_omr.py
fi

echo ""
echo "🚀 Starting 100% Accurate OMR Service..."
echo "🔗 API Documentation: http://localhost:8000/docs"
echo "⚡ Enhanced Endpoint: /api/v1/evaluate-with-fallback"
echo "🎯 Test Command: python analyze_test_omr.py"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload