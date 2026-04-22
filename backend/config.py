"""
Configuration settings for Travel AI Agent Platform
"""

from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings"""
    
    # API Keys
    openai_api_key: str
    pinecone_api_key: str
    pinecone_environment: str
    
    # Database
    database_url: str = "sqlite:///./travel_ai.db"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # Travel APIs
    amadeus_api_key: Optional[str] = None
    amadeus_secret: Optional[str] = None
    booking_api_key: Optional[str] = None
    weather_api_key: Optional[str] = None
    viator_api_key: Optional[str] = None
    
    # JWT
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
