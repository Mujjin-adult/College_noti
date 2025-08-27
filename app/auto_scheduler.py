"""
대학 공지사항 자동 크롤링 스케줄러
college_code의 크롤러들을 자동으로 등록하고 관리
"""

import logging
from typing import Dict, List, Any
from datetime import datetime, timedelta
from celery import current_app
from celery.schedules import crontab

from database import get_db_context
from crud import create_job, get_job_by_name, update_job_status
from models import JobStatus, SeedType, RenderMode, RobotsPolicy
from college_crawlers import get_college_crawler

logger = logging.getLogger(__name__)


class CollegeAutoScheduler:
    """대학 공지사항 자동 스케줄러"""

    def __init__(self):
        self.crawler = get_college_crawler()
        self.job_configs = self._get_job_configs()

    def _get_job_configs(self) -> List[Dict[str, Any]]:
        """크롤링 작업 설정 목록"""
        return [
            {
                "name": "봉사 공지사항 크롤링",
                "priority": "P1",
                "seed_type": SeedType.URL_LIST,
                "seed_payload": {
                    "urls": ["https://www.inu.ac.kr/bbs/inu/253/artclList.do"],
                    "category": "volunteer",
                    "page_num": "253",
                },
                "render_mode": RenderMode.STATIC,
                "robots_policy": RobotsPolicy.OBEY,
                "schedule_cron": "0 */2 * * *",  # 2시간마다
                "rate_limit_per_host": 0.5,  # 2초에 1회
                "max_depth": 1,
            },
            {
                "name": "취업 공지사항 크롤링",
                "priority": "P1",
                "seed_type": SeedType.URL_LIST,
                "seed_payload": {
                    "urls": ["https://www.inu.ac.kr/employment/inu/employmentlist.do"],
                    "category": "job",
                },
                "render_mode": RenderMode.STATIC,
                "robots_policy": RobotsPolicy.OBEY,
                "schedule_cron": "0 */3 * * *",  # 3시간마다
                "rate_limit_per_host": 0.5,
                "max_depth": 1,
            },
            {
                "name": "장학금 공지사항 크롤링",
                "priority": "P1",
                "seed_type": SeedType.URL_LIST,
                "seed_payload": {
                    "urls": ["https://www.inu.ac.kr/bbs/inu/249/artclList.do"],
                    "category": "scholarship",
                    "page_num": "249",
                },
                "render_mode": RenderMode.STATIC,
                "robots_policy": RobotsPolicy.OBEY,
                "schedule_cron": "0 */4 * * *",  # 4시간마다
                "rate_limit_per_host": 0.5,
                "max_depth": 1,
            },
            {
                "name": "일반행사/채용 크롤링",
                "priority": "P2",
                "seed_type": SeedType.URL_LIST,
                "seed_payload": {
                    "urls": ["https://www.inu.ac.kr/bbs/inu/2611/artclList.do"],
                    "category": "general_events",
                    "page_num": "2611",
                },
                "render_mode": RenderMode.STATIC,
                "robots_policy": RobotsPolicy.OBEY,
                "schedule_cron": "0 */6 * * *",  # 6시간마다
                "rate_limit_per_host": 0.5,
                "max_depth": 1,
            },
            {
                "name": "교육시험 크롤링",
                "priority": "P2",
                "seed_type": SeedType.URL_LIST,
                "seed_payload": {
                    "urls": ["https://www.inu.ac.kr/bbs/inu/252/artclList.do"],
                    "category": "educational_test",
                    "page_num": "252",
                },
                "render_mode": RenderMode.STATIC,
                "robots_policy": RobotsPolicy.OBEY,
                "schedule_cron": "0 */6 * * *",  # 6시간마다
                "rate_limit_per_host": 0.5,
                "max_depth": 1,
            },
            {
                "name": "등록금납부 크롤링",
                "priority": "P2",
                "seed_type": SeedType.URL_LIST,
                "seed_payload": {
                    "urls": ["https://www.inu.ac.kr/bbs/inu/250/artclList.do"],
                    "category": "tuition_payment",
                    "page_num": "250",
                },
                "render_mode": RenderMode.STATIC,
                "robots_policy": RobotsPolicy.OBEY,
                "schedule_cron": "0 */8 * * *",  # 8시간마다
                "rate_limit_per_host": 0.5,
                "max_depth": 1,
            },
            {
                "name": "학점 크롤링",
                "priority": "P2",
                "seed_type": SeedType.URL_LIST,
                "seed_payload": {
                    "urls": ["https://www.inu.ac.kr/bbs/inu/247/artclList.do"],
                    "category": "academic_credit",
                    "page_num": "247",
                },
                "render_mode": RenderMode.STATIC,
                "robots_policy": RobotsPolicy.OBEY,
                "schedule_cron": "0 */8 * * *",  # 8시간마다
                "rate_limit_per_host": 0.5,
                "max_depth": 1,
            },
            {
                "name": "학위 크롤링",
                "priority": "P2",
                "seed_type": SeedType.URL_LIST,
                "seed_payload": {
                    "urls": ["https://www.inu.ac.kr/bbs/inu/246/artclList.do"],
                    "category": "degree",
                    "page_num": "246",
                },
                "render_mode": RenderMode.STATIC,
                "robots_policy": RobotsPolicy.OBEY,
                "schedule_cron": "0 */8 * * *",  # 8시간마다
                "rate_limit_per_host": 0.5,
                "max_depth": 1,
            },
        ]

    def register_all_jobs(self) -> List[int]:
        """모든 크롤링 작업을 데이터베이스에 등록"""
        logger.info("Registering all college crawling jobs...")

        job_ids = []

        with get_db_context() as db:
            for config in self.job_configs:
                try:
                    # 기존 작업이 있는지 확인
                    existing_job = get_job_by_name(db, config["name"])

                    if existing_job:
                        logger.info(f"Job already exists: {config['name']}")
                        job_ids.append(existing_job.id)
                        continue

                    # 새 작업 생성
                    job_data = {
                        "name": config["name"],
                        "priority": config["priority"],
                        "seed_type": config["seed_type"],
                        "seed_payload": config["seed_payload"],
                        "render_mode": config["render_mode"],
                        "robots_policy": config["robots_policy"],
                        "schedule_cron": config["schedule_cron"],
                        "rate_limit_per_host": config["rate_limit_per_host"],
                        "max_depth": config["max_depth"],
                        "status": JobStatus.ACTIVE,
                    }

                    job = create_job(db, job_data)
                    job_ids.append(job.id)
                    logger.info(f"Created job: {config['name']} (ID: {job.id})")

                except Exception as e:
                    logger.error(f"Failed to create job {config['name']}: {e}")
                    continue

        logger.info(f"Registered {len(job_ids)} jobs")
        return job_ids

    def update_celery_schedule(self):
        """Celery Beat 스케줄 업데이트"""
        logger.info("Updating Celery Beat schedule...")

        try:
            # 기존 스케줄 제거
            current_app.conf.beat_schedule.clear()

            # 새로운 스케줄 추가
            for config in self.job_configs:
                schedule_name = f"college-{config['name'].replace(' ', '-').lower()}"

                # crontab 문자열을 파싱하여 crontab 객체 생성
                cron_parts = config["schedule_cron"].split()
                if len(cron_parts) == 5:
                    minute, hour, day, month, day_of_week = cron_parts
                    schedule_obj = crontab(
                        minute=minute,
                        hour=hour,
                        day_of_month=day,
                        month_of_year=month,
                        day_of_week=day_of_week,
                    )
                else:
                    # 기본값: 매시간
                    schedule_obj = crontab(minute=0, hour="*")

                current_app.conf.beat_schedule[schedule_name] = {
                    "task": "tasks.college_crawl_task",
                    "schedule": schedule_obj,
                    "args": (config["name"],),
                    "options": {
                        "priority": self._get_priority_value(config["priority"])
                    },
                }

                logger.info(
                    f"Added schedule: {schedule_name} - {config['schedule_cron']}"
                )

            logger.info("Celery Beat schedule updated successfully")

        except Exception as e:
            logger.error(f"Failed to update Celery Beat schedule: {e}")

    def _get_priority_value(self, priority: str) -> int:
        """우선순위 문자열을 숫자로 변환"""
        priority_map = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
        return priority_map.get(priority, 2)

    def test_crawlers(self) -> Dict[str, Any]:
        """크롤러 테스트 실행"""
        logger.info("Testing all college crawlers...")

        results = {}

        try:
            # 각 크롤러 개별 테스트
            results["volunteer"] = self.crawler.crawl_volunteer()
            results["job"] = self.crawler.crawl_job()
            results["scholarship"] = self.crawler.crawl_scholarship()

            # 통합 테스트
            results["comprehensive"] = self.crawler.crawl_all()

            # 결과 요약
            summary = {}
            for category, items in results.items():
                if isinstance(items, list):
                    summary[category] = len(items)
                elif isinstance(items, dict):
                    summary[category] = sum(
                        len(cat_items) for cat_items in items.values()
                    )

            results["summary"] = summary
            logger.info(f"Crawler test completed: {summary}")

        except Exception as e:
            logger.error(f"Error during crawler test: {e}")
            results["error"] = str(e)

        return results


# 전역 인스턴스
auto_scheduler = CollegeAutoScheduler()


def get_auto_scheduler() -> CollegeAutoScheduler:
    """자동 스케줄러 인스턴스 반환"""
    return auto_scheduler


def init_college_scheduler():
    """대학 크롤링 스케줄러 초기화"""
    try:
        scheduler = get_auto_scheduler()

        # 작업 등록
        job_ids = scheduler.register_all_jobs()

        # Celery 스케줄 업데이트
        scheduler.update_celery_schedule()

        logger.info(f"College scheduler initialized with {len(job_ids)} jobs")
        return True

    except Exception as e:
        logger.error(f"Failed to initialize college scheduler: {e}")
        return False
