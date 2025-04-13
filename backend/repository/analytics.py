"""
this module contains the AnalyticsRepository class, which encapsulates
database operations for analytics-related queries.
"""

from typing import Optional
from sqlalchemy.orm import Session
from backend.database.models import CountsFor, Requirement, Offering, Course, Audit, Enrollment
import logging # Add logging

class AnalyticsRepository:
    """encapsulates database operations for analytics-related queries."""

    def __init__(self, db: Session):
        self.db = db

    def get_course_coverage(self, major: str, semester: Optional[str] = None):
        """Fetch the count of courses fulfilling each requirement for a given major,
        optionally filtering by courses with an offering record in Qatar
        and by semester if provided."""

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
            # Build a subquery for course codes with an offering record in Qatar.
            offering_subq = self.db.query(Offering.course_code).filter(Offering.campus_id == 2)
            if semester:
                offering_subq = offering_subq.filter(Offering.semester == semester)
            offering_subq = offering_subq.subquery()

            # Count courses that are linked to the requirement and have
            #  an offering record (from the subquery)
            course_count = (
                self.db.query(Course)
                .join(CountsFor)
                .filter(
                    CountsFor.requirement == req,
                    Course.course_code.in_(offering_subq)
                )
                .distinct(Course.course_code)
                .count()
            )
            result[req] = course_count

        return result

    def get_enrollment_data(self, course_code: str):
        """Fetch past enrollment data for a specific course, including offering_id and semester."""
        logging.info(f"[AnalyticsRepository] Fetching enrollment data for course: {course_code}")
        try:
            enrollment_data = (
                self.db.query(Enrollment, Offering.semester, Offering.offering_id)
                .join(Offering, Enrollment.offering_id == Offering.offering_id)  # Join on offering_id
                .filter(Offering.course_code == course_code)  # Filter by course_code from Offering
                .all()
            )
            logging.info(f"[AnalyticsRepository] Raw DB query returned {len(enrollment_data)} rows.")
            # Log first few results if available
            if enrollment_data:
                 logging.debug(f"[AnalyticsRepository] First raw result example: {enrollment_data[0]}")
                 if len(enrollment_data) > 1:
                      logging.debug(f"[AnalyticsRepository] Second raw result example: {enrollment_data[1]}")

            # Create a dictionary to aggregate results
            aggregated_data = {}

            for enrollment, semester, _ in enrollment_data: # offering_id is fetched but not used in key
                class_ = enrollment.class_  # Use class_ from Enrollment
                enrollment_count = enrollment.enrollment_count

                # Create a unique key for each semester and class combination
                key = (semester, class_)

                if key not in aggregated_data:
                    aggregated_data[key] = {
                        "semester": semester,
                        "class_": class_,
                        "enrollment_count": 0
                    }

                # Sum the enrollment counts
                aggregated_data[key]["enrollment_count"] += enrollment_count

            final_result = list(aggregated_data.values())
            logging.info(f"[AnalyticsRepository] Aggregated enrollment data into {len(final_result)} records.")
            if final_result:
                 logging.debug(f"[AnalyticsRepository] First aggregated result example: {final_result[0]}")

            return final_result
        except Exception as e:
             logging.error(f"[AnalyticsRepository] Error fetching enrollment data for {course_code}: {e}")
             # Re-raise or return empty list depending on desired error handling
             raise
