from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
import redis
import logging
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler

from .api.endpoints import router as domains_router
from .db import engine, Base
from .services.ingestion import process_new_domains
from .services.scorer import load_model

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create tables
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load ML Model
    load_model()
    
    # Setup Scheduler
    scheduler = BackgroundScheduler()
    # Run every 15 minutes
    scheduler.add_job(process_new_domains, 'interval', minutes=15)
    scheduler.start()
    
    # Run once on startup just to populate prototype
    logger.info("Running initial ingestion...")
    import threading
    threading.Thread(target=process_new_domains).start()
    
    yield
    scheduler.shutdown()

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
