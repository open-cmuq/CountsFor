"""
this module contains the AnalyticsRepository class, which encapsulates
database operations for analytics-related queries.
"""

from typing import Optional
from sqlalchemy.orm import Session
from backend.database.models import CountsFor, Requirement, Offering, Course, Audit

class AnalyticsRepository:
    """encapsulates database operations for analytics-related queries."""

    def __init__(self, db: Session):
        self.db = db

    def get_course_coverage(self, major: str, semester: Optional[str] = None):
        """Fetch the count of courses fulfilling each requirement for a given major,
        optionally filtering by semester and campus ID."""

        # Base query for requirements
        requirement_counts = (
            self.db.query(Requirement.requirement)
            .join(CountsFor, CountsFor.requirement == Requirement.requirement)
            .join(Audit, Requirement.audit_id == Audit.audit_id)
            .filter(Audit.major == major)
            .distinct()
        ).all()

        result = {}

        for (req,) in requirement_counts:
            # Count courses fulfilling the requirement
            course_count = self.db.query(Course).join(CountsFor).join(Offering).filter(
                CountsFor.requirement == req,
                Course.offered_qatar == True,  # Assuming you want courses offered in Qatar
                Offering.semester == semester,
                Offering.campus_id == 2  # Filter by campus ID
            ).distinct(Course.course_code).count()

            result[req] = course_count

        return result
