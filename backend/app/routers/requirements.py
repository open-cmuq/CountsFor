from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database.db import get_db
from backend.services.requirements import RequirementService
from backend.app.schemas import RequirementResponse, RequirementsResponse

router = APIRouter()

def get_requirement_service(db: Session = Depends(get_db)) -> RequirementService:
    """
    Provides a RequirementService instance for handling requirement-related operations.
    """
    return RequirementService(db)

@router.get("/requirements", response_model=RequirementsResponse)
def get_requirements(requirement_service: RequirementService = Depends(get_requirement_service)):
    """API route to fetch all course requirements."""
    return requirement_service.fetch_all_requirements()
