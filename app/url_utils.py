import hashlib
import re
from urllib.parse import urlparse, urljoin, urlunparse, parse_qs, urlencode
from typing import Set, Optional, List
import logging

logger = logging.getLogger(__name__)


class URLNormalizer:
    """URL 정규화 및 중복 방지"""

    def __init__(self):
        # 제거할 쿼리 파라미터들 (일반적으로 불필요한 파라미터)
        self.remove_params = {
            "utm_source",
            "utm_medium",
            "utm_campaign",
            "utm_term",
            "utm_content",
            "fbclid",
            "gclid",
            "msclkid",
            "ref",
            "source",
            "campaign",
            "session_id",
            "timestamp",
            "cache",
            "v",
            "version",
        }

        # 정규화할 도메인별 규칙
        self.domain_rules = {
            "www.example.com": {
                "remove_params": ["page", "sort"],
                "force_https": True,
                "remove_fragment": True,
            }
        }

    def normalize_url(self, url: str, domain: Optional[str] = None) -> str:
        """URL 정규화"""
        try:
            parsed = urlparse(url)

            # 스키마 정규화
            if parsed.scheme in ["http", "https"]:
                scheme = "https" if self._should_force_https(domain) else parsed.scheme
            else:
                scheme = "https"

            # 도메인 정규화
            netloc = parsed.netloc.lower()
            if netloc.startswith("www."):
                netloc = netloc[4:]  # www 제거

            # 경로 정규화
            path = self._normalize_path(parsed.path)

            # 쿼리 파라미터 정규화
            query = self._normalize_query(parsed.query, domain)

            # 프래그먼트 정규화
            fragment = "" if self._should_remove_fragment(domain) else parsed.fragment

            # 정규화된 URL 조합
            normalized = urlunparse((scheme, netloc, path, "", query, fragment))

            logger.debug(f"Normalized URL: {url} -> {normalized}")
            return normalized

        except Exception as e:
            logger.error(f"Error normalizing URL {url}: {e}")
            return url

    def _should_force_https(self, domain: Optional[str]) -> bool:
        """HTTPS 강제 적용 여부"""
        if domain and domain in self.domain_rules:
            return self.domain_rules[domain].get("force_https", False)
        return False

    def _should_remove_fragment(self, domain: Optional[str]) -> bool:
        """프래그먼트 제거 여부"""
        if domain and domain in self.domain_rules:
            return self.domain_rules[domain].get("remove_fragment", False)
        return False

    def _normalize_path(self, path: str) -> str:
        """경로 정규화"""
        if not path:
            return "/"

        # 중복 슬래시 제거
        path = re.sub(r"/+", "/", path)

        # 끝에 슬래시 추가 (선택적)
        if not path.endswith("/") and "." not in path.split("/")[-1]:
            path += "/"

        return path

    def _normalize_query(self, query: str, domain: Optional[str]) -> str:
        """쿼리 파라미터 정규화"""
        if not query:
            return ""

        try:
            params = parse_qs(query)
            normalized_params = {}

            # 도메인별 규칙 적용
            domain_remove_params = set()
            if domain and domain in self.domain_rules:
                domain_remove_params = set(
                    self.domain_rules[domain].get("remove_params", [])
                )

            # 제거할 파라미터들
            all_remove_params = self.remove_params | domain_remove_params

            for key, values in params.items():
                if key.lower() not in all_remove_params:
                    # 값이 하나인 경우 리스트가 아닌 단일 값으로 저장
                    if len(values) == 1:
                        normalized_params[key] = values[0]
                    else:
                        normalized_params[key] = values

            if not normalized_params:
                return ""

            # 정렬된 쿼리 문자열 생성
            return urlencode(sorted(normalized_params.items()))

        except Exception as e:
            logger.error(f"Error normalizing query {query}: {e}")
            return query

    def get_domain(self, url: str) -> str:
        """URL에서 도메인 추출"""
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except Exception:
            return ""


