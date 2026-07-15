from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
import redis
import logging
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler

from .api.endpoints import router as domains_router
from .db import engine, Base
from .services.scorer import load_models

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load ML Model
    load_models()
    
    logger.info("Application starting up... Celery will handle ingestion tasks.")
    yield
    logger.info("Application shutting down...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="API for the AI-Powered Phishing Domain Detector",
    lifespan=lifespan
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to the frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from .api.endpoints import router as domains_router
from .api.auth import router as auth_router

app.include_router(auth_router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(domains_router, prefix="/api/v1")

@app.get("/health", tags=["System"])
async def health_check():
    status = {"api": "ok", "redis": "unknown"}
    
    # Check Redis connection
    try:
        r = redis.Redis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        r.ping()
        status["redis"] = "ok"
    except Exception as e:
        status["redis"] = f"error: {str(e)}"
        
    return {"status": status}

@app.get("/", tags=["System"])
async def root():
    return {"message": "Welcome to the Phishing Domain Detector API"}
