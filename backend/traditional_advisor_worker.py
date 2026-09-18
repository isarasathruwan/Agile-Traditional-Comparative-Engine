import logging
import time

from app.config.config import settings
from app.config.database_config import SessionLocal
from app.service.traditional_advisor_service import TraditionalAdvisorService

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Traditional advisor worker started")
    service = TraditionalAdvisorService()
    while True:
        db = SessionLocal()
        try:
            if not service.process_next_job(db):
                time.sleep(settings.traditional_advisor_worker_poll_seconds)
        except Exception:
            logger.exception("Traditional advisor worker loop failed")
            time.sleep(settings.traditional_advisor_worker_poll_seconds)
        finally:
            db.close()
