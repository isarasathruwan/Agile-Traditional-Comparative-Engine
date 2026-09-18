"""A small cross-worker rate limiter for a shared Gemini API key."""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path

from app.config.config import settings

logger = logging.getLogger(__name__)


class GeminiRequestLimiter:
    """Reserve Gemini request slots across the local worker processes.

    The document and traditional-advisor workers mount the same document volume, so
    this lock file serializes their calls without requiring another service.  A
    value of zero intentionally disables throttling for controlled test setups.
    """

    def __init__(self) -> None:
        self.path = Path(settings.assessment_documents_dir) / ".gemini-request-slot"

    def wait_for_slot(self, operation: str) -> None:
        interval = settings.gemini_min_request_interval_seconds
        if interval <= 0:
            return

        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a+", encoding="utf-8") as lock_file:
            # Docker and the supported deployment target are Linux. Importing here
            # keeps non-Linux unit-test imports harmless.
            import fcntl

            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                lock_file.seek(0)
                try:
                    next_allowed = float(lock_file.read().strip() or 0)
                except ValueError:
                    next_allowed = 0
                wait_seconds = max(0.0, next_allowed - time.time())
                if wait_seconds:
                    logger.info(
                        "Gemini request throttled operation=%s wait_seconds=%.1f",
                        operation,
                        wait_seconds,
                    )
                    time.sleep(wait_seconds)
                lock_file.seek(0)
                lock_file.truncate()
                lock_file.write(str(time.time() + interval))
                lock_file.flush()
                os.fsync(lock_file.fileno())
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
