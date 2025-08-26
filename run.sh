#!/bin/bash

# OMR Service Startup Script

echo "OMR Evaluation Microservice"
echo "=========================="

# Check Python version
python_version=$(python3 --version 2>&1 | grep -Po '(?<=Python )\d+\.\d+')
echo "Python version: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
fi

# Create necessary directories
mkdir -p logs
mkdir -p tests/sample_images

# Generate sample OMR sheets if they don't exist
if [ ! -f "sample_omr_sheet.png" ]; then
    echo "Generating sample OMR sheets..."
    python generate_sample_omr.py
fi

# Run the application
echo ""
echo "Starting OMR service..."
echo "API will be available at: http://localhost:8000"
echo "API Documentation: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload