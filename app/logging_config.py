import logging
import logging.handlers
import sys
import os
from pathlib import Path
from typing import Optional
from config import get_monitoring_config

# 로그 포맷터
DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DETAILED_FORMAT = (
    "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
)

# 로그 파일 경로
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# 로그 파일명
APP_LOG_FILE = LOG_DIR / "app.log"
ERROR_LOG_FILE = LOG_DIR / "error.log"
ACCESS_LOG_FILE = LOG_DIR / "access.log"
CRAWLER_LOG_FILE = LOG_DIR / "crawler.log"


class ColoredFormatter(logging.Formatter):
    """컬러 로그 포맷터"""

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",  # Reset
    }

    def format(self, record):
        # 로그 레벨에 따른 색상 적용
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"

        return super().format(record)


def setup_logging(
    log_level: Optional[str] = None,
    enable_console: bool = True,
    enable_file: bool = True,
    enable_rotation: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
):
    """로깅 시스템 설정"""

    # 설정에서 로그 레벨 가져오기
    if log_level is None:
        try:
            config = get_monitoring_config()
            log_level = config.get("log_level", "INFO")
        except Exception:
            log_level = "INFO"

    # 로그 레벨 파싱
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # 루트 로거 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # 기존 핸들러 제거
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # 포맷터 생성
    console_formatter = ColoredFormatter(DEFAULT_FORMAT)
    file_formatter = logging.Formatter(DETAILED_FORMAT)

    # 콘솔 핸들러
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

    # 파일 핸들러
    if enable_file:
        # 메인 애플리케이션 로그
        if enable_rotation:
            app_handler = logging.handlers.RotatingFileHandler(
                APP_LOG_FILE,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8",
            )
        else:
            app_handler = logging.FileHandler(APP_LOG_FILE, encoding="utf-8")

        app_handler.setLevel(numeric_level)
        app_handler.setFormatter(file_formatter)
        root_logger.addHandler(app_handler)

        # 에러 전용 로그
        error_handler = logging.handlers.RotatingFileHandler(
            ERROR_LOG_FILE,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        root_logger.addHandler(error_handler)

    # 특정 모듈별 로거 설정
    setup_module_loggers(
        numeric_level, enable_file, enable_rotation, max_bytes, backup_count
    )

    logging.info(f"Logging system initialized with level: {log_level}")
    logging.info(f"Log files directory: {LOG_DIR.absolute()}")


def setup_module_loggers(
    level: int,
    enable_file: bool,
    enable_rotation: bool,
    max_bytes: int,
    backup_count: int,
):
    """모듈별 로거 설정"""

    # 크롤러 로거
    crawler_logger = logging.getLogger("crawler")
    crawler_logger.setLevel(level)

    if enable_file:
        if enable_rotation:
            crawler_handler = logging.handlers.RotatingFileHandler(
                CRAWLER_LOG_FILE,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8",
            )
        else:
            crawler_handler = logging.FileHandler(CRAWLER_LOG_FILE, encoding="utf-8")

        crawler_handler.setLevel(level)
        crawler_handler.setFormatter(logging.Formatter(DETAILED_FORMAT))
        crawler_logger.addHandler(crawler_handler)

    # FastAPI 로거
    fastapi_logger = logging.getLogger("uvicorn")
    fastapi_logger.setLevel(level)

    # Celery 로거
    celery_logger = logging.getLogger("celery")
    celery_logger.setLevel(level)

    # SQLAlchemy 로거 (SQL 쿼리 로깅)
    sqlalchemy_logger = logging.getLogger("sqlalchemy.engine")
    sqlalchemy_logger.setLevel(logging.WARNING)  # SQL 쿼리는 WARNING 레벨 이상만

    # requests 로거 (HTTP 요청 로깅)
    requests_logger = logging.getLogger("urllib3")
    requests_logger.setLevel(logging.WARNING)  # HTTP 요청은 WARNING 레벨 이상만


def get_logger(name: str) -> logging.Logger:
    """모듈별 로거 반환"""
    return logging.getLogger(name)


def log_request(
    request_id: str, method: str, url: str, status_code: int, duration: float
):
    """HTTP 요청 로깅"""
    logger = get_logger("access")
    logger.info(
        f"Request {request_id} - {method} {url} - {status_code} - {duration:.3f}s"
    )


def log_crawler_event(
    event_type: str, url: str, status: str, details: Optional[str] = None
):
    """크롤러 이벤트 로깅"""
    logger = get_logger("crawler")
    message = f"Crawler {event_type} - {url} - {status}"
    if details:
        message += f" - {details}"

    if status == "SUCCESS":
        logger.info(message)
    elif status == "FAILED":
        logger.error(message)
    elif status == "BLOCKED":
        logger.warning(message)
    else:
        logger.debug(message)


def log_error(
    error: Exception, context: Optional[str] = None, extra: Optional[dict] = None
):
    """에러 로깅"""
    logger = get_logger("error")

    message = f"Error: {type(error).__name__}: {str(error)}"
    if context:
        message = f"{context} - {message}"

    if extra:
        extra_str = " - ".join([f"{k}={v}" for k, v in extra.items()])
        message += f" - {extra_str}"

    logger.error(message, exc_info=True)


def log_performance(operation: str, duration: float, details: Optional[dict] = None):
    """성능 로깅"""
    logger = get_logger("performance")

    message = f"Performance - {operation}: {duration:.3f}s"
    if details:
        details_str = " - ".join([f"{k}={v}" for k, v in details.items()])
        message += f" - {details_str}"

    if duration > 1.0:  # 1초 이상이면 WARNING
        logger.warning(message)
    else:
        logger.info(message)


def cleanup_logs(max_days: int = 30):
    """오래된 로그 파일 정리"""
    import time
    from pathlib import Path

    current_time = time.time()
    cutoff_time = current_time - (max_days * 24 * 60 * 60)

    for log_file in LOG_DIR.glob("*.log.*"):
        if log_file.stat().st_mtime < cutoff_time:
            try:
                log_file.unlink()
                logging.info(f"Removed old log file: {log_file}")
            except Exception as e:
                logging.error(f"Failed to remove old log file {log_file}: {e}")


# 기본 로깅 설정
def init_logging():
    """애플리케이션 시작 시 로깅 초기화"""
    try:
        setup_logging()
        logging.info("Logging system initialized successfully")
    except Exception as e:
        # 로깅 시스템 초기화 실패 시 기본 설정
        logging.basicConfig(
            level=logging.INFO,
            format=DEFAULT_FORMAT,
            handlers=[logging.StreamHandler(sys.stdout)],
        )
        logging.error(f"Failed to initialize logging system: {e}")


# 컨텍스트 매니저로 로그 레벨 임시 변경
class TemporaryLogLevel:
    """임시로 로그 레벨을 변경하는 컨텍스트 매니저"""

    def __init__(self, logger_name: str, level: int):
        self.logger_name = logger_name
        self.level = level
        self.original_level = None
        self.logger = None

    def __enter__(self):
        self.logger = logging.getLogger(self.logger_name)
        self.original_level = self.logger.level
        self.logger.setLevel(self.level)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.logger and self.original_level is not None:
            self.logger.setLevel(self.original_level)
