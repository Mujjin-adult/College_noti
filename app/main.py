from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import time
import uuid
from contextlib import asynccontextmanager
from fastapi.responses import HTMLResponse

from api import router as api_router
from logging_config import init_logging, log_request
from database import init_database
from config import get_settings, validate_settings
from auto_scheduler import init_college_scheduler

# 로깅 시스템 초기화
init_logging()

# 설정 유효성 검사
try:
    validate_settings()
except Exception as e:
    print(f"Configuration validation failed: {e}")
    raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # 시작 시
    print("Starting College Notice Crawler...")

    # 데이터베이스 초기화
    if init_database():
        print("Database initialized successfully")
    else:
        print("Database initialization failed")

    # 대학 크롤링 스케줄러 초기화
    if init_college_scheduler():
        print("College scheduler initialized successfully")
    else:
        print("College scheduler initialization failed")

    print("Application startup completed")

    yield

    # 종료 시
    print("Shutting down College Notice Crawler...")


# FastAPI 앱 생성
app = FastAPI(
    title="College Notice Crawler API",
    description="대학 공지사항을 수집하는 크롤링 시스템",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 미들웨어
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 신뢰할 수 있는 호스트 미들웨어
app.add_middleware(
    TrustedHostMiddleware, allowed_hosts=["*"]  # 프로덕션에서는 특정 호스트만 허용
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """요청 처리 시간 측정 및 로깅"""
    request_id = str(uuid.uuid4())
    start_time = time.time()

    # 요청 시작 로깅
    print(f"Request {request_id} started: {request.method} {request.url}")

    response = await call_next(request)

    # 요청 완료 로깅
    process_time = time.time() - start_time
    log_request(
        request_id, request.method, str(request.url), response.status_code, process_time
    )

    response.headers["X-Process-Time"] = str(process_time)
    response.headers["X-Request-ID"] = request_id

    return response


# API 라우터 등록
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "College Notice Crawler API",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy", "timestamp": time.time()}


@app.get("/test-crawlers")
async def test_crawlers():
    """크롤러 테스트 엔드포인트"""
    from auto_scheduler import get_auto_scheduler

    try:
        scheduler = get_auto_scheduler()
        results = scheduler.test_crawlers()
        return {
            "status": "success",
            "message": "Crawler test completed",
            "results": results,
        }
    except Exception as e:
        return {"status": "error", "message": f"Crawler test failed: {str(e)}"}


@app.post("/run-crawler/{category}")
async def run_crawler(category: str):
    """특정 카테고리 크롤러 수동 실행"""
    from college_crawlers import get_college_crawler

    try:
        crawler = get_college_crawler()

        if category == "volunteer":
            results = crawler.crawl_volunteer()
        elif category == "job":
            results = crawler.crawl_job()
        elif category == "scholarship":
            results = crawler.crawl_scholarship()
        elif category == "general_events":
            results = crawler.crawl_general_events()
        elif category == "educational_test":
            results = crawler.crawl_educational_test()
        elif category == "tuition_payment":
            results = crawler.crawl_tuition_payment()
        elif category == "academic_credit":
            results = crawler.crawl_academic_credit()
        elif category == "degree":
            results = crawler.crawl_degree()
        elif category == "all":
            results = crawler.crawl_all()
        else:
            return {"status": "error", "message": f"Unknown category: {category}"}

        return {
            "status": "success",
            "category": category,
            "results": results,
            "count": len(results) if isinstance(results, list) else "N/A",
        }

    except Exception as e:
        return {"status": "error", "message": f"Crawler execution failed: {str(e)}"}


@app.post("/force-schedule-update")
async def force_schedule_update():
    """Celery 스케줄 강제 업데이트"""
    from auto_scheduler import get_auto_scheduler

    try:
        scheduler = get_auto_scheduler()
        scheduler.update_celery_schedule()
        return {"status": "success", "message": "Schedule updated successfully"}
    except Exception as e:
        return {"status": "error", "message": f"Schedule update failed: {str(e)}"}


@app.get("/dashboard")
async def dashboard():
    """크롤링 데이터 대시보드"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>대학 공지사항 크롤링 대시보드</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { background: #f0f0f0; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
            .section { background: white; padding: 20px; margin-bottom: 20px; border: 1px solid #ddd; border-radius: 5px; }
            .button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 3px; cursor: pointer; margin: 5px; }
            .button:hover { background: #0056b3; }
            .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }
            .stat-card { background: #f8f9fa; padding: 20px; border-radius: 5px; text-align: center; }
            .stat-number { font-size: 2em; font-weight: bold; color: #007bff; }
            .data-table { width: 100%; border-collapse: collapse; margin-top: 10px; }
            .data-table th, .data-table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            .data-table th { background-color: #f2f2f2; }
            .search-box { width: 300px; padding: 8px; margin: 10px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏫 대학 공지사항 크롤링 대시보드</h1>
                <p>인천대학교 공지사항 크롤링 현황 및 데이터 조회</p>
            </div>
            
            <div class="section">
                <h2>📊 크롤링 통계</h2>
                <div class="stats">
                    <div class="stat-card">
                        <div class="stat-number" id="total-docs">-</div>
                        <div>총 문서 수</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" id="total-jobs">-</div>
                        <div>크롤링 작업 수</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" id="active-jobs">-</div>
                        <div>활성 작업 수</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" id="latest-update">-</div>
                        <div>최근 업데이트</div>
                    </div>
                </div>
                <button class="button" onclick="loadStats()">통계 새로고침</button>
            </div>
            
            <div class="section">
                <h2>🔍 데이터 검색</h2>
                <input type="text" id="search-query" class="search-box" placeholder="검색어를 입력하세요...">
                <select id="search-source">
                    <option value="">모든 소스</option>
                    <option value="volunteer">봉사</option>
                    <option value="job">취업</option>
                    <option value="scholarship">장학금</option>
                    <option value="general_events">일반행사</option>
                    <option value="educational_test">교육시험</option>
                    <option value="tuition_payment">등록금납부</option>
                    <option value="academic_credit">학점</option>
                    <option value="degree">학위</option>
                </select>
                <button class="button" onclick="searchDocuments()">검색</button>
                <div id="search-results"></div>
            </div>
            
            <div class="section">
                <h2>📋 최근 크롤링된 문서</h2>
                <button class="button" onclick="loadRecentDocuments()">최근 문서 로드</button>
                <div id="recent-documents"></div>
            </div>
            
            <div class="section">
                <h2>⚙️ 크롤링 관리</h2>
                <button class="button" onclick="testCrawlers()">크롤러 테스트</button>
                <button class="button" onclick="updateSchedule()">스케줄 업데이트</button>
                <button class="button" onclick="runAllCrawlers()">전체 크롤링 실행</button>
                <div id="management-results"></div>
            </div>
        </div>
        
        <script>
            // 페이지 로드 시 통계 로드
            window.onload = function() {
                loadStats();
                loadRecentDocuments();
            };
            
            async function loadStats() {
                try {
                    const response = await fetch('/api/v1/documents/summary');
                    const data = await response.json();
                    
                    document.getElementById('total-docs').textContent = data.total_documents || 0;
                    document.getElementById('latest-update').textContent = data.latest_update ? new Date(data.latest_update).toLocaleDateString() : 'N/A';
                    
                    // 작업 상태도 로드
                    const statusResponse = await fetch('/api/v1/crawling-status');
                    const statusData = await statusResponse.json();
                    
                    document.getElementById('total-jobs').textContent = statusData.job_status?.length || 0;
                    document.getElementById('active-jobs').textContent = statusData.job_status?.filter(j => j.status === 'ACTIVE').length || 0;
                    
                } catch (error) {
                    console.error('통계 로드 실패:', error);
                }
            }
            
            async function loadRecentDocuments() {
                try {
                    const response = await fetch('/api/v1/documents/recent?limit=10');
                    const data = await response.json();
                    
                    const container = document.getElementById('recent-documents');
                    if (data.documents && data.documents.length > 0) {
                        let html = '<table class="data-table"><tr><th>제목</th><th>작성자</th><th>카테고리</th><th>소스</th><th>크롤링 시간</th></tr>';
                        data.documents.forEach(doc => {
                            html += `<tr>
                                <td><a href="${doc.url}" target="_blank">${doc.title}</a></td>
                                <td>${doc.writer}</td>
                                <td>${doc.category || 'N/A'}</td>
                                <td>${doc.source}</td>
                                <td>${new Date(doc.created_at).toLocaleString()}</td>
                            </tr>`;
                        });
                        html += '</table>';
                        container.innerHTML = html;
                    } else {
                        container.innerHTML = '<p>아직 크롤링된 문서가 없습니다.</p>';
                    }
                } catch (error) {
                    console.error('최근 문서 로드 실패:', error);
                    document.getElementById('recent-documents').innerHTML = '<p>문서 로드에 실패했습니다.</p>';
                }
            }
            
            async function searchDocuments() {
                const query = document.getElementById('search-query').value;
                const source = document.getElementById('search-source').value;
                
                if (!query) {
                    alert('검색어를 입력해주세요.');
                    return;
                }
                
                try {
                    let url = `/api/v1/documents/search?q=${encodeURIComponent(query)}`;
                    if (source) {
                        url += `&source=${encodeURIComponent(source)}`;
                    }
                    
                    const response = await fetch(url);
                    const data = await response.json();
                    
                    const container = document.getElementById('search-results');
                    if (data.results && data.results.length > 0) {
                        let html = `<h3>검색 결과 (${data.total_found}개)</h3>`;
                        html += '<table class="data-table"><tr><th>제목</th><th>작성자</th><th>카테고리</th><th>소스</th><th>크롤링 시간</th></tr>';
                        data.results.forEach(doc => {
                            html += `<tr>
                                <td><a href="${doc.url}" target="_blank">${doc.title}</a></td>
                                <td>${doc.writer}</td>
                                <td>${doc.category || 'N/A'}</td>
                                <td>${doc.source}</td>
                                <td>${new Date(doc.created_at).toLocaleString()}</td>
                            </tr>`;
                        });
                        html += '</table>';
                        container.innerHTML = html;
                    } else {
                        container.innerHTML = '<p>검색 결과가 없습니다.</p>';
                    }
                } catch (error) {
                    console.error('검색 실패:', error);
                    document.getElementById('search-results').innerHTML = '<p>검색에 실패했습니다.</p>';
                }
            }
            
            async function testCrawlers() {
                try {
                    const response = await fetch('/test-crawlers');
                    const data = await response.json();
                    
                    document.getElementById('management-results').innerHTML = 
                        `<h3>크롤러 테스트 결과</h3><pre>${JSON.stringify(data, null, 2)}</pre>`;
                } catch (error) {
                    document.getElementById('management-results').innerHTML = 
                        `<p>크롤러 테스트 실패: ${error.message}</p>`;
                }
            }
            
            async function updateSchedule() {
                try {
                    const response = await fetch('/force-schedule-update', {method: 'POST'});
                    const data = await response.json();
                    
                    document.getElementById('management-results').innerHTML = 
                        `<h3>스케줄 업데이트 결과</h3><pre>${JSON.stringify(data, null, 2)}</pre>`;
                } catch (error) {
                    document.getElementById('management-results').innerHTML = 
                        `<p>스케줄 업데이트 실패: ${error.message}</p>`;
                }
            }
            
            async function runAllCrawlers() {
                try {
                    const response = await fetch('/run-crawler/all', {method: 'POST'});
                    const data = await response.json();
                    
                    document.getElementById('management-results').innerHTML = 
                        `<h3>전체 크롤링 실행 결과</h3><pre>${JSON.stringify(data, null, 2)}</pre>`;
                    
                    // 잠시 후 통계와 최근 문서 새로고침
                    setTimeout(() => {
                        loadStats();
                        loadRecentDocuments();
                    }, 2000);
                } catch (error) {
                    document.getElementById('management-results').innerHTML = 
                        `<p>전체 크롤링 실행 실패: ${error.message}</p>`;
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)
