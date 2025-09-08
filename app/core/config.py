from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "Lexi Case Tracker API"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    JAGRITI_BASE_URL: str = "https://e-jagriti.gov.in"
    JAGRITI_TIMEOUT: int = 60
    JAGRITI_MAX_RETRIES: int = 3
    REQUEST_DELAY: float = 2.0
    
    JAGRITI_USERNAME: Optional[str] = None
    JAGRITI_PASSWORD: Optional[str] = None
    JAGRITI_MOBILE: Optional[str] = None
    
    USE_HEADLESS_BROWSER: bool = True
    BROWSER_TIMEOUT: int = 30000
    
    ALLOWED_ORIGINS: List[str] = ["*"]
    
    LOG_LEVEL: str = "INFO"
    LOG_ROTATION: str = "1 day"
    LOG_RETENTION: str = "30 days"
    
    CACHE_TTL_STATES: int = 86400
    CACHE_TTL_COMMISSIONS: int = 3600 
    CACHE_TTL_CASES: int = 300
    
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 3600
    
    DATABASE_URL: str = "sqlite:///./cases.db"
    
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()