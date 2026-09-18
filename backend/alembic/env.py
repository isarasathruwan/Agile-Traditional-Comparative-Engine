from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.config.config import settings
from app.config.database_config import Base
from app.entity.admin_user_entity import AdminUserEntity  # noqa: F401
from app.entity.assessment_entity import (  # noqa: F401
    AssessmentAnswerEntity,
    AssessmentResultEntity,
    AssessmentSubmissionEntity,
)
from app.entity.draft_entity import AssessmentDraftEntity, AssessmentDocumentEntity  # noqa: F401
from app.entity.document_intelligence_entity import (  # noqa: F401
    DocumentAgentRunEntity,
    DocumentChunkEntity,
    DocumentPageEntity,
    DocumentProcessingJobEntity,
    EvidenceAnswerEntity,
    EvidenceCitationEntity,
)
from app.entity.questionnaire_entity import QuestionnaireVersionEntity  # noqa: F401
from app.entity.rule_config_entity import RuleConfigVersionEntity  # noqa: F401
from app.entity.traditional_advisor_entity import TraditionalAdvisorEntity  # noqa: F401

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
