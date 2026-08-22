from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    SARVAM_API_KEY: str = ""
    LLM_PROVIDER: str = "openai" # "openai", "anthropic"
    LLM_API_KEY: str = ""
    LLM_BASE_URL: Optional[str] = None
    LLM_MODEL: str = "gpt-4o-mini"
    RERANKER_MODEL: str = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"
    
    DATA_DIR: str = "./data"
    INDEX_DIR: str = "./data/indexes"
    DB_PATH: str = "./data/metadata.db"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
