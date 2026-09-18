from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from app.config.config import settings
from app.config.database_config import Base, SessionLocal, engine
from app.config.logging_config import configure_logging
from app.config.middleware import auth_middleware, request_context_middleware
from app.controller import admin_controller, assessment_controller, questionnaire_controller, draft_controller
from app.entity import (
    admin_user_entity,
    assessment_entity,
    questionnaire_entity,
    rule_config_entity,
)
from app.entity import document_intelligence_entity  # noqa: F401
from app.entity import traditional_advisor_entity  # noqa: F401
from app.exceptions.handlers import register_exception_handlers
from app.service.auth_service import AuthService

app = FastAPI(title=settings.app_name, version="0.1.0")
configure_logging()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(assessment_controller.router, prefix="/api/v1/assessments", tags=["assessments"])
app.include_router(draft_controller.router, prefix="/api/v1/assessment-drafts", tags=["assessment-drafts"])
app.include_router(questionnaire_controller.router, prefix="/api/v1/questionnaire", tags=["questionnaire"])
app.include_router(admin_controller.router, prefix="/api/v1/admin", tags=["admin"])
app.middleware("http")(request_context_middleware)
app.middleware("http")(auth_middleware)

register_exception_handlers(app)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "methodalign-api"}


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        AuthService().seed_default_admin(db)
    finally:
        db.close()
