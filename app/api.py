from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from database import get_db
from crud import (
    create_job,
    get_job,
    get_jobs,
    update_job_status,
    create_task,
    get_task,
    get_tasks,
    update_task_status,
    create_document,
    get_documents,
    get_documents_by_job,
    get_job_statistics,
    get_host_statistics,
)

router = APIRouter()


# 잡 생성 요청 스키마
class JobCreateRequest(BaseModel):
    name: str
    priority: str
    seed_type: str
    seed_payload: dict
    render_mode: str
    rate_limit_per_host: Optional[float] = 1.0
    max_depth: Optional[int] = 1
    robots_policy: str
    schedule_cron: Optional[str] = None


# 잡 생성
@router.post("/jobs")
def create_job(req: JobCreateRequest):
    # TODO: DB에 crawl_job 저장, celery beat에 등록
    # 예시: crawl_task.apply_async(args=[job_id, url, req.priority, req.render_mode], priority=1)
    return {"status": "created", "job": req}


# 잡 조회
@router.get("/jobs/{job_id}")
def get_job(job_id: int):
    # TODO: DB에서 조회
    return {"job_id": job_id, "status": "mock"}


# 잡 상태 변경
@router.post("/jobs/{job_id}/{action}")
def job_action(job_id: int, action: str):
    # action: pause/resume/cancel
    # TODO: DB 상태 변경, celery 작업 제어
    return {"job_id": job_id, "action": action, "result": "mock"}


# 수동 트리거
@router.post("/jobs/{job_id}/run")
def run_job(job_id: int):
    # TODO: 해당 잡의 시드/URL 목록을 celery에 등록
    return {"job_id": job_id, "triggered": True}


# 추출 결과 검색
@router.get("/docs")
def search_docs(
    job_id: Optional[int] = None, url: Optional[str] = None, q: Optional[str] = None
):
    # TODO: DB에서 extracted_doc 검색
    return {"results": []}


# 헬스 체크
@router.get("/health")
def health():
    return {"status": "ok"}


# 메트릭 엔드포인트 (Prometheus)
@router.get("/metrics")
def metrics():
    # TODO: Prometheus 메트릭 반환
    return (
        "# HELP crawler_tasks_total ...\n# TYPE crawler_tasks_total counter\ncrawler_tasks_total{status='success'} 10\n",
        200,
        {"Content-Type": "text/plain"},
    )


@router.get("/documents")
def get_all_documents(
    db: Session = Depends(get_db),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    source: Optional[str] = Query(
        None, description="Filter by source (e.g., volunteer, job, scholarship)"
    ),
    category: Optional[str] = Query(None, description="Filter by category"),
):
    """모든 추출된 문서 조회"""
    documents = get_documents(
        db, limit=limit, offset=offset, source=source, category=category
    )
    return {"documents": documents, "total": len(documents)}


