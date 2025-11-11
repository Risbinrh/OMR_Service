@echo off
REM Start OMR Microservice (Windows)

echo Starting OMR Detection ^& Autograding Microservice...

REM Check if model exists
if not exist "..\epoch20.pt" (
    echo ERROR: Model file not found: ..\epoch20.pt
    pause
    exit /b 1
)

REM Check for virtual environment in parent directory
if not exist "..\venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found
    echo Please run: python -m venv venv
    echo Then: venv\Scripts\pip install -r microservice\requirements.txt
    pause
    exit /b 1
)

REM Create directories
if not exist "uploads" mkdir uploads
if not exist "results" mkdir results
if not exist "answer_keys" mkdir answer_keys

REM Start server
echo.
echo Starting server on http://localhost:8000
echo API Documentation: http://localhost:8000/docs
echo.
..\venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
