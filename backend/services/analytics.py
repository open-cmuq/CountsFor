"""
This module contains the AnalyticsService class, which handles business
logic for analytics-related queries.
"""
from typing import Optional
from sqlalchemy.orm import Session
from backend.repository.analytics import AnalyticsRepository
from backend.app.schemas import CourseCoverageResponse
import logging

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

        # Log the data received from the repository
        logging.info(f"[AnalyticsService] Data received from repository for {course_code}: {len(raw_data)} records")
        if raw_data:
            logging.debug(f"[AnalyticsService] First repo record example: {raw_data[0]}")

        formatted_data = [
            {
                "semester": record["semester"],
                "enrollment_count": record["enrollment_count"],
                "class_": record["class_"],
                # "offering_id": record.get("offering_id") # Not present in aggregated data
            }
            for record in raw_data
        ]

        logging.info(f"[AnalyticsService] Returning {len(formatted_data)} formatted enrollment records for {course_code}")
        if formatted_data:
            logging.debug(f"[AnalyticsService] First formatted record example: {formatted_data[0]}")

        return formatted_data
