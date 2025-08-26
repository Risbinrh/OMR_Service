import logging
import sys
from pythonjsonlogger import jsonlogger
from app.core.config import get_settings

settings = get_settings()


def setup_logging():
    """Configure logging for the application"""
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    # Create logger
    logger = logging.getLogger("omr_service")
    logger.setLevel(log_level)
    
    # Remove existing handlers
    logger.handlers = []
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    
    # Configure formatter based on settings
    if settings.log_format == "json":
        formatter = jsonlogger.JsonFormatter(
            "%(timestamp)s %(level)s %(name)s %(message)s",
            rename_fields={"timestamp": "time", "level": "severity"}
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Configure uvicorn access logs
    uvicorn_logger = logging.getLogger("uvicorn.access")
    uvicorn_logger.handlers = []
    uvicorn_logger.addHandler(handler)
    uvicorn_logger.setLevel(log_level)
    
    return logger


logger = setup_logging()