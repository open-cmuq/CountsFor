from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database.db import get_db
from backend.services.departments import DepartmentService
from backend.app.schemas import DepartmentListResponse

router = APIRouter()

def get_department_service(db: Session = Depends(get_db)) -> DepartmentService:
    """
    Provides a DepartmentService instance for handling department-related operations.
    """
    return DepartmentService(db)

@router.get("/departments", response_model=DepartmentListResponse)
def get_departments(department_service: DepartmentService = Depends(get_department_service)):
    """
    API route to fetch all available departments with their names.
    """
    return department_service.fetch_all_departments()
