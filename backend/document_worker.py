"""Single-worker process for the first production document-processing deployment."""

import logging
import time

from app.config.config import settings
from app.config.database_config import SessionLocal
from app.service.document_intelligence_service import DocumentIntelligenceService

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)


def main() -> None:
    service = DocumentIntelligenceService()
    logger.info("Document worker started")
    while True:
        db = SessionLocal()
        try:
            processed = service.process_next_job(db)
        except Exception:
            logger.exception("Unexpected document worker error")
            processed = False
        finally:
            db.close()
        if not processed:
            time.sleep(settings.document_worker_poll_seconds)


if __name__ == "__main__":
    main()
