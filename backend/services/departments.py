from backend.repository.departments import DepartmentRepository
from backend.app.schemas import DepartmentListResponse, DepartmentResponse
from sqlalchemy.orm import Session

class DepartmentService:
    """Handles business logic for departments."""

    def __init__(self, db: Session):
        self.department_repo = DepartmentRepository(db)

    def fetch_all_departments(self) -> DepartmentListResponse:
        """Fetch a list of departments that have courses."""
        raw_departments = self.department_repo.get_all_departments()

        departments = [
            DepartmentResponse(dep_code=dep_code, name=name)
            for dep_code, name in raw_departments
        ]

        return DepartmentListResponse(departments=departments)
