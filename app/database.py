from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
import logging

from config import get_database_url
from models import Base

logger = logging.getLogger(__name__)

# 환경변수에서 데이터베이스 URL 가져오기
DATABASE_URL = get_database_url()

# 엔진 생성 (커넥션 풀 설정 포함)
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# 세션 팩토리 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """데이터베이스 세션을 반환하는 제너레이터"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """컨텍스트 매니저로 데이터베이스 세션 관리"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def create_tables():
    """모든 테이블 생성"""
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """모든 테이블 삭제 (개발용)"""
    Base.metadata.drop_all(bind=engine)


def init_database():
    """데이터베이스 초기화"""
    try:
        create_tables()
        print("Database tables created successfully")
        return True
    except Exception as e:
        print(f"Failed to create database tables: {e}")
        return False
