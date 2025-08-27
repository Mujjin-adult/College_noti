import os
from typing import Optional, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


class DatabaseSettings(BaseSettings):
    """데이터베이스 설정"""

    url: str = Field(
        default="postgresql://crawler:crawler123@postgres:5432/school_notices",
        env="DATABASE_URL",
    )
    pool_size: int = Field(default=10, env="DB_POOL_SIZE")
    max_overflow: int = Field(default=20, env="DB_MAX_OVERFLOW")
    pool_pre_ping: bool = Field(default=True, env="DB_POOL_PRE_PING")
    pool_recycle: int = Field(default=3600, env="DB_POOL_RECYCLE")


class RedisSettings(BaseSettings):
    """Redis 설정"""

    broker_url: str = Field(default="redis://redis:6379/0", env="CELERY_BROKER_URL")
    result_backend: str = Field(
        default="redis://redis:6379/0", env="CELERY_RESULT_BACKEND"
    )
    host: str = Field(default="redis", env="REDIS_HOST")
    port: int = Field(default=6379, env="REDIS_PORT")
    db: int = Field(default=0, env="REDIS_DB")
    password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")


class CrawlerSettings(BaseSettings):
    """크롤러 설정"""

    default_rate_limit_per_host: float = Field(
        default=1.0, env="DEFAULT_RATE_LIMIT_PER_HOST"
    )
    max_concurrent_requests_per_host: int = Field(
        default=2, env="MAX_CONCURRENT_REQUESTS_PER_HOST"
    )
    browser_timeout_seconds: int = Field(default=30, env="BROWSER_TIMEOUT_SECONDS")
    max_retries: int = Field(default=3, env="MAX_RETRIES")
    retry_delay_seconds: int = Field(default=5, env="RETRY_DELAY_SECONDS")
    respect_robots_txt: bool = Field(default=True, env="RESPECT_ROBOTS_TXT")
    user_agent: str = Field(
        default="Mozilla/5.0 (compatible; CollegeNotiBot/1.0)", env="USER_AGENT"
    )
    request_timeout: int = Field(default=30, env="REQUEST_TIMEOUT")
    max_content_length: int = Field(
        default=10 * 1024 * 1024, env="MAX_CONTENT_LENGTH"
    )  # 10MB


class PlaywrightSettings(BaseSettings):
    """Playwright 설정"""

    browser_type: str = Field(default="chromium", env="PLAYWRIGHT_BROWSER_TYPE")
    headless: bool = Field(default=True, env="PLAYWRIGHT_HEADLESS")
    viewport_width: int = Field(default=1920, env="PLAYWRIGHT_VIEWPORT_WIDTH")
    viewport_height: int = Field(default=1080, env="PLAYWRIGHT_VIEWPORT_HEIGHT")
    user_agent: str = Field(
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        env="PLAYWRIGHT_USER_AGENT",
    )
    timeout: int = Field(default=30000, env="PLAYWRIGHT_TIMEOUT")  # 30초
    wait_until: str = Field(default="networkidle", env="PLAYWRIGHT_WAIT_UNTIL")


class MonitoringSettings(BaseSettings):
    """모니터링 설정"""

    sentry_dsn: Optional[str] = Field(default=None, env="SENTRY_DSN")
    environment: str = Field(default="development", env="ENV")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    enable_prometheus: bool = Field(default=True, env="ENABLE_PROMETHEUS")
    metrics_port: int = Field(default=8000, env="METRICS_PORT")
    health_check_interval: int = Field(default=30, env="HEALTH_CHECK_INTERVAL")


class NotificationSettings(BaseSettings):
    """알림 설정"""

    slack_webhook_url: Optional[str] = Field(default=None, env="SLACK_WEBHOOK_URL")
    enable_slack_notifications: bool = Field(
        default=False, env="ENABLE_SLACK_NOTIFICATIONS"
    )
    notification_level: str = Field(default="ERROR", env="NOTIFICATION_LEVEL")
    webhook_timeout: int = Field(default=10, env="WEBHOOK_TIMEOUT")


class SecuritySettings(BaseSettings):
    """보안 설정"""

    enable_rate_limiting: bool = Field(default=True, env="ENABLE_RATE_LIMITING")
    enable_proxy_rotation: bool = Field(default=False, env="ENABLE_PROXY_ROTATION")
    proxy_list: Optional[str] = Field(default=None, env="PROXY_LIST")
    max_requests_per_minute: int = Field(default=60, env="MAX_REQUESTS_PER_MINUTE")
    block_suspicious_ips: bool = Field(default=True, env="BLOCK_SUSPICIOUS_IPS")


