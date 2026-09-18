from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.config.database_config import get_db
from app.config.config import settings
from app.model.assessment_model import (
    AssessmentCreateRequest,
    AssessmentEventData,
    AssessmentEventRequest,
    AssessmentResultData,
)
from app.model.traditional_advisor_model import TraditionalAdvisorData
from app.service.assessment_service import AssessmentService
from app.service.traditional_advisor_service import TraditionalAdvisorService
from app.util.response import GenericResponse, apply_status_code

router = APIRouter()
assessment_service = AssessmentService()
traditional_advisor_service = TraditionalAdvisorService()


@router.post("", response_model=GenericResponse[AssessmentResultData], status_code=201)
def create_assessment(
    payload: AssessmentCreateRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> GenericResponse[AssessmentResultData]:
    service_response = assessment_service.create_assessment(
        db=db,
        payload=payload,
        participant_token=request.cookies.get(settings.participant_cookie_name),
    )
    return apply_status_code(response=response, payload=service_response)


@router.post("/events", response_model=GenericResponse[AssessmentEventData], status_code=201)
def track_assessment_event(
    payload: AssessmentEventRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> GenericResponse[AssessmentEventData]:
    service_response = assessment_service.track_event(db=db, payload=payload)
    return apply_status_code(response=response, payload=service_response)


@router.get("/{submission_id}/traditional-advisor", response_model=GenericResponse[TraditionalAdvisorData], status_code=200)
def get_traditional_advisor(
    submission_id: int,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> GenericResponse[TraditionalAdvisorData]:
    service_response = traditional_advisor_service.get_for_participant(
        db, submission_id, request.cookies.get(settings.participant_cookie_name)
    )
    return apply_status_code(response=response, payload=service_response)


@router.post("/{submission_id}/traditional-advisor/retry", response_model=GenericResponse[TraditionalAdvisorData], status_code=200)
def retry_traditional_advisor(
    submission_id: int,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> GenericResponse[TraditionalAdvisorData]:
    traditional_advisor_service.get_for_participant(db, submission_id, request.cookies.get(settings.participant_cookie_name))
    service_response = traditional_advisor_service.retry(db, submission_id)
    return apply_status_code(response=response, payload=service_response)


@router.get("/{submission_id}", response_model=GenericResponse[AssessmentResultData], status_code=200)
def get_assessment(
    submission_id: int,
    response: Response,
    db: Session = Depends(get_db),
) -> GenericResponse[AssessmentResultData]:
    service_response = assessment_service.get_assessment(db=db, submission_id=submission_id)
    return apply_status_code(response=response, payload=service_response)
