"""
대학 공지사항 크롤러 통합 모듈
college_code 폴더의 개별 크롤러들을 통합하여 관리
"""

import requests
from bs4 import BeautifulSoup
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import time
import random

logger = logging.getLogger(__name__)


class CollegeCrawler:
    """대학 공지사항 통합 크롤러"""

    def __init__(self):
        self.base_url = "https://www.inu.ac.kr"
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        )

    def crawl_volunteer(self, page_num: str = "253") -> List[Dict[str, Any]]:
        """봉사 크롤링"""
        try:
            url = f"{self.base_url}/bbs/inu/{page_num}/artclList.do"

            payload = {
                "layout": "Q0UK5PJj2ZsQo0aX2Frag0Mw8X0X3D",
                "menuNo": page_num,
                "page": "1",
            }

            response = self.session.post(url, data=payload)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            rows = soup.select("table.board-table tbody tr")

            result = []
            for row in rows:
                try:
                    a = row.select_one("a")
                    if not a:
                        continue

                    title = a.get_text(strip=True)
                    href = a.get("href", "")
                    full_url = (
                        f"{self.base_url}{href}" if href.startswith("/") else href
                    )

                    writer = row.select_one("td.td-write")
                    writer_text = writer.get_text(strip=True) if writer else "N/A"

                    date = row.select_one("td.td-date")
                    date_text = date.get_text(strip=True) if date else "N/A"

                    hits = row.select_one("td.td-access")
                    hits_text = hits.get_text(strip=True) if hits else "N/A"

                    result.append(
                        {
                            "title": title,
                            "writer": writer_text,
                            "date": date_text,
                            "hits": hits_text,
                            "url": full_url,
                            "category": "봉사",
                            "source": "volunteer",
                        }
                    )
                except Exception as e:
                    logger.error(f"Error parsing volunteer row: {e}")
                    continue

            logger.info(f"Volunteer crawling completed: {len(result)} items")
            return result

        except Exception as e:
            logger.error(f"Error crawling volunteer: {e}")
            return []

    def crawl_job(self) -> List[Dict[str, Any]]:
        """취업 크롤링"""
        try:
            url = f"{self.base_url}/employment/inu/employmentlist.do"

            payload = {"page": "1"}

            response = self.session.post(url, data=payload)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            rows = soup.select("table tbody tr")

            result = []
            for row in rows:
                try:
                    a = row.select_one("a")
                    if not a:
                        continue

                    title = a.get_text(strip=True)
                    href = a.get("href", "")
                    full_url = (
                        f"{self.base_url}{href}" if href.startswith("/") else href
                    )

                    writer = row.select_one("td.td-write")
                    writer_text = writer.get_text(strip=True) if writer else "N/A"

                    date = row.select_one("td.td-date")
                    date_text = date.get_text(strip=True) if date else "N/A"

                    hits = row.select_one("td.td-access")
                    hits_text = hits.get_text(strip=True) if hits else "N/A"

                    category = row.select_one("td.td-category")
                    category_text = category.get_text(strip=True) if category else "N/A"

                    result.append(
                        {
                            "title": title,
                            "writer": writer_text,
                            "date": date_text,
                            "hits": hits_text,
                            "url": full_url,
                            "category": category_text,
                            "source": "job",
                        }
                    )
                except Exception as e:
                    logger.error(f"Error parsing job row: {e}")
                    continue

            logger.info(f"Job crawling completed: {len(result)} items")
            return result

        except Exception as e:
            logger.error(f"Error crawling job: {e}")
            return []

    def crawl_scholarship(self, page_num: str = "249") -> List[Dict[str, Any]]:
        """장학금 크롤링"""
        try:
            url = f"{self.base_url}/bbs/inu/{page_num}/artclList.do"

            payload = {
                "layout": "Q0UK5PJj2ZsQo0aX2Frag0Mw8X0X3D",
                "menuNo": page_num,
                "page": "1",
            }

            response = self.session.post(url, data=payload)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            rows = soup.select("table.board-table tbody tr")

            result = []
            for row in rows:
                try:
                    a = row.select_one("a")
                    if not a:
                        continue

                    title = a.get_text(strip=True)
                    href = a.get("href", "")
                    full_url = (
                        f"{self.base_url}{href}" if href.startswith("/") else href
                    )

                    writer = row.select_one("td.td-write")
                    writer_text = writer.get_text(strip=True) if writer else "N/A"

                    date = row.select_one("td.td-date")
                    date_text = date.get_text(strip=True) if date else "N/A"

                    hits = row.select_one("td.td-access")
                    hits_text = hits.get_text(strip=True) if hits else "N/A"

                    category = row.select_one("td.td-category")
                    category_text = category.get_text(strip=True) if category else "N/A"

                    result.append(
                        {
                            "title": title,
                            "writer": writer_text,
                            "date": date_text,
                            "hits": hits_text,
                            "url": full_url,
                            "category": category_text,
                            "source": "scholarship",
                        }
                    )
                except Exception as e:
                    logger.error(f"Error parsing scholarship row: {e}")
                    continue

            logger.info(f"Scholarship crawling completed: {len(result)} items")
            return result

        except Exception as e:
            logger.error(f"Error crawling scholarship: {e}")
            return []

    def crawl_general_events(self, page_num: str = "2611") -> List[Dict[str, Any]]:
        """일반행사/채용 크롤링"""
        try:
            url = f"{self.base_url}/bbs/inu/{page_num}/artclList.do"

            payload = {
                "layout": "Q0UK5PJj2ZsQo0aX2Frag0Mw8X0X3D",
                "menuNo": page_num,
                "page": "1",
            }

            response = self.session.post(url, data=payload)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            rows = soup.select("table.board-table tbody tr")

            result = []
            for row in rows:
                try:
                    a = row.select_one("a")
                    if not a:
                        continue

                    title = a.get_text(strip=True)
                    href = a.get("href", "")
                    full_url = (
                        f"{self.base_url}{href}" if href.startswith("/") else href
                    )

                    writer = row.select_one("td.td-write")
                    writer_text = writer.get_text(strip=True) if writer else "N/A"

                    date = row.select_one("td.td-date")
                    date_text = date.get_text(strip=True) if date else "N/A"

                    hits = row.select_one("td.td-access")
                    hits_text = hits.get_text(strip=True) if hits else "N/A"

                    category = row.select_one("td.td-category")
                    category_text = category.get_text(strip=True) if category else "N/A"

                    result.append(
                        {
                            "title": title,
                            "writer": writer_text,
                            "date": date_text,
                            "hits": hits_text,
                            "url": full_url,
                            "category": category_text,
                            "source": "general_events",
                        }
                    )
                except Exception as e:
                    logger.error(f"Error parsing general events row: {e}")
                    continue

            logger.info(f"General events crawling completed: {len(result)} items")
            return result

        except Exception as e:
            logger.error(f"Error crawling general events: {e}")
            return []

    def crawl_educational_test(self, page_num: str = "252") -> List[Dict[str, Any]]:
        """교육시험 크롤링"""
        try:
            url = f"{self.base_url}/bbs/inu/{page_num}/artclList.do"

            payload = {
                "layout": "Q0UK5PJj2ZsQo0aX2Frag0Mw8X0X3D",
                "menuNo": page_num,
                "page": "1",
            }

            response = self.session.post(url, data=payload)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            rows = soup.select("table.board-table tbody tr")

            result = []
            for row in rows:
                try:
                    a = row.select_one("a")
                    if not a:
                        continue

                    title = a.get_text(strip=True)
                    href = a.get("href", "")
                    full_url = (
                        f"{self.base_url}{href}" if href.startswith("/") else href
                    )

                    writer = row.select_one("td.td-write")
                    writer_text = writer.get_text(strip=True) if writer else "N/A"

                    date = row.select_one("td.td-date")
                    date_text = date.get_text(strip=True) if date else "N/A"

                    hits = row.select_one("td.td-access")
                    hits_text = hits.get_text(strip=True) if hits else "N/A"

                    result.append(
                        {
                            "title": title,
                            "writer": writer_text,
                            "date": date_text,
                            "hits": hits_text,
                            "url": full_url,
                            "category": "교육시험",
                            "source": "educational_test",
                        }
                    )
                except Exception as e:
                    logger.error(f"Error parsing educational test row: {e}")
                    continue

            logger.info(f"Educational test crawling completed: {len(result)} items")
            return result

        except Exception as e:
            logger.error(f"Error crawling educational test: {e}")
            return []

    def crawl_tuition_payment(self, page_num: str = "250") -> List[Dict[str, Any]]:
        """등록금납부 크롤링"""
        try:
            url = f"{self.base_url}/bbs/inu/{page_num}/artclList.do"

            payload = {
                "layout": "Q0UK5PJj2ZsQo0aX2Frag0Mw8X0X3D",
                "menuNo": page_num,
                "page": "1",
            }

            response = self.session.post(url, data=payload)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            rows = soup.select("table.board-table tbody tr")

            result = []
            for row in rows:
                try:
                    a = row.select_one("a")
                    if not a:
                        continue

                    title = a.get_text(strip=True)
                    href = a.get("href", "")
                    full_url = (
                        f"{self.base_url}{href}" if href.startswith("/") else href
                    )

                    writer = row.select_one("td.td-write")
                    writer_text = writer.get_text(strip=True) if writer else "N/A"

                    date = row.select_one("td.td-date")
                    date_text = date.get_text(strip=True) if date else "N/A"

                    hits = row.select_one("td.td-access")
                    hits_text = hits.get_text(strip=True) if hits else "N/A"

                    result.append(
                        {
                            "title": title,
                            "writer": writer_text,
                            "date": date_text,
                            "hits": hits_text,
                            "url": full_url,
                            "category": "등록금납부",
                            "source": "tuition_payment",
                        }
                    )
                except Exception as e:
                    logger.error(f"Error parsing tuition payment row: {e}")
                    continue

            logger.info(f"Tuition payment crawling completed: {len(result)} items")
            return result

        except Exception as e:
            logger.error(f"Error crawling tuition payment: {e}")
            return []

    def crawl_academic_credit(self, page_num: str = "247") -> List[Dict[str, Any]]:
        """학점 크롤링"""
        try:
            url = f"{self.base_url}/bbs/inu/{page_num}/artclList.do"

            payload = {
                "layout": "Q0UK5PJj2ZsQo0aX2Frag0Mw8X0X3D",
                "menuNo": page_num,
                "page": "1",
            }

            response = self.session.post(url, data=payload)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            rows = soup.select("table.board-table tbody tr")

            result = []
            for row in rows:
                try:
                    a = row.select_one("a")
                    if not a:
                        continue

                    title = a.get_text(strip=True)
                    href = a.get("href", "")
                    full_url = (
                        f"{self.base_url}{href}" if href.startswith("/") else href
                    )

                    writer = row.select_one("td.td-write")
                    writer_text = writer.get_text(strip=True) if writer else "N/A"

                    date = row.select_one("td.td-date")
                    date_text = date.get_text(strip=True) if date else "N/A"

                    hits = row.select_one("td.td-access")
                    hits_text = hits.get_text(strip=True) if hits else "N/A"

                    result.append(
                        {
                            "title": title,
                            "writer": writer_text,
                            "date": date_text,
                            "hits": hits_text,
                            "url": full_url,
                            "category": "학점",
                            "source": "academic_credit",
                        }
                    )
                except Exception as e:
                    logger.error(f"Error parsing academic credit row: {e}")
                    continue

            logger.info(f"Academic credit crawling completed: {len(result)} items")
            return result

        except Exception as e:
            logger.error(f"Error crawling academic credit: {e}")
            return []

    def crawl_degree(self, page_num: str = "246") -> List[Dict[str, Any]]:
        """학위 크롤링"""
        try:
            url = f"{self.base_url}/bbs/inu/{page_num}/artclList.do"

            payload = {
                "layout": "Q0UK5PJj2ZsQo0aX2Frag0Mw8X0X3D",
                "menuNo": page_num,
                "page": "1",
            }

            response = self.session.post(url, data=payload)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            rows = soup.select("table.board-table tbody tr")

            result = []
            for row in rows:
                try:
                    a = row.select_one("a")
                    if not a:
                        continue

                    title = a.get_text(strip=True)
                    href = a.get("href", "")
                    full_url = (
                        f"{self.base_url}{href}" if href.startswith("/") else href
                    )

                    writer = row.select_one("td.td-write")
                    writer_text = writer.get_text(strip=True) if writer else "N/A"

                    date = row.select_one("td.td-date")
                    date_text = date.get_text(strip=True) if date else "N/A"

                    hits = row.select_one("td.td-access")
                    hits_text = hits.get_text(strip=True) if hits else "N/A"

                    result.append(
                        {
                            "title": title,
                            "writer": writer_text,
                            "date": date_text,
                            "hits": hits_text,
                            "url": full_url,
                            "category": "학위",
                            "source": "degree",
                        }
                    )
                except Exception as e:
                    logger.error(f"Error parsing degree row: {e}")
                    continue

            logger.info(f"Degree crawling completed: {len(result)} items")
            return result

        except Exception as e:
            logger.error(f"Error crawling degree: {e}")
            return []

    def crawl_all(self) -> Dict[str, List[Dict[str, Any]]]:
        """모든 카테고리 크롤링"""
        logger.info("Starting comprehensive college crawling...")

        results = {}

        # 각 카테고리별로 크롤링 (간격을 두어 서버 부하 방지)
        try:
            results["volunteer"] = self.crawl_volunteer()
            time.sleep(random.uniform(1, 3))  # 1-3초 대기

            results["job"] = self.crawl_job()
            time.sleep(random.uniform(1, 3))

            results["scholarship"] = self.crawl_scholarship()
            time.sleep(random.uniform(1, 3))

            results["general_events"] = self.crawl_general_events()
            time.sleep(random.uniform(1, 3))

            results["educational_test"] = self.crawl_educational_test()
            time.sleep(random.uniform(1, 3))

            results["tuition_payment"] = self.crawl_tuition_payment()
            time.sleep(random.uniform(1, 3))

            results["academic_credit"] = self.crawl_academic_credit()
            time.sleep(random.uniform(1, 3))

            results["degree"] = self.crawl_degree()

        except Exception as e:
            logger.error(f"Error in comprehensive crawling: {e}")

        total_items = sum(len(items) for items in results.values())
        logger.info(f"Comprehensive crawling completed: {total_items} total items")

        return results


# 전역 인스턴스
college_crawler = CollegeCrawler()


def get_college_crawler() -> CollegeCrawler:
    """크롤러 인스턴스 반환"""
    return college_crawler
