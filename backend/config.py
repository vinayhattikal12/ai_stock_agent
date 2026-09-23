import os
from typing import List
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    UPSTOX_ACCESS_TOKEN: str = os.getenv("UPSTOX_ACCESS_TOKEN", "")
    UPSTOX_API_VERSION: str = os.getenv("UPSTOX_API_VERSION", "v2")
    UPSTOX_BASE_URL: str = "https://api.upstox.com"
    
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/stock_intelligence.db")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    PORT: int = int(os.getenv("PORT", "8000"))
    HOST: str = os.getenv("HOST", "0.0.0.0")
    
    CORS_ORIGINS: List[str] = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS", 
            "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"
        ).split(",")
        if origin.strip()
    ]

settings = Settings()
