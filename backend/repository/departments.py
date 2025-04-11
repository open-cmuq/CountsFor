from sqlalchemy.orm import Session
from sqlalchemy import case, cast, Integer
from backend.database.models import Department, Course  # Ensure Course model is imported

class DepartmentRepository:
    """Encapsulates database operations for departments."""

    def __init__(self, db: Session):
        self.db = db

    def get_all_departments(self):
        """
        Fetch all departments that have at least one associated course.
        """
        return (
            self.db.query(Department.dep_code, Department.name)
            .join(Course, Course.dep_code == Department.dep_code)
            .distinct()
            .order_by(
                case(
                    (Department.dep_code.op("regexp")("^[0-9]+$"), cast(Department.dep_code, Integer)),
                    else_=999999  # non-numeric codes go to the bottom
                ).asc(),
                Department.dep_code.asc()  # secondary ordering for non-numeric codes
            )
            .all()
        )

    def get_department_name(self, dep_code: str):
        """Fetch department name by department code."""
        department = self.db.query(Department.name).filter(Department.dep_code == dep_code).first()
        return department.name if department else dep_code  # Return code if no name found
