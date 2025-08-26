from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
from datetime import datetime
import uuid

from app.core.config import get_settings
from app.core.exceptions import OMRProcessingError
from app.utils.logging import logger
from app.api.endpoints import health, evaluate
from app import __version__

settings = get_settings()

# Track application start time
app_start_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info(f"Starting {settings.app_name} v{__version__}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"Max file size: {settings.max_file_size / 1024 / 1024:.1f} MB")
    
    yield
    
    logger.info("Shutting down application")


app = FastAPI(
    title=settings.app_name,
    version=__version__,
    description="Self-contained API service for processing scanned OMR answer sheets",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time header to all responses"""
    start_time = time.time()
    request_id = str(uuid.uuid4())
    
    # Add request ID to request state
    request.state.request_id = request_id
    
    # Log incoming request
    logger.info(f"Request {request_id}: {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    response.headers["X-Request-ID"] = request_id
    
    # Log response
    logger.info(f"Request {request_id} completed in {process_time:.3f}s")
    
    return response


@app.exception_handler(OMRProcessingError)
async def omr_exception_handler(request: Request, exc: OMRProcessingError):
    """Handle OMR processing exceptions"""
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.error(f"OMR Processing Error in request {request_id}: {exc.message}")
    
    return JSONResponse(
        status_code=422,
        content={
            "request_id": request_id,
            "status": "error",
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.error(f"Unexpected error in request {request_id}: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "request_id": request_id,
            "status": "error",
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "details": {"error": str(exc)} if settings.debug else {}
            }
        }
    )


# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(evaluate.router, prefix=settings.api_v1_str, tags=["evaluation"])

# Import and include enhanced evaluation endpoints
from app.api.endpoints import enhanced_evaluate
app.include_router(enhanced_evaluate.router, prefix=settings.api_v1_str, tags=["enhanced-evaluation"])


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint"""
    return {
        "service": settings.app_name,
        "version": __version__,
        "status": "operational",
        "documentation": "/docs" if settings.debug else None
    }


def get_app_uptime():
    """Get application uptime in seconds"""
    return int(time.time() - app_start_time)