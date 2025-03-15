from backend.repository.departments import DepartmentRepository
from backend.app.schemas import DepartmentListResponse, DepartmentResponse
from sqlalchemy.orm import Session
from typing import List

class DepartmentService:
    """Handles business logic for departments."""

    def __init__(self, db: Session):
        self.department_repo = DepartmentRepository(db)

    def fetch_all_departments(self) -> DepartmentListResponse:
        """Fetch a list of all departments with their names."""
        raw_departments = self.department_repo.get_all_departments()

        # ✅ Ensure response matches the Pydantic schema
        departments = [
            DepartmentResponse(dep_code=dep_code, name=name)
            for dep_code, name in raw_departments
        ]

        return DepartmentListResponse(departments=departments)
