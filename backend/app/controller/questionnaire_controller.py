from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.config.database_config import get_db
from app.model.questionnaire_model import QuestionnaireData
from app.service.questionnaire_service import QuestionnaireService
from app.util.response import GenericResponse, apply_status_code

router = APIRouter()
questionnaire_service = QuestionnaireService()


@router.get("/active", response_model=GenericResponse[QuestionnaireData], status_code=200)
def get_active_questionnaire(
    response: Response, db: Session = Depends(get_db)
) -> GenericResponse[QuestionnaireData]:
    service_response = questionnaire_service.get_active_payload(db=db)
    return apply_status_code(response=response, payload=service_response)
