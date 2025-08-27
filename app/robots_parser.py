import requests
from urllib.parse import urlparse, urljoin
from typing import Dict, List, Optional, Set
import time
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class RobotsPolicy(Enum):
    ALLOW = "ALLOW"
    DISALLOW = "DISALLOW"
    UNKNOWN = "UNKNOWN"


@dataclass
class RobotsRule:
    user_agent: str
    policy: RobotsPolicy
    path: str
    crawl_delay: Optional[float] = None


class RobotsParser:
    """robots.txt 파싱 및 준수 로직"""

    def __init__(self, base_url: str, user_agent: str = "*"):
        self.base_url = base_url
        self.user_agent = user_agent
        self.rules: List[RobotsRule] = []
        self.sitemaps: List[str] = []
        self.last_accessed: Optional[float] = None
        self._parsed = False

    def parse(self) -> bool:
        """robots.txt 파싱"""
        try:
            robots_url = urljoin(self.base_url, "/robots.txt")

            # robots.txt 요청
            headers = {"User-Agent": self.user_agent}
            response = requests.get(robots_url, headers=headers, timeout=10)

            if response.status_code != 200:
                logger.warning(f"robots.txt not found or error: {response.status_code}")
                return False

            self._parse_content(response.text)
            self._parsed = True
            self.last_accessed = time.time()
            return True

        except Exception as e:
            logger.error(f"Error parsing robots.txt: {e}")
            return False

    def _parse_content(self, content: str):
        """robots.txt 내용 파싱"""
        current_user_agent = None
        current_crawl_delay = None

        for line in content.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if ":" not in line:
                continue

            directive, value = line.split(":", 1)
            directive = directive.strip().lower()
            value = value.strip()

            if directive == "user-agent":
                current_user_agent = value
                current_crawl_delay = None
            elif directive == "disallow":
                if current_user_agent in ["*", self.user_agent]:
                    self.rules.append(
                        RobotsRule(
                            user_agent=current_user_agent,
                            policy=RobotsPolicy.DISALLOW,
                            path=value,
                            crawl_delay=current_crawl_delay,
                        )
                    )
            elif directive == "allow":
                if current_user_agent in ["*", self.user_agent]:
                    self.rules.append(
                        RobotsRule(
                            user_agent=current_user_agent,
                            policy=RobotsPolicy.ALLOW,
                            path=value,
                            crawl_delay=current_crawl_delay,
                        )
                    )
            elif directive == "crawl-delay":
                if current_user_agent in ["*", self.user_agent]:
                    try:
                        current_crawl_delay = float(value)
                    except ValueError:
                        logger.warning(f"Invalid crawl-delay value: {value}")
            elif directive == "sitemap":
                self.sitemaps.append(value)

    def is_allowed(self, url: str) -> bool:
        """URL이 robots.txt 규칙에 따라 허용되는지 확인"""
        if not self._parsed:
            if not self.parse():
                return True  # 파싱 실패 시 기본적으로 허용

        parsed_url = urlparse(url)
        path = parsed_url.path

        # 기본적으로 허용
        result = True

        for rule in self.rules:
            if rule.user_agent in ["*", self.user_agent]:
                if path.startswith(rule.path):
                    if rule.policy == RobotsPolicy.DISALLOW:
                        result = False
                    elif rule.policy == RobotsPolicy.ALLOW:
                        result = True

        return result

    def get_crawl_delay(self) -> float:
        """현재 User-Agent에 대한 crawl-delay 반환"""
        if not self._parsed:
            return 0.0

        for rule in self.rules:
            if rule.user_agent in ["*", self.user_agent] and rule.crawl_delay:
                return rule.crawl_delay

        return 0.0

    def get_sitemaps(self) -> List[str]:
        """sitemap URL 목록 반환"""
        if not self._parsed:
            self.parse()
        return self.sitemaps.copy()

    def should_respect_delay(self) -> bool:
        """crawl-delay를 준수해야 하는지 확인"""
        if not self.last_accessed:
            return False

        delay = self.get_crawl_delay()
        if delay <= 0:
            return False

        elapsed = time.time() - self.last_accessed
        return elapsed < delay

    def wait_if_needed(self):
        """필요한 경우 crawl-delay만큼 대기"""
        if self.should_respect_delay():
            delay = self.get_crawl_delay()
            logger.info(f"Respecting robots.txt crawl-delay: {delay}s")
            time.sleep(delay)
            self.last_accessed = time.time()


class RobotsManager:
    """여러 도메인의 robots.txt 관리"""

    def __init__(self):
        self.parsers: Dict[str, RobotsParser] = {}
        self.cache_ttl = 3600  # 1시간

    def get_parser(self, url: str, user_agent: str = "*") -> RobotsParser:
        """URL에 대한 robots.txt 파서 반환"""
        domain = urlparse(url).netloc

        if domain not in self.parsers:
            self.parsers[domain] = RobotsParser(f"https://{domain}", user_agent)

        parser = self.parsers[domain]

        # 캐시 만료 확인
        if (
            parser.last_accessed
            and (time.time() - parser.last_accessed) > self.cache_ttl
        ):
            parser._parsed = False

        return parser

    def is_allowed(self, url: str, user_agent: str = "*") -> bool:
        """URL이 robots.txt 규칙에 따라 허용되는지 확인"""
        parser = self.get_parser(url, user_agent)
        return parser.is_allowed(url)

    def wait_if_needed(self, url: str, user_agent: str = "*"):
        """필요한 경우 crawl-delay만큼 대기"""
        parser = self.get_parser(url, user_agent)
        parser.wait_if_needed()

    def get_sitemaps(self, url: str, user_agent: str = "*") -> List[str]:
        """도메인의 sitemap URL 목록 반환"""
        parser = self.get_parser(url, user_agent)
        return parser.get_sitemaps()

    def clear_cache(self, domain: Optional[str] = None):
        """캐시 정리"""
        if domain:
            if domain in self.parsers:
                del self.parsers[domain]
        else:
            self.parsers.clear()
