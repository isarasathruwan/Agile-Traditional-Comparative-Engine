from datetime import datetime

from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.config.auth_config import ROLE_PERMISSIONS, get_current_admin, require_permission
from app.config.database_config import get_db
from app.entity.admin_user_entity import AdminUserEntity
from app.model.admin_model import (
    AdminLoginData,
    AdminLoginRequest,
    AdminCurrentUserData,
    AdminUserCreateRequest,
    AdminUserData,
    AdminUserUpdateRequest,
    AiAnalyticsData,
    AssessmentDeleteData,
    IncompleteActivityData,
    IncompleteActivityResetRequest,
    DocumentProcessingRetryData,
    AssessmentWorkspaceAnalyticsData,
    AnalyticsSummaryData,
    AssessmentDetailData,
    AssessmentListItem,
    CompanyGroupItem,
    DistributionsData,
    ResearchMetricsData,
    RuleConfigData,
    RulePreviewData,
    RulePreviewRequest,
    RuleVersionActivateRequest,
    RuleConfigUpdateRequest,
    TrendsData,
)
from app.model.questionnaire_model import QuestionnaireData, QuestionnaireUpdateRequest
from app.model.traditional_advisor_model import TraditionalAdvisorData
from app.service.admin_service import AdminService
from app.service.admin_user_service import AdminUserService
from app.service.auth_service import AuthService
from app.service.questionnaire_service import QuestionnaireService
from app.service.rule_service import RuleService
from app.service.traditional_advisor_service import TraditionalAdvisorService
from app.util.response import GenericResponse, PaginatedResponse, apply_status_code

router = APIRouter()
auth_service = AuthService()
rule_service = RuleService()
admin_service = AdminService()
admin_user_service = AdminUserService()
questionnaire_service = QuestionnaireService()
traditional_advisor_service = TraditionalAdvisorService()


