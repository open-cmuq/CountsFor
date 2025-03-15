from sqlalchemy.orm import Session
from backend.database.models import Department

class DepartmentRepository:
    """Encapsulates database operations for departments."""

    def __init__(self, db: Session):
        self.db = db

    def get_all_departments(self):
        """Fetch all departments with their names."""
        return self.db.query(Department.dep_code, Department.name).all()  # ✅ Ensures tuple (dep_code, name)
