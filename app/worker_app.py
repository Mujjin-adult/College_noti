# worker_app.py
from tasks import celery_app

# Celery 앱을 외부에서 접근할 수 있도록 export
__all__ = ["celery_app"]