@router.post("/login", response_model=GenericResponse[AdminLoginData], status_code=200)
def admin_login(
    payload: AdminLoginRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> GenericResponse[AdminLoginData]:
    service_response = auth_service.login(db=db, payload=payload)
    return apply_status_code(response=response, payload=service_response)


@router.get("/me", response_model=GenericResponse[AdminCurrentUserData], status_code=200)
def get_current_admin_user(
    response: Response,
    user: AdminUserEntity = Depends(get_current_admin),
) -> GenericResponse[AdminCurrentUserData]:
    service_response = GenericResponse.success_response(
        "Current admin fetched.",
        data=AdminCurrentUserData(
            id=user.id,
            email=user.email,
            role=user.role,
            is_active=user.is_active,
            permissions=sorted(ROLE_PERMISSIONS.get(user.role, set())),
        ),
    )
    return apply_status_code(response=response, payload=service_response)


@router.get("/rules", response_model=GenericResponse[RuleConfigData], status_code=200)
def get_rules(
    response: Response,
    _: AdminUserEntity = Depends(require_permission("rules:read")),
    db: Session = Depends(get_db),
) -> GenericResponse[RuleConfigData]:
    service_response = rule_service.get_rule_payload(db=db)
    return apply_status_code(response=response, payload=service_response)


@router.put("/rules", response_model=GenericResponse[RuleConfigData], status_code=200)
def update_rules(
    payload: RuleConfigUpdateRequest,
    response: Response,
    user: AdminUserEntity = Depends(require_permission("rules:write")),
    db: Session = Depends(get_db),
) -> GenericResponse[RuleConfigData]:
    service_response = rule_service.update_rule_payload(db=db, payload=payload, changed_by=user.email)
    return apply_status_code(response=response, payload=service_response)


@router.post("/rules/preview", response_model=GenericResponse[RulePreviewData], status_code=200)
def preview_rules(
    payload: RulePreviewRequest,
    response: Response,
    _: AdminUserEntity = Depends(require_permission("rules:write")),
) -> GenericResponse[RulePreviewData]:
    service_response = rule_service.preview_rule_payload(payload=payload.payload)
    return apply_status_code(response=response, payload=service_response)


@router.get("/rules/versions", response_model=GenericResponse[list[RuleConfigData]], status_code=200)
def list_rule_versions(
    response: Response,
    _: AdminUserEntity = Depends(require_permission("rules:read")),
    db: Session = Depends(get_db),
) -> GenericResponse[list[RuleConfigData]]:
    service_response = rule_service.list_versions(db=db)
    return apply_status_code(response=response, payload=service_response)


@router.put("/rules/activate", response_model=GenericResponse[RuleConfigData], status_code=200)
def activate_rule_version(
    payload: RuleVersionActivateRequest,
    response: Response,
    user: AdminUserEntity = Depends(require_permission("rules:activate")),
    db: Session = Depends(get_db),
) -> GenericResponse[RuleConfigData]:
    service_response = rule_service.activate_version(db=db, version=payload.version, changed_by=user.email)
    return apply_status_code(response=response, payload=service_response)


@router.get("/analytics/summary", response_model=GenericResponse[AnalyticsSummaryData], status_code=200)
def analytics_summary(
    response: Response,
    _: AdminUserEntity = Depends(require_permission("analytics:read")),
    db: Session = Depends(get_db),
) -> GenericResponse[AnalyticsSummaryData]:
    service_response = admin_service.get_analytics_summary(db=db)
    return apply_status_code(response=response, payload=service_response)


@router.get("/analytics/research", response_model=GenericResponse[ResearchMetricsData], status_code=200)
def research_metrics(
    response: Response,
    questionnaire_version: int | None = Query(default=None, ge=1),
    rules_version: int | None = Query(default=None, ge=1),
    _: AdminUserEntity = Depends(require_permission("research:read")),
    db: Session = Depends(get_db),
) -> GenericResponse[ResearchMetricsData]:
    service_response = admin_service.get_research_metrics(
        db=db,
        questionnaire_version=questionnaire_version,
        rules_version=rules_version,
    )
    return apply_status_code(response=response, payload=service_response)


@router.get("/analytics/ai", response_model=GenericResponse[AiAnalyticsData], status_code=200)
def ai_analytics(
    response: Response,
    _: AdminUserEntity = Depends(require_permission("analytics:read")),
    db: Session = Depends(get_db),
) -> GenericResponse[AiAnalyticsData]:
    service_response = admin_service.get_ai_analytics(db=db)
    return apply_status_code(response=response, payload=service_response)


@router.get(
    "/assessments/analytics",
    response_model=GenericResponse[AssessmentWorkspaceAnalyticsData],
    status_code=200,
)
def assessment_workspace_analytics(
    response: Response,
    _: AdminUserEntity = Depends(require_permission("analytics:read")),
    db: Session = Depends(get_db),
) -> GenericResponse[AssessmentWorkspaceAnalyticsData]:
    service_response = admin_service.get_assessment_workspace_analytics(db=db)
    return apply_status_code(response=response, payload=service_response)


@router.get("/assessments", response_model=PaginatedResponse[list[AssessmentListItem]], status_code=200)
def list_assessments(
    response: Response,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    sort_by: str = Query(default="created_at"),
    sort_dir: str = Query(default="desc"),
    search: str | None = Query(default=None),
    company: str | None = Query(default=None),
    recommendation: str | None = Query(default=None),
    industry: str | None = Query(default=None),
    project_type: str | None = Query(default=None),
    rules_version: int | None = Query(default=None),
    questionnaire_version: int | None = Query(default=None),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    document_backed_only: bool = Query(default=False),
    _: AdminUserEntity = Depends(require_permission("assessments:read")),
    db: Session = Depends(get_db),
) -> PaginatedResponse[list[AssessmentListItem]]:
    parsed_date_from = datetime.fromisoformat(date_from) if date_from else None
    parsed_date_to = datetime.fromisoformat(date_to) if date_to else None
    service_response = admin_service.list_assessments(
        db=db,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_dir=sort_dir,
        search=search,
        company=company,
        recommendation=recommendation,
        industry=industry,
        project_type=project_type,
        rules_version=rules_version,
        questionnaire_version=questionnaire_version,
        date_from=parsed_date_from,
        date_to=parsed_date_to,
        document_backed_only=document_backed_only,
    )
    return apply_status_code(response=response, payload=service_response)


@router.get(
    "/assessment-company-groups",
    response_model=PaginatedResponse[list[CompanyGroupItem]],
    status_code=200,
)
def list_assessment_company_groups(
    response: Response,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    sort_by: str = Query(default="latest_submission_at"),
    sort_dir: str = Query(default="desc"),
    search: str | None = Query(default=None),
    company: str | None = Query(default=None),
    recommendation: str | None = Query(default=None),
    industry: str | None = Query(default=None),
    project_type: str | None = Query(default=None),
    rules_version: int | None = Query(default=None),
    questionnaire_version: int | None = Query(default=None),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    document_backed_only: bool = Query(default=False),
    _: AdminUserEntity = Depends(require_permission("assessments:read")),
    db: Session = Depends(get_db),
) -> PaginatedResponse[list[CompanyGroupItem]]:
    parsed_date_from = datetime.fromisoformat(date_from) if date_from else None
    parsed_date_to = datetime.fromisoformat(date_to) if date_to else None
    service_response = admin_service.list_grouped_assessments_by_company(
        db=db,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_dir=sort_dir,
        search=search,
        company=company,
        recommendation=recommendation,
        industry=industry,
        project_type=project_type,
        rules_version=rules_version,
        questionnaire_version=questionnaire_version,
        date_from=parsed_date_from,
        date_to=parsed_date_to,
        document_backed_only=document_backed_only,
    )
    return apply_status_code(response=response, payload=service_response)


@router.get("/assessments/{submission_id}", response_model=GenericResponse[AssessmentDetailData], status_code=200)
def get_assessment_detail(
    submission_id: int,
    response: Response,
    _: AdminUserEntity = Depends(require_permission("assessments:read")),
    db: Session = Depends(get_db),
) -> GenericResponse[AssessmentDetailData]:
    service_response = admin_service.get_assessment_detail(db=db, submission_id=submission_id)
    return apply_status_code(response=response, payload=service_response)


@router.post(
    "/assessments/{submission_id}/document-processing/retry",
    response_model=GenericResponse[DocumentProcessingRetryData],
    status_code=200,
)
def retry_assessment_document_processing(
    submission_id: int,
    response: Response,
    _: AdminUserEntity = Depends(require_permission("assessments:write")),
    db: Session = Depends(get_db),
) -> GenericResponse[DocumentProcessingRetryData]:
    service_response = admin_service.retry_document_processing(db=db, submission_id=submission_id)
    return apply_status_code(response=response, payload=service_response)


@router.get("/assessments/{submission_id}/traditional-advisor", response_model=GenericResponse[TraditionalAdvisorData], status_code=200)
def get_assessment_traditional_advisor(
    submission_id: int,
    response: Response,
    _: AdminUserEntity = Depends(require_permission("assessments:read")),
    db: Session = Depends(get_db),
) -> GenericResponse[TraditionalAdvisorData]:
    data = traditional_advisor_service.get_for_admin(db, submission_id)
    return apply_status_code(response=response, payload=GenericResponse.success_response("Traditional advisor status fetched.", data=data))


@router.post("/assessments/{submission_id}/traditional-advisor/retry", response_model=GenericResponse[TraditionalAdvisorData], status_code=200)
def retry_assessment_traditional_advisor(
    submission_id: int,
    response: Response,
    _: AdminUserEntity = Depends(require_permission("assessments:write")),
    db: Session = Depends(get_db),
) -> GenericResponse[TraditionalAdvisorData]:
    return apply_status_code(response=response, payload=traditional_advisor_service.retry(db, submission_id))


@router.delete("/assessments/{submission_id}", response_model=GenericResponse[AssessmentDeleteData], status_code=200)
def delete_assessment(
    submission_id: int,
    response: Response,
    _: AdminUserEntity = Depends(require_permission("assessments:write")),
    db: Session = Depends(get_db),
) -> GenericResponse[AssessmentDeleteData]:
    service_response = admin_service.delete_assessment(db=db, submission_id=submission_id)
    return apply_status_code(response=response, payload=service_response)


@router.get(
    "/assessment-activity/incomplete",
    response_model=GenericResponse[IncompleteActivityData],
    status_code=200,
)
def get_incomplete_assessment_activity(
    response: Response,
    _: AdminUserEntity = Depends(require_permission("assessment_data:reset")),
    db: Session = Depends(get_db),
) -> GenericResponse[IncompleteActivityData]:
    service_response = admin_service.get_incomplete_activity(db=db)
    return apply_status_code(response=response, payload=service_response)


@router.delete(
    "/assessment-activity/incomplete",
    response_model=GenericResponse[IncompleteActivityData],
    status_code=200,
)
def reset_incomplete_assessment_activity(
    payload: IncompleteActivityResetRequest,
    response: Response,
    _: AdminUserEntity = Depends(require_permission("assessment_data:reset")),
    db: Session = Depends(get_db),
) -> GenericResponse[IncompleteActivityData]:
    service_response = admin_service.reset_incomplete_activity(db=db, confirmation=payload.confirmation)
    return apply_status_code(response=response, payload=service_response)


@router.get("/assessment-documents/{document_id}/preview")
def preview_assessment_document(
    document_id: int,
    _: AdminUserEntity = Depends(require_permission("assessments:read")),
    db: Session = Depends(get_db),
):
    content, filename, content_type = admin_service.get_document_content(db=db, document_id=document_id)
    return StreamingResponse(iter([content]), media_type=content_type, headers={"Content-Disposition": f'inline; filename="{filename}"'})


@router.get("/assessment-documents/{document_id}/download")
def download_assessment_document(
    document_id: int,
    _: AdminUserEntity = Depends(require_permission("assessments:read")),
    db: Session = Depends(get_db),
):
    content, filename, content_type = admin_service.get_document_content(db=db, document_id=document_id)
    return StreamingResponse(iter([content]), media_type=content_type, headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@router.get("/analytics/trends", response_model=GenericResponse[TrendsData], status_code=200)
def analytics_trends(
    response: Response,
    days: int = Query(default=30, ge=1, le=365),
    recommendation: str | None = Query(default=None),
    industry: str | None = Query(default=None),
    project_type: str | None = Query(default=None),
    rules_version: int | None = Query(default=None),
    questionnaire_version: int | None = Query(default=None),
    _: AdminUserEntity = Depends(require_permission("analytics:read")),
    db: Session = Depends(get_db),
) -> GenericResponse[TrendsData]:
    service_response = admin_service.get_trends(
        db=db,
        days=days,
        recommendation=recommendation,
        industry=industry,
        project_type=project_type,
        rules_version=rules_version,
        questionnaire_version=questionnaire_version,
    )
    return apply_status_code(response=response, payload=service_response)


@router.get("/analytics/distributions", response_model=GenericResponse[DistributionsData], status_code=200)
def analytics_distributions(
    response: Response,
    recommendation: str | None = Query(default=None),
    industry: str | None = Query(default=None),
    project_type: str | None = Query(default=None),
    rules_version: int | None = Query(default=None),
    questionnaire_version: int | None = Query(default=None),
    _: AdminUserEntity = Depends(require_permission("analytics:read")),
    db: Session = Depends(get_db),
) -> GenericResponse[DistributionsData]:
    service_response = admin_service.get_distributions(
        db=db,
        recommendation=recommendation,
        industry=industry,
        project_type=project_type,
        rules_version=rules_version,
        questionnaire_version=questionnaire_version,
    )
    return apply_status_code(response=response, payload=service_response)


@router.get("/export.csv")
def export_assessments_csv(
    _: AdminUserEntity = Depends(require_permission("assessments:export")),
    db: Session = Depends(get_db),
):
    output = admin_service.export_assessments_csv(db=db)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=assessments.csv"},
    )


@router.get("/questionnaires", response_model=GenericResponse[list[QuestionnaireData]], status_code=200)
def list_questionnaire_versions(
    response: Response,
    _: AdminUserEntity = Depends(require_permission("questionnaire:read")),
    db: Session = Depends(get_db),
) -> GenericResponse[list[QuestionnaireData]]:
    service_response = questionnaire_service.list_versions(db=db)
    return apply_status_code(response=response, payload=service_response)


@router.put("/questionnaires", response_model=GenericResponse[QuestionnaireData], status_code=200)
def update_questionnaire(
    payload: QuestionnaireUpdateRequest,
    response: Response,
    user: AdminUserEntity = Depends(require_permission("questionnaire:write")),
    db: Session = Depends(get_db),
) -> GenericResponse[QuestionnaireData]:
    service_response = questionnaire_service.create_version(
        db=db,
        payload=payload,
        changed_by=user.email,
    )
    return apply_status_code(response=response, payload=service_response)


@router.put(
    "/questionnaires/activate/{version}",
    response_model=GenericResponse[QuestionnaireData],
    status_code=200,
)
def activate_questionnaire_version(
    version: int,
    response: Response,
    user: AdminUserEntity = Depends(require_permission("questionnaire:activate")),
    db: Session = Depends(get_db),
) -> GenericResponse[QuestionnaireData]:
    service_response = questionnaire_service.activate_version(
        db=db,
        version=version,
        changed_by=user.email,
    )
    return apply_status_code(response=response, payload=service_response)


@router.get("/users", response_model=GenericResponse[list[AdminUserData]], status_code=200)
def list_admin_users(
    response: Response,
    _: AdminUserEntity = Depends(require_permission("admin_users:read")),
    db: Session = Depends(get_db),
) -> GenericResponse[list[AdminUserData]]:
    service_response = admin_user_service.list_users(db=db)
    return apply_status_code(response=response, payload=service_response)


@router.post("/users", response_model=GenericResponse[AdminUserData], status_code=201)
def create_admin_user(
    payload: AdminUserCreateRequest,
    response: Response,
    _: AdminUserEntity = Depends(require_permission("admin_users:write")),
    db: Session = Depends(get_db),
) -> GenericResponse[AdminUserData]:
    service_response = admin_user_service.create_user(db=db, payload=payload)
    return apply_status_code(response=response, payload=service_response)


@router.put("/users/{user_id}", response_model=GenericResponse[AdminUserData], status_code=200)
def update_admin_user(
    user_id: int,
    payload: AdminUserUpdateRequest,
    response: Response,
    current_user: AdminUserEntity = Depends(require_permission("admin_users:write")),
    db: Session = Depends(get_db),
) -> GenericResponse[AdminUserData]:
    safe_payload = payload
    if current_user.id == user_id and not payload.is_active:
        safe_payload = payload.model_copy(update={"is_active": True})
    service_response = admin_user_service.update_user(db=db, user_id=user_id, payload=safe_payload)
    return apply_status_code(response=response, payload=service_response)
