"""
OMR Detection and Autograding Microservice
FastAPI-based REST API for processing OMR sheets and automatic grading
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
from datetime import datetime
from pathlib import Path
import shutil
import json

# Import OMR pipeline from app directory
from app.mobile_omr_pipeline_v2 import MobileOMRPipelineV2

from app.models import (
    ProcessResponse,
    GradeRequest,
    GradeResponse,
    AnswerKey,
    AnswerKeyCreate,
    GradingRules,
)
from app.grading import GradingEngine
from app.storage import AnswerKeyStorage


# Initialize FastAPI app
app = FastAPI(
    title="OMR Detection & Autograding API",
    description="REST API for processing mobile photos of OMR sheets and automatic grading",
    version="1.0.0",
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
MODEL_PATH = Path("../epoch20.pt")
UPLOAD_DIR = Path("uploads")
RESULTS_DIR = Path("results")
ANSWER_KEYS_DIR = Path("answer_keys")

# Create directories
UPLOAD_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)
ANSWER_KEYS_DIR.mkdir(exist_ok=True)

# Initialize OMR pipeline
omr_pipeline = None
answer_key_storage = AnswerKeyStorage(ANSWER_KEYS_DIR)
grading_engine = GradingEngine()


@app.on_event("startup")
async def startup_event():
    """Initialize the OMR pipeline on startup"""
    global omr_pipeline

    if not MODEL_PATH.exists():
        raise RuntimeError(f"Model not found: {MODEL_PATH}")

    omr_pipeline = MobileOMRPipelineV2(str(MODEL_PATH))
    print(f"OMR Pipeline initialized with model: {MODEL_PATH}")


@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "service": "OMR Detection & Autograding API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "docs": "/docs",
            "process": "/api/v1/process",
            "grade": "/api/v1/grade",
            "answer_keys": "/api/v1/answer-keys",
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "model_loaded": omr_pipeline is not None,
    }


@app.post("/api/v1/process", response_model=ProcessResponse)
async def process_omr_sheet(
    file: UploadFile = File(..., description="OMR sheet image (JPG/PNG)"),
    save_debug: bool = Form(True, description="Save debug visualization images"),
):
    """
    Process an OMR sheet image and extract answers

    - **file**: Image file of OMR sheet (mobile photo)
    - **save_debug**: Whether to save debug visualization images

    Returns detected answers and processing metadata
    """

    # Validate file type
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(400, "File must be an image")

    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    file_path = UPLOAD_DIR / filename

    # Save uploaded file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(500, f"Failed to save file: {str(e)}")

    # Process with OMR pipeline
    try:
        results = omr_pipeline.process(str(file_path), save_debug=save_debug)

        if "error" in results:
            raise HTTPException(400, results["error"])

        extraction = results["extraction"]
        answers = extraction["answers"]

        # Prepare response
        response = ProcessResponse(
            success=True,
            image_filename=filename,
            processed_at=datetime.now().isoformat(),
            total_questions=100,
            answered=len(answers),
            unanswered=extraction["unanswered"],
            multiple_fills=len(extraction["multiple_fills"]),
            answers=answers,
            multiple_fills_details=extraction["multiple_fills"],
            detection_count=results["detection_count"],
        )

        # Save results
        result_file = RESULTS_DIR / f"{timestamp}_{Path(file.filename).stem}_result.json"
        with open(result_file, "w") as f:
            json.dump(response.dict(), f, indent=2)

        return response

    except Exception as e:
        raise HTTPException(500, f"Processing failed: {str(e)}")


@app.post("/api/v1/grade", response_model=GradeResponse)
async def grade_omr_sheet(
    file: UploadFile = File(..., description="OMR sheet image"),
    answer_key_id: str = Form(..., description="Answer key ID"),
    correct_marks: float = Form(1.0, description="Marks for correct answer"),
    wrong_marks: float = Form(0.0, description="Marks deducted for wrong answer"),
    unanswered_marks: float = Form(0.0, description="Marks for unanswered"),
):
    """
    Process OMR sheet and grade against answer key

    - **file**: OMR sheet image
    - **answer_key_id**: ID of the answer key to use
    - **correct_marks**: Marks awarded for correct answer (default: 1.0)
    - **wrong_marks**: Marks deducted for wrong answer (default: 0.0, use negative for penalty)
    - **unanswered_marks**: Marks for unanswered questions (default: 0.0)

    Returns grading results with score and detailed comparison
    """

    # First, process the OMR sheet
    process_result = await process_omr_sheet(file, save_debug=True)

    if not process_result.success:
        raise HTTPException(400, "Failed to process OMR sheet")

    # Load answer key
    answer_key = answer_key_storage.get_answer_key(answer_key_id)
    if not answer_key:
        raise HTTPException(404, f"Answer key not found: {answer_key_id}")

    # Create grading rules
    rules = GradingRules(
        correct_marks=correct_marks,
        wrong_marks=wrong_marks,
        unanswered_marks=unanswered_marks,
    )

    # Grade the sheet
    try:
        grade_result = grading_engine.grade(
            student_answers=process_result.answers,
            answer_key=answer_key.answers,
            rules=rules,
        )

        # Prepare response
        response = GradeResponse(
            success=True,
            image_filename=process_result.image_filename,
            answer_key_id=answer_key_id,
            answer_key_name=answer_key.name,
            graded_at=datetime.now().isoformat(),
            total_questions=100,
            answered=process_result.answered,
            correct=grade_result["correct"],
            wrong=grade_result["wrong"],
            unanswered=process_result.unanswered,
            score=grade_result["score"],
            max_score=grade_result["max_score"],
            percentage=grade_result["percentage"],
            grading_rules=rules,
            detailed_results=grade_result["details"],
        )

        # Save grading results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = RESULTS_DIR / f"{timestamp}_grading_result.json"
        with open(result_file, "w") as f:
            json.dump(response.dict(), f, indent=2)

        return response

    except Exception as e:
        raise HTTPException(500, f"Grading failed: {str(e)}")


@app.post("/api/v1/answer-keys", response_model=AnswerKey)
async def create_answer_key(answer_key: AnswerKeyCreate):
    """
    Create a new answer key

    - **name**: Name/description of the answer key
    - **answers**: Dictionary of question number to correct answer (1-100)
    - **metadata**: Optional metadata (exam name, date, etc.)
    """

    # Validate answers
    if len(answer_key.answers) > 100:
        raise HTTPException(400, "Maximum 100 questions allowed")

    for q_num in answer_key.answers.keys():
        if q_num < 1 or q_num > 100:
            raise HTTPException(400, f"Invalid question number: {q_num}")
        if answer_key.answers[q_num] not in ["A", "B", "C", "D"]:
            raise HTTPException(400, f"Invalid answer for Q{q_num}: {answer_key.answers[q_num]}")

    # Create answer key
    try:
        created_key = answer_key_storage.create_answer_key(answer_key)
        return created_key
    except Exception as e:
        raise HTTPException(500, f"Failed to create answer key: {str(e)}")


@app.get("/api/v1/answer-keys", response_model=List[AnswerKey])
async def list_answer_keys():
    """List all available answer keys"""
    return answer_key_storage.list_answer_keys()


@app.get("/api/v1/answer-keys/{answer_key_id}", response_model=AnswerKey)
async def get_answer_key(answer_key_id: str):
    """Get a specific answer key by ID"""
    answer_key = answer_key_storage.get_answer_key(answer_key_id)
    if not answer_key:
        raise HTTPException(404, f"Answer key not found: {answer_key_id}")
    return answer_key


@app.delete("/api/v1/answer-keys/{answer_key_id}")
async def delete_answer_key(answer_key_id: str):
    """Delete an answer key"""
    if answer_key_storage.delete_answer_key(answer_key_id):
        return {"success": True, "message": f"Answer key deleted: {answer_key_id}"}
    else:
        raise HTTPException(404, f"Answer key not found: {answer_key_id}")


@app.post("/api/v1/batch-process")
async def batch_process(files: List[UploadFile] = File(...)):
    """
    Process multiple OMR sheets in batch

    Returns list of processing results for each image
    """

    results = []

    for file in files:
        try:
            result = await process_omr_sheet(file, save_debug=False)
            results.append({
                "filename": file.filename,
                "success": True,
                "result": result.dict(),
            })
        except Exception as e:
            results.append({
                "filename": file.filename,
                "success": False,
                "error": str(e),
            })

    return {
        "total": len(files),
        "successful": sum(1 for r in results if r["success"]),
        "failed": sum(1 for r in results if not r["success"]),
        "results": results,
    }


@app.post("/api/v1/batch-grade")
async def batch_grade(
    files: List[UploadFile] = File(...),
    answer_key_id: str = Form(...),
    correct_marks: float = Form(1.0),
    wrong_marks: float = Form(0.0),
):
    """
    Grade multiple OMR sheets in batch against the same answer key

    Returns grading results for each sheet
    """

    results = []

    for file in files:
        try:
            result = await grade_omr_sheet(
                file, answer_key_id, correct_marks, wrong_marks, 0.0
            )
            results.append({
                "filename": file.filename,
                "success": True,
                "score": result.score,
                "percentage": result.percentage,
                "result": result.dict(),
            })
        except Exception as e:
            results.append({
                "filename": file.filename,
                "success": False,
                "error": str(e),
            })

    # Calculate statistics
    successful_results = [r for r in results if r["success"]]

    statistics = {}
    if successful_results:
        scores = [r["score"] for r in successful_results]
        percentages = [r["percentage"] for r in successful_results]

        statistics = {
            "total_graded": len(successful_results),
            "average_score": sum(scores) / len(scores),
            "average_percentage": sum(percentages) / len(percentages),
            "highest_score": max(scores),
            "lowest_score": min(scores),
        }

    return {
        "total": len(files),
        "successful": len(successful_results),
        "failed": len(results) - len(successful_results),
        "statistics": statistics,
        "results": results,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
