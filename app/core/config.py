from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    PROJECT_NAME: str = "Lexi Case Tracker"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    JAGRITI_BASE_URL: str = "https://e-jagriti.gov.in"
    JAGRITI_TIMEOUT: int = 30
    
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "https://your-frontend-domain.com"
    ]
    
    LOG_LEVEL: str = "INFO"
    
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL: int = 3600
    
    class Config:
        env_file = ".env"


settings = Settings()