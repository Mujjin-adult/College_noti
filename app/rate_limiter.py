import time
import asyncio
from typing import Dict, Optional, Set
from dataclasses import dataclass
from collections import defaultdict, deque
import logging
from urllib.parse import urlparse
import threading
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """호스트별 레이트 리밋 설정"""

    qps_limit: float = 1.0  # 초당 요청 수
    concurrency_limit: int = 1  # 동시 요청 수
    daily_budget_sec_browser: int = 3600  # 일일 브라우저 사용 시간 (초)
    burst_limit: int = 5  # 버스트 허용 요청 수


class TokenBucket:
    """토큰 버킷 알고리즘으로 QPS 제한"""

    def __init__(self, rate: float, capacity: int = 10):
        self.rate = rate  # 토큰 생성 속도 (초당)
        self.capacity = capacity  # 버킷 용량
        self.tokens = capacity  # 현재 토큰 수
        self.last_update = time.time()
        self._lock = threading.Lock()

    def consume(self, tokens: int = 1) -> bool:
        """토큰 소비 시도"""
        with self._lock:
            now = time.time()
            # 시간 경과에 따른 토큰 생성
            time_passed = now - self.last_update
            new_tokens = time_passed * self.rate
            self.tokens = min(self.capacity, self.tokens + new_tokens)
            self.last_update = now

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    def wait_for_tokens(self, tokens: int = 1, timeout: float = 60.0) -> bool:
        """토큰이 사용 가능할 때까지 대기"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.consume(tokens):
                return True
            time.sleep(0.1)  # 100ms 대기
        return False


class SemaphoreManager:
    """호스트별 동시성 제어를 위한 세마포어 관리"""

    def __init__(self):
        self.semaphores: Dict[str, asyncio.Semaphore] = {}
        self._lock = threading.Lock()

    def get_semaphore(self, host: str, limit: int) -> asyncio.Semaphore:
        """호스트별 세마포어 반환"""
        with self._lock:
            if host not in self.semaphores:
                self.semaphores[host] = asyncio.Semaphore(limit)
            return self.semaphores[host]

    def update_semaphore(self, host: str, limit: int):
        """세마포어 제한 업데이트"""
        with self._lock:
            if host in self.semaphores:
                # 기존 세마포어 제거
                del self.semaphores[host]
            # 새로운 세마포어 생성
            self.semaphores[host] = asyncio.Semaphore(limit)


class RateLimiter:
    """호스트별 레이트 리미팅 및 동시성 제어"""

    def __init__(self):
        self.token_buckets: Dict[str, TokenBucket] = {}
        self.semaphore_manager = SemaphoreManager()
        self.active_requests: Dict[str, Set[str]] = defaultdict(set)
        self.daily_usage: Dict[str, int] = defaultdict(int)  # 초 단위
        self.last_reset = time.time()
        self._lock = threading.Lock()

        # 기본 설정
        self.default_config = RateLimitConfig()

    def _get_host(self, url: str) -> str:
        """URL에서 호스트 추출"""
        return urlparse(url).netloc

    def _reset_daily_usage_if_needed(self):
        """일일 사용량 초기화 (자정)"""
        now = time.time()
        if now - self.last_reset >= 86400:  # 24시간
            with self._lock:
                self.daily_usage.clear()
                self.last_reset = now

    def set_host_config(self, host: str, config: RateLimitConfig):
        """호스트별 설정 업데이트"""
        with self._lock:
            # 토큰 버킷 업데이트
            self.token_buckets[host] = TokenBucket(config.qps_limit, config.burst_limit)

            # 세마포어 업데이트
            self.semaphore_manager.update_semaphore(host, config.concurrency_limit)

            logger.info(
                f"Updated rate limit config for {host}: QPS={config.qps_limit}, "
                f"Concurrency={config.concurrency_limit}"
            )

    def get_host_config(self, host: str) -> RateLimitConfig:
        """호스트별 설정 반환 (기본값 사용)"""
        # TODO: 데이터베이스에서 설정 조회
        return self.default_config

    def can_make_request(self, url: str) -> bool:
        """요청 가능 여부 확인"""
        host = self._get_host(url)
        self._reset_daily_usage_if_needed()

        # 일일 예산 확인
        config = self.get_host_config(host)
        if self.daily_usage[host] >= config.daily_budget_sec_browser:
            logger.warning(f"Daily budget exceeded for {host}")
            return False

        # 토큰 버킷 확인
        if host in self.token_buckets:
            return self.token_buckets[host].consume()

        return True

    def wait_for_request(self, url: str, timeout: float = 60.0) -> bool:
        """요청 가능할 때까지 대기"""
        host = self._get_host(url)

        if host in self.token_buckets:
            return self.token_buckets[host].wait_for_tokens(timeout=timeout)

        return True

    @asynccontextmanager
    async def acquire_semaphore(self, url: str):
        """동시성 제어를 위한 세마포어 획득"""
        host = self._get_host(url)
        config = self.get_host_config(host)

        semaphore = self.semaphore_manager.get_semaphore(host, config.concurrency_limit)

        try:
            await semaphore.acquire()
            logger.debug(f"Acquired semaphore for {host}")
            yield
        finally:
            semaphore.release()
            logger.debug(f"Released semaphore for {host}")

    def record_request_start(self, url: str, request_id: str):
        """요청 시작 기록"""
        host = self._get_host(url)
        with self._lock:
            self.active_requests[host].add(request_id)

    def record_request_end(self, url: str, request_id: str, browser_time: int = 0):
        """요청 종료 기록"""
        host = self._get_host(url)
        self._reset_daily_usage_if_needed()

        with self._lock:
            if request_id in self.active_requests[host]:
                self.active_requests[host].remove(request_id)

            # 브라우저 사용 시간 기록
            if browser_time > 0:
                self.daily_usage[host] += browser_time

    def get_host_stats(self, host: str) -> Dict:
        """호스트별 통계 정보"""
        self._reset_daily_usage_if_needed()

        config = self.get_host_config(host)
        active_count = len(self.active_requests[host])
        daily_usage = self.daily_usage[host]

        return {
            "host": host,
            "qps_limit": config.qps_limit,
            "concurrency_limit": config.concurrency_limit,
            "active_requests": active_count,
            "daily_usage_sec": daily_usage,
            "daily_budget_sec": config.daily_budget_sec_browser,
            "budget_usage_percent": (
                (daily_usage / config.daily_budget_sec_browser * 100)
                if config.daily_budget_sec_browser > 0
                else 0
            ),
        }

    def get_all_host_stats(self) -> Dict[str, Dict]:
        """모든 호스트의 통계 정보"""
        stats = {}
        for host in set(
            list(self.token_buckets.keys()) + list(self.active_requests.keys())
        ):
            stats[host] = self.get_host_stats(host)
        return stats

    def is_host_overloaded(self, host: str) -> bool:
        """호스트가 과부하 상태인지 확인"""
        stats = self.get_host_stats(host)
        return (
            stats["active_requests"] >= stats["concurrency_limit"]
            or stats["budget_usage_percent"] >= 90
        )

    def cleanup(self):
        """리소스 정리"""
        with self._lock:
            self.token_buckets.clear()
            self.active_requests.clear()
            self.daily_usage.clear()


# 전역 인스턴스
rate_limiter = RateLimiter()


def get_rate_limiter() -> RateLimiter:
    """전역 레이트 리미터 반환"""
    return rate_limiter
