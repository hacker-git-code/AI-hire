from typing import Any, Dict, List, Optional
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, validator, Field
from pathlib import Path
from functools import lru_cache

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "AI Hiring Assistant"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "AI Hiring Assistant API"
    
    # Security
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str
    
    # Google Gemini
    GOOGLE_API_KEY: str
    
    # Email (Optional)
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = None
    
    # Storage (Using Supabase Storage)
    STORAGE_BUCKET: str = "resumes"
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Vector Search Configuration (using Supabase pgvector)
    VECTOR_DIMENSION: int = 768  # Default dimension for embeddings
    
    # File Storage
    UPLOAD_DIR: Path = Path("uploads")
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # Security
    ALGORITHM: str = "HS256"
    
    class Config:
        case_sensitive = True
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

settings = get_settings() 