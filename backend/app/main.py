from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from backend.app.config import settings
from backend.app.database import init_databases, get_db
from backend.app.api.websocket import router as ws_router

app = FastAPI(
    title="AI Civilization Builder",
    description="Build living civilizations instead of static simulations.",
    version="1.0.0"
)

# Set CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup events
@app.on_event("startup")
def startup_event():
    init_databases()

# Include WebSocket routes
app.include_router(ws_router)

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "config": {"world_size": f"{settings.WORLD_WIDTH}x{settings.WORLD_HEIGHT}"}}

@app.get("/api/worlds")
def list_worlds(db: Session = Depends(get_db)):
    # To be populated with worlds logic
    return []
