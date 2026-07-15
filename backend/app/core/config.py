from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Phishing Domain Detector API"
    VERSION: str = "0.1.0"
    
    # Database
    DATABASE_URL: str = "postgresql://phishing_user:phishing_pass@localhost:5432/phishing_db"
    
    # Redis Cache
    REDIS_URL: str = "redis://localhost:6379/0"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

settings = Settings()
