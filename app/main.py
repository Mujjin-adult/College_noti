from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from tasks import crawl_source  # Celery task
from typing import Optional

app = FastAPI(title="School Notice Crawler API")


# 요청 바디 스키마
class CrawlRequest(BaseModel):
    source: str  # 예: "academic", "scholarship"
    immediate: Optional[bool] = False  # True면 즉시 실행


@app.get("/")
def root():
    return {"message": "School Notice Crawler API is running"}


@app.post("/crawl")
def trigger_crawl(req: CrawlRequest, background_tasks: BackgroundTasks):
    """
    Celery로 크롤링 작업을 등록하거나, 즉시 실행
    """
    if req.immediate:
        # FastAPI Background Task로 즉시 실행
        background_tasks.add_task(run_crawl_direct, req.source)
        return {"status": "started_immediately", "source": req.source}
    else:
        # Celery 큐로 작업 지시
        crawl_source.delay(req.source)
        return {"status": "queued_to_celery", "source": req.source}


def run_crawl_direct(source: str):
    """
    FastAPI Background Task로 직접 실행 (테스트용)
    """
    print(f"[Direct Run] Crawling source: {source}")
    # 여기에 실제 크롤링 코드 호출
    # 예: from crawler.parsers import run_parser
    # run_parser(source)


@app.get("/health")
def health_check():
    return {"status": "ok"}
