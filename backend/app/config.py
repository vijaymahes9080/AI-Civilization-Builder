import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API Configurations
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    
    # Local Storage Paths
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    SQLITE_DB_PATH: str = f"sqlite:///{os.path.join(BASE_DIR, 'civilization.db')}"
    DUCKDB_PATH: str = os.path.join(BASE_DIR, "history.duckdb")
    VECTOR_STORE_DIR: str = os.path.join(BASE_DIR, "vector_memory")
    
    # Local AI Configurations
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"  # or qwen2.5-coder:7b
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    
    # Simulation Parameters
    WORLD_WIDTH: int = 50
    WORLD_HEIGHT: int = 50
    INITIAL_CITIZENS: int = 20
    DEFAULT_TICK_RATE_MS: int = 1000  # 1 second per tick
    
    # Event Bus / PubSub
    REDIS_URL: str = ""  # If empty, use internal memory/SQLite queue
    
    class Config:
        env_prefix = "CIV_"
        case_sensitive = True

settings = Settings()

# Create vector store directory if it doesn't exist
os.makedirs(settings.VECTOR_STORE_DIR, exist_ok=True)
