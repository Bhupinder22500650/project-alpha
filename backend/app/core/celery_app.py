import os
from celery import Celery

# Uses redis as broker and backend
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "phishing_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['app.services.ingestion']
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    # Configure periodic tasks (Celery Beat)
    beat_schedule={
        'poll-ct-logs-every-15-mins': {
            'task': 'app.services.ingestion.scheduled_ingestion',
            'schedule': 900.0, # 15 minutes
        },
    }
)