class Settings(BaseSettings):
    """전체 설정"""

    # 기본 설정
    app_name: str = Field(default="College Notice Crawler", env="APP_NAME")
    debug: bool = Field(default=False, env="DEBUG")
    secret_key: str = Field(default="your-secret-key-here", env="SECRET_KEY")

    # 하위 설정들
    database: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    crawler: CrawlerSettings = CrawlerSettings()
    playwright: PlaywrightSettings = PlaywrightSettings()
    monitoring: MonitoringSettings = MonitoringSettings()
    notification: NotificationSettings = NotificationSettings()
    security: SecuritySettings = SecuritySettings()

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """설정 인스턴스 반환 (캐시됨)"""
    return Settings()


def get_database_url() -> str:
    """데이터베이스 URL 반환"""
    settings = get_settings()
    return settings.database.url


def get_redis_url() -> str:
    """Redis URL 반환"""
    settings = get_settings()
    return settings.redis.broker_url


def get_crawler_config() -> Dict[str, Any]:
    """크롤러 설정 반환"""
    settings = get_settings()
    return {
        "rate_limit_per_host": settings.crawler.default_rate_limit_per_host,
        "max_concurrent_requests": settings.crawler.max_concurrent_requests_per_host,
        "browser_timeout": settings.crawler.browser_timeout_seconds,
        "max_retries": settings.crawler.max_retries,
        "retry_delay": settings.crawler.retry_delay_seconds,
        "respect_robots_txt": settings.crawler.respect_robots_txt,
        "user_agent": settings.crawler.user_agent,
        "request_timeout": settings.crawler.request_timeout,
        "max_content_length": settings.crawler.max_content_length,
    }


def get_playwright_config() -> Dict[str, Any]:
    """Playwright 설정 반환"""
    settings = get_settings()
    return {
        "browser_type": settings.playwright.browser_type,
        "headless": settings.playwright.headless,
        "viewport_width": settings.playwright.viewport_width,
        "viewport_height": settings.playwright.viewport_height,
        "user_agent": settings.playwright.user_agent,
        "timeout": settings.playwright.timeout,
        "wait_until": settings.playwright.wait_until,
    }


def get_monitoring_config() -> Dict[str, Any]:
    """모니터링 설정 반환"""
    settings = get_settings()
    return {
        "sentry_dsn": settings.monitoring.sentry_dsn,
        "environment": settings.monitoring.environment,
        "log_level": settings.monitoring.log_level,
        "enable_prometheus": settings.monitoring.enable_prometheus,
        "metrics_port": settings.monitoring.metrics_port,
        "health_check_interval": settings.monitoring.health_check_interval,
    }


def get_notification_config() -> Dict[str, Any]:
    """알림 설정 반환"""
    settings = get_settings()
    return {
        "slack_webhook_url": settings.notification.slack_webhook_url,
        "enable_slack_notifications": settings.notification.enable_slack_notifications,
        "notification_level": settings.notification.notification_level,
        "webhook_timeout": settings.notification.webhook_timeout,
    }


def get_security_config() -> Dict[str, Any]:
    """보안 설정 반환"""
    settings = get_settings()
    return {
        "enable_rate_limiting": settings.security.enable_rate_limiting,
        "enable_proxy_rotation": settings.security.enable_proxy_rotation,
        "proxy_list": settings.security.proxy_list,
        "max_requests_per_minute": settings.security.max_requests_per_minute,
        "block_suspicious_ips": settings.security.block_suspicious_ips,
    }


def validate_settings():
    """설정 유효성 검사"""
    try:
        settings = get_settings()

        # 필수 설정 검사
        if not settings.database.url:
            raise ValueError("DATABASE_URL is required")

        if not settings.redis.broker_url:
            raise ValueError("CELERY_BROKER_URL is required")

        # 크롤러 설정 검사
        if settings.crawler.default_rate_limit_per_host <= 0:
            raise ValueError("DEFAULT_RATE_LIMIT_PER_HOST must be positive")

        if settings.crawler.max_concurrent_requests_per_host <= 0:
            raise ValueError("MAX_CONCURRENT_REQUESTS_PER_HOST must be positive")

        # Playwright 설정 검사
        if settings.playwright.browser_type not in ["chromium", "firefox", "webkit"]:
            raise ValueError(
                "PLAYWRIGHT_BROWSER_TYPE must be one of: chromium, firefox, webkit"
            )

        logger.info("Settings validation passed")
        return True

    except Exception as e:
        logger.error(f"Settings validation failed: {e}")
        raise


def reload_settings():
    """설정 재로드 (캐시 무효화)"""
    get_settings.cache_clear()
    logger.info("Settings cache cleared, will reload on next access")
