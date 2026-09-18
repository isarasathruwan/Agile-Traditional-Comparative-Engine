from sqlalchemy import func, select
from sqlalchemy.orm import Session


# Two-key PostgreSQL advisory locks keep document-job locks isolated from any
# other advisory-lock use in the application.
DOCUMENT_JOB_LOCK_NAMESPACE = 77_201


def _supports_advisory_locks(db: Session) -> bool:
    return db.get_bind().dialect.name == "postgresql"


def acquire_document_job_lock(db: Session, job_id: int) -> None:
    """Hold a session lock for the complete lifetime of a worker job."""
    if not _supports_advisory_locks(db):
        return
    db.execute(select(func.pg_advisory_lock(DOCUMENT_JOB_LOCK_NAMESPACE, job_id))).scalar_one_or_none()


def release_document_job_lock(db: Session, job_id: int) -> None:
    if not _supports_advisory_locks(db):
        return
    db.execute(select(func.pg_advisory_unlock(DOCUMENT_JOB_LOCK_NAMESPACE, job_id))).scalar_one_or_none()


def document_job_has_live_worker(db: Session, job_id: int) -> bool:
    """Return true only when another PostgreSQL session owns the job lock.

    When no worker owns the lock, this transaction acquires it until the
    request ends. That closes the race between the safety check and deletion.
    Non-PostgreSQL test environments retain the conservative status-based
    behavior.
    """
    if not _supports_advisory_locks(db):
        return True
    acquired = bool(
        db.scalar(select(func.pg_try_advisory_xact_lock(DOCUMENT_JOB_LOCK_NAMESPACE, job_id)))
    )
    return not acquired
