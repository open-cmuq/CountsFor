"""
this module defines the API routes for analytics queries.
"""

from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database.db import get_db
from backend.services.analytics import AnalyticsService
from backend.app.schemas import CourseCoverageResponse, EnrollmentDataResponse

router = APIRouter()

def get_analytics_service(db: Session = Depends(get_db)) -> AnalyticsService:
    """provides AnalyticsService instance for handling analytics queries."""
    return AnalyticsService(db)

@router.get("/analytics/course-coverage", response_model=CourseCoverageResponse)
def get_course_coverage(
    major: str,
    semester: Optional[str] = None,
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Get course coverage data: number of courses fulfilling each requirement for a major.
    - `major`: Required, filters by major.
    - `semester`: Optional, filters by semester.

    Example Requests:
    - `/analytics/course-coverage?major=CS`
    - `/analytics/course-coverage?major=BA&semester=F22`
    """
    return analytics_service.fetch_course_coverage(major, semester)

@router.get("/analytics/enrollment-data", response_model=EnrollmentDataResponse)
def get_enrollment_data(
    course_code: str,
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Get past enrollment data for a specific course.
    - `course_code`: Required, the code of the course.

    Example Request:
    - `/analytics/enrollment-data?course_code=CS101`
    """
    enrollment_data = analytics_service.fetch_enrollment_data(course_code)
    return EnrollmentDataResponse(enrollment_data=enrollment_data)
