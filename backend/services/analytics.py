"""
This module contains the AnalyticsService class, which handles business
logic for analytics-related queries.
"""
from typing import Optional
from sqlalchemy.orm import Session
from backend.repository.analytics import AnalyticsRepository
from backend.app.schemas import CourseCoverageResponse

class AnalyticsService:
    """handles business logic for analytics-related queries."""

    def __init__(self, db: Session):
        self.analytics_repo = AnalyticsRepository(db)

    def fetch_course_coverage(self, major: str,
                              semester: Optional[str] = None) -> CourseCoverageResponse:
        """Fetch course coverage data, counting offerings per requirement."""
        raw_data = self.analytics_repo.get_course_coverage(major, semester)

        formatted_data = [{"requirement": req, "num_courses": count} for (req,
                                                                        count) in raw_data.items()]

        return CourseCoverageResponse(major=major, semester=semester, coverage=formatted_data)

    def fetch_enrollment_data(self, course_code: str):
        """Fetch enrollment data for a specific course, including offering_id and semester."""
        raw_data = self.analytics_repo.get_enrollment_data(course_code)
        return [
            {
                "semester": record["semester"],
                "enrollment_count": record["enrollment_count"],
                "class_": record["class_"],
                "offering_id": record.get("offering_id")
            }
            for record in raw_data
        ]
