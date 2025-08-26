from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "OMR Evaluation Service"
    version: str = "1.0.0"
    debug: bool = False
    
    # API Settings
    api_v1_str: str = "/api/v1"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_extensions: set = {".jpg", ".jpeg", ".png", ".pdf"}
    
    # Processing Settings
    processing_timeout: int = 30
    confidence_threshold: float = 0.8
    strict_mode: bool = True
    max_workers: int = 4
    temp_dir: str = "/tmp/omr_processing"
    
    # Redis Settings (Optional for batch processing)
    redis_url: Optional[str] = None
    redis_ttl: int = 3600  # 1 hour
    
    # Security Settings
    jwt_secret: str = "your-secret-key-change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60
    
    # Logging Settings
    log_level: str = "INFO"
    log_format: str = "json"
    
    # OMR Detection Settings
    min_bubble_fill_ratio: float = 0.3
    max_bubble_fill_ratio: float = 0.95
    bubble_detection_threshold: int = 180
    min_circle_radius: int = 8
    max_circle_radius: int = 20
    
    # Scoring Settings
    default_correct_marks: int = 4
    default_incorrect_marks: int = -1
    default_unanswered_marks: int = 0
    
    # Batch Processing Settings
    max_batch_size: int = 50
    batch_processing_queue: str = "omr_batch_queue"
    
    # Performance Settings
    enable_gpu: bool = False
    image_cache_size: int = 100
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()