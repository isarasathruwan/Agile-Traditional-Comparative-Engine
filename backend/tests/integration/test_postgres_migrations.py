import os

import pytest
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import inspect, text

from app.config.database_config import engine


pytestmark = pytest.mark.integration


@pytest.mark.skipif(os.getenv("RUN_POSTGRES_TESTS") != "1", reason="PostgreSQL integration database not requested")
def test_database_is_at_single_head_with_pgvector_and_seeded_configuration():
    config = Config("alembic.ini")
    script = ScriptDirectory.from_config(config)
    heads = script.get_heads()
    assert len(heads) == 1

    with engine.connect() as connection:
        context = MigrationContext.configure(connection)
        assert context.get_current_revision() == heads[0]
        assert connection.scalar(text("SELECT extversion FROM pg_extension WHERE extname = 'vector'"))
        assert connection.scalar(text("SELECT count(*) FROM questionnaire_versions")) >= 1
        assert connection.scalar(text("SELECT count(*) FROM rule_config_versions")) >= 1

    tables = set(inspect(engine).get_table_names())
    assert {
        "assessment_submissions",
        "assessment_drafts",
        "assessment_document_chunks",
        "assessment_document_processing_jobs",
    }.issubset(tables)
