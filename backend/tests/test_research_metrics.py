from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config.database_config import Base
from app.entity.assessment_entity import AssessmentAnswerEntity, AssessmentResultEntity
from app.service.admin_service import AdminService


def _db_session():
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    return SessionLocal()


def test_research_metrics_shape_and_minimum_values():
    db = _db_session()
    now = datetime.utcnow()

    db.add(
        AssessmentResultEntity(
            submission_id=1,
            recommendation="Agile",
            agile_score=80.0,
            traditional_score=60.0,
            flexibility_score=4.0,
            performance_score=3.0,
            strictness_score=2.0,
            rationale="r1",
            decision_report={
                "strategy_profile": {
                    "hybrid_readiness": {"score": 72, "level": "high", "rationale": []},
                    "delivery_strategy": "agile_led_with_governance",
                    "strategy_options": [{"key": "safe", "label": "SAFe"}],
                }
            },
            rules_version=1,
            questionnaire_version=1,
            created_at=now,
        )
    )
    db.add(
        AssessmentResultEntity(
            submission_id=2,
            recommendation="Traditional",
            agile_score=50.0,
            traditional_score=85.0,
            flexibility_score=2.5,
            performance_score=4.0,
            strictness_score=4.5,
            rationale="r2",
            rules_version=1,
            questionnaire_version=1,
            created_at=now,
        )
    )
    db.add_all(
        [
            AssessmentAnswerEntity(submission_id=1, question_key="Q11", construct="FLEXIBILITY", value=4),
            AssessmentAnswerEntity(submission_id=1, question_key="Q12", construct="FLEXIBILITY", value=4),
            AssessmentAnswerEntity(submission_id=1, question_key="Q13", construct="FLEXIBILITY", value=4),
            AssessmentAnswerEntity(submission_id=2, question_key="Q11", construct="FLEXIBILITY", value=2),
            AssessmentAnswerEntity(submission_id=2, question_key="Q12", construct="FLEXIBILITY", value=3),
            AssessmentAnswerEntity(submission_id=2, question_key="Q13", construct="FLEXIBILITY", value=2),
        ]
    )
    db.commit()

    response = AdminService().get_research_metrics(db).data
    assert response is not None
    assert response.questionnaire_version == 1
    assert response.rules_version == 1
    assert response.sample_size == 2
    assert "FLEXIBILITY" in response.cronbach_alpha
    assert "flexibility_vs_agile" in response.correlations
    assert "flexibility_agile_vs_traditional" in response.t_tests
    assert "t_statistic" in response.t_tests["flexibility_agile_vs_traditional"]
    assert "overall" in response.dependent_variable_means
    assert "timeline_adherence" in response.dependent_variable_means["overall"]
    assert response.hybrid_readiness_distribution["high"] == 1
    assert response.delivery_strategy_distribution["agile_led_with_governance"] == 1
    assert response.strategy_option_counts["safe"] == 1