@router.get("/documents/summary")
def get_documents_summary(db: Session = Depends(get_db)):
    """문서 요약 통계 조회"""
    try:
        # 소스별 문서 수
        source_stats = db.execute(
            """
            SELECT source, COUNT(*) as count, MAX(created_at) as latest_update
            FROM extracted_doc 
            GROUP BY source 
            ORDER BY count DESC
        """
        ).fetchall()

        # 카테고리별 문서 수
        category_stats = db.execute(
            """
            SELECT category, COUNT(*) as count
            FROM extracted_doc 
            WHERE category IS NOT NULL
            GROUP BY category 
            ORDER BY count DESC
        """
        ).fetchall()

        # 전체 통계
        total_docs = db.execute("SELECT COUNT(*) FROM extracted_doc").scalar()
        latest_doc = db.execute("SELECT MAX(created_at) FROM extracted_doc").scalar()

        return {
            "total_documents": total_docs,
            "latest_update": latest_doc,
            "source_statistics": [
                {
                    "source": row.source,
                    "count": row.count,
                    "latest_update": row.latest_update,
                }
                for row in source_stats
            ],
            "category_statistics": [
                {"category": row.category, "count": row.count} for row in category_stats
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")


@router.get("/documents/recent")
def get_recent_documents(
    db: Session = Depends(get_db), limit: int = Query(20, ge=1, le=100)
):
    """최근 크롤링된 문서 조회"""
    try:
        recent_docs = db.execute(
            """
            SELECT 
                title, writer, date, hits, url, source, category, created_at
            FROM extracted_doc 
            ORDER BY created_at DESC 
            LIMIT :limit
        """,
            {"limit": limit},
        ).fetchall()

        return {
            "documents": [
                {
                    "title": doc.title,
                    "writer": doc.writer,
                    "date": doc.date,
                    "hits": doc.hits,
                    "url": doc.url,
                    "source": doc.source,
                    "category": doc.category,
                    "created_at": doc.created_at,
                }
                for doc in recent_docs
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get recent documents: {str(e)}"
        )


@router.get("/documents/search")
def search_documents(
    db: Session = Depends(get_db),
    q: str = Query(..., description="Search query"),
    source: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    """문서 검색"""
    try:
        # 제목이나 내용에서 검색
        search_query = f"%{q}%"

        if source:
            results = db.execute(
                """
                SELECT title, writer, date, hits, url, source, category, created_at
                FROM extracted_doc 
                WHERE (title ILIKE :query OR content ILIKE :query) 
                AND source = :source
                ORDER BY created_at DESC 
                LIMIT :limit
            """,
                {"query": search_query, "source": source, "limit": limit},
            ).fetchall()
        else:
            results = db.execute(
                """
                SELECT title, writer, date, hits, url, source, category, created_at
                FROM extracted_doc 
                WHERE title ILIKE :query OR content ILIKE :query
                ORDER BY created_at DESC 
                LIMIT :limit
            """,
                {"query": search_query, "limit": limit},
            ).fetchall()

        return {
            "query": q,
            "source": source,
            "results": [
                {
                    "title": doc.title,
                    "writer": doc.writer,
                    "date": doc.date,
                    "hits": doc.hits,
                    "url": doc.url,
                    "source": doc.source,
                    "category": doc.category,
                    "created_at": doc.created_at,
                }
                for doc in results
            ],
            "total_found": len(results),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/crawling-status")
def get_crawling_status(db: Session = Depends(get_db)):
    """크롤링 상태 및 통계 조회"""
    try:
        # 작업별 상태
        job_status = db.execute(
            """
            SELECT 
                name, status, created_at, last_run_at,
                (SELECT COUNT(*) FROM crawl_task WHERE job_id = cj.id) as task_count,
                (SELECT COUNT(*) FROM extracted_doc WHERE job_id = cj.id) as doc_count
            FROM crawl_job cj
            ORDER BY created_at DESC
        """
        ).fetchall()

        # 최근 크롤링 활동
        recent_activity = db.execute(
            """
            SELECT 
                ct.job_id,
                cj.name as job_name,
                ct.status,
                ct.created_at,
                ct.completed_at
            FROM crawl_task ct
            JOIN crawl_job cj ON ct.job_id = cj.id
            ORDER BY ct.created_at DESC
            LIMIT 10
        """
        ).fetchall()

        return {
            "job_status": [
                {
                    "name": job.name,
                    "status": job.status,
                    "created_at": job.created_at,
                    "last_run_at": job.last_run_at,
                    "task_count": job.task_count,
                    "doc_count": job.doc_count,
                }
                for job in job_status
            ],
            "recent_activity": [
                {
                    "job_id": activity.job_id,
                    "job_name": activity.job_name,
                    "status": activity.status,
                    "created_at": activity.created_at,
                    "completed_at": activity.completed_at,
                }
                for activity in recent_activity
            ],
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get crawling status: {str(e)}"
        )
