# tasks.py
import os
from celery import Celery

BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://redis:6379/0")
RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://redis:6379/0")

celery_app = Celery(
    "school_notices",
    broker=BROKER_URL,
    backend=RESULT_BACKEND,
)


@celery_app.task
def test_task(x=1, y=2):
    return x + y


@celery_app.task
def crawl_source(source: str):
    """
    지정된 소스에서 크롤링을 수행하는 Celery 태스크
    """
    print(f"[Celery Task] Crawling source: {source}")
    # 여기에 실제 크롤링 로직 구현
    # 예: from .crawlers import run_crawler
    # return run_crawler(source)
    return {
        "status": "completed",
        "source": source,
        "message": "Crawling task completed",
    }
