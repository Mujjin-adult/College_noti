# College Notice Crawler

대학 공지사항을 수집하는 크롤링 시스템입니다.

## 주요 기능

- **크롤 잡 관리**: 잡 생성/조회/수정/취소, 우선순위(P0-P3), 예약(크론/일회성) 지원
- **스코프 지원**: 도메인 단위/URL 리스트 단위/사이트맵 단위/검색어 기반 동적 탐색
- **중복 방지**: URL canonicalization + 해시 기반 중복 체크
- **렌더링 옵션**: 정적(HTTP) + 동적(헤드리스 브라우저, Playwright) 선택
- **폴리트니스 & 컴플라이언스**: robots.txt 준수, 호스트별 레이트리밋
- **에러/재시도**: 네트워크/HTTP/렌더링 에러 유형화, 지수 백오프 + Jitter
- **데이터 저장**: 추출 결과와 원문 저장, 동일 URL의 스냅샷 버전링
- **스케줄러**: 주기적 리프레시, 우선 순위 큐 + 데드레터 큐(DLQ)
- **모니터링**: Celery Flower, Prometheus 메트릭, Sentry 에러 추적, Slack 알림

## 시스템 구성

- **FastAPI**: API 게이트웨이/관리 UI 백엔드
- **Celery + Redis**: 작업 큐(브로커=Redis, 결과백엔드=Redis)
- **PostgreSQL**: 메타데이터·결과 저장
- **Playwright**: Headless 브라우저 컨테이너
- **Sentry**: 예외/성능 트레이싱
- **Prometheus/Grafana**: 메트릭 수집 및 시각화
- **Slack**: 경보 채널

## 데이터 모델

### 주요 테이블

- `crawl_job`: 잡 정의 (우선순위, 스케줄, 시드 타입 등)
- `crawl_task`: 세부 작업/URL 단위 (상태, 재시도, 에러 등)
- `extracted_doc`: 추출된 문서 (원문, 추출 결과, 스냅샷 버전 등)
- `host_budget`: 호스트별 예산 관리 (QPS, 동시성, 브라우저 시간 등)
- `webhook`: 웹훅 설정 (잡 완료, 문서 준비, 에러 등)

## API 명세

- `POST /jobs`: 잡 생성
- `GET /jobs/{id}`: 잡 조회
- `POST /jobs/{id}/pause|resume|cancel`: 잡 상태 변경
- `POST /jobs/{id}/run`: 수동 트리거
- `GET /docs`: 추출 결과 검색
- `GET /health`: 헬스 체크
- `GET /metrics`: Prometheus 메트릭

## 설치 및 실행

1. **의존성 설치**

```bash
uv sync
```

2. **환경변수 설정**

```bash
cp .env.example .env
# .env 파일 편집
```

3. **Docker Compose로 실행**

```bash
docker-compose up -d
```

4. **마이그레이션 실행**

```bash
docker-compose exec fastapi alembic upgrade head
```

## 주의사항

- **AI 파서 기능 제거됨**: 이전 버전에 있던 LLM 기반 파서 생성 기능은 제거되었습니다.
- **수동 파싱**: 각 도메인별로 수동으로 파싱 로직을 구현해야 합니다.
- **스키마 관리**: JSONSchema 기반 스키마 정의 기능은 제거되었습니다.

## 라이센스

MIT License
