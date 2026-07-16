import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import duckdb
from backend.app.config import settings

# SQLAlchemy setup (SQLite)
engine = create_engine(
    settings.SQLITE_DB_PATH,
    connect_args={"check_same_thread": False}  # Needed for SQLite multi-thread FastAPI routes
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Dependency injector for SQLAlchemy SQLite session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# DuckDB Setup (Event Log & History)
def get_duckdb_conn():
    """Get a connection to DuckDB file for event logging"""
    # DuckDB supports file-level locking. We connect and ensure we close properly.
    conn = duckdb.connect(settings.DUCKDB_PATH)
    return conn

def init_databases():
    """Initialize DB tables if they don't exist"""
    # Create SQLite relational tables
    Base.metadata.create_all(bind=engine)
    
    # Initialize DuckDB simulation_events table
    conn = get_duckdb_conn()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS simulation_events (
                event_id VARCHAR(36) PRIMARY KEY,
                world_id VARCHAR(36),
                tick INTEGER,
                event_type VARCHAR(100),
                source_entity_id VARCHAR(36),
                target_entity_id VARCHAR(36),
                description TEXT,
                metadata JSON,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    finally:
        conn.close()
