"""
Configuration for OMR Microservice
"""

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # Application
    APP_NAME: str = "OMR Detection & Autograding API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = False

    # Paths
    BASE_DIR: Path = Path(__file__).parent.parent
    MODEL_PATH: Path = BASE_DIR / "models" / "epoch20.pt"
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    RESULTS_DIR: Path = BASE_DIR / "results"
    ANSWER_KEYS_DIR: Path = BASE_DIR / "answer_keys"

    # CORS
    CORS_ORIGINS: list = ["*"]

    # File uploads
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB

    class Config:
        env_file = ".env"
        case_sensitive = True


# Create global settings instance
settings = Settings()

# Ensure directories exist
settings.UPLOAD_DIR.mkdir(exist_ok=True)
settings.RESULTS_DIR.mkdir(exist_ok=True)
settings.ANSWER_KEYS_DIR.mkdir(exist_ok=True)
