import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Server configuration settings that can be updated from environment variables."""
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    CORS_ORIGINS: list = ["*"]
    MAX_UPLOAD_SIZE_MB: int = 10
    LOG_LEVEL: str = "INFO"
    MODEL_PATH: str = "../waray_speech_model.keras"
    ENCODER_PATH: str = "../encoder_classes.npy"
    
    # Production settings
    PRODUCTION: bool = False
    SECRET_KEY: str = "change-this-in-production"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()