class DuplicateChecker:
    """URL 중복 체크"""

    def __init__(self, storage_backend: Optional[str] = None):
        self.storage_backend = storage_backend or "memory"
        self.normalizer = URLNormalizer()

        if self.storage_backend == "memory":
            self._seen_urls: Set[str] = set()
        elif self.storage_backend == "redis":
            # TODO: Redis 백엔드 구현
            self._seen_urls: Set[str] = set()
        else:
            self._seen_urls: Set[str] = set()

    def is_duplicate(self, url: str) -> bool:
        """URL이 중복인지 확인"""
        normalized = self.normalizer.normalize_url(url)
        url_hash = self._get_url_hash(normalized)

        if self.storage_backend == "memory":
            return url_hash in self._seen_urls
        elif self.storage_backend == "redis":
            # TODO: Redis에서 확인
            return url_hash in self._seen_urls
        else:
            return url_hash in self._seen_urls

    def mark_as_seen(self, url: str):
        """URL을 방문된 것으로 표시"""
        normalized = self.normalizer.normalize_url(url)
        url_hash = self._get_url_hash(normalized)

        if self.storage_backend == "memory":
            self._seen_urls.add(url_hash)
        elif self.storage_backend == "redis":
            # TODO: Redis에 저장
            self._seen_urls.add(url_hash)
        else:
            self._seen_urls.add(url_hash)

    def _get_url_hash(self, url: str) -> str:
        """URL 해시 생성"""
        return hashlib.sha256(url.encode("utf-8")).hexdigest()

    def get_stats(self) -> dict:
        """중복 체크 통계"""
        return {
            "storage_backend": self.storage_backend,
            "total_urls_seen": len(self._seen_urls),
            "memory_usage_mb": len(self._seen_urls)
            * 64
            / (1024 * 1024),  # 대략적인 메모리 사용량
        }

    def clear(self):
        """모든 URL 기록 삭제"""
        self._seen_urls.clear()

    def export_urls(self) -> List[str]:
        """방문된 URL 목록 내보내기 (디버깅용)"""
        return list(self._seen_urls)


class URLExpander:
    """URL 확장 (사이트맵, 링크 추출 등)"""

    def __init__(self):
        self.normalizer = URLNormalizer()

    def expand_sitemap(self, sitemap_url: str) -> List[str]:
        """사이트맵에서 URL 목록 추출"""
        # TODO: XML 사이트맵 파싱 구현
        return []

    def expand_domain(self, domain: str, max_depth: int = 2) -> List[str]:
        """도메인에서 URL 목록 추출 (링크 크롤링)"""
        # TODO: 링크 크롤링 구현
        return []

    def extract_links_from_html(self, html: str, base_url: str) -> List[str]:
        """HTML에서 링크 추출"""
        import re

        # 간단한 정규식으로 링크 추출
        link_pattern = r'href=["\']([^"\']+)["\']'
        links = re.findall(link_pattern, html)

        # 절대 URL로 변환
        absolute_links = []
        for link in links:
            if link.startswith(("http://", "https://")):
                absolute_links.append(link)
            elif link.startswith("/"):
                parsed_base = urlparse(base_url)
                absolute_links.append(
                    f"{parsed_base.scheme}://{parsed_base.netloc}{link}"
                )
            elif not link.startswith(("#", "javascript:", "mailto:")):
                absolute_links.append(urljoin(base_url, link))

        return absolute_links


# 전역 인스턴스들
url_normalizer = URLNormalizer()
duplicate_checker = DuplicateChecker()
url_expander = URLExpander()


def get_url_normalizer() -> URLNormalizer:
    """전역 URL 정규화기 반환"""
    return url_normalizer


def get_duplicate_checker() -> DuplicateChecker:
    """전역 중복 체커 반환"""
    return duplicate_checker


def get_url_expander() -> URLExpander:
    """전역 URL 확장기 반환"""
    return url_expander
