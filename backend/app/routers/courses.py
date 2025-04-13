"""
This script defines API endpoints for course-related operations.
This module contains the FastAPI routes for retrieving course information,
filtering courses based on department and requirements, and integrating with
the service layer for business logic.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database.db import get_db
from backend.services.courses import CourseService
from backend.app.schemas import (CourseResponse, CourseListResponse,
                                 CombinedCourseFilter)

router = APIRouter()

def get_course_service(db: Session = Depends(get_db)) -> CourseService:
    """
    Provides a CourseService instance for handling course-related operations.
    """
    return CourseService(db)

@router.get("/courses/search", response_model=CourseListResponse)
def search_courses(
    filters: CombinedCourseFilter = Depends(),
    course_service: CourseService = Depends(get_course_service)
):
    """
    fetch courses based on a combination of filters.
    """
    courses = course_service.fetch_courses_by_filters(
        department=filters.department,
        semester=filters.semester,
        has_prereqs=filters.has_prereqs,
        cs_requirement=filters.cs_requirement,
        is_requirement=filters.is_requirement,
        ba_requirement=filters.ba_requirement,
        bs_requirement=filters.bs_requirement,
        offered_qatar=filters.offered_qatar,
        offered_pitts=filters.offered_pitts,
        search_query=filters.searchQuery  # new parameter passed along
    )
    if not courses.courses:
        raise HTTPException(status_code=404, detail="No courses found matching "
        "the provided filters")
    return courses

@router.get("/courses/semesters")
def get_all_semesters(course_service: CourseService = Depends(get_course_service)):
    """
    Endpoint to retrieve a list of all semesters (from the Offerings table).
    """
    semesters = course_service.fetch_all_semesters()
    return {"semesters": semesters}


@router.get("/courses/{course_code}", response_model=CourseResponse)
def get_course(course_code: str, course_service: CourseService = Depends(get_course_service)):
    """
    fetch course details by course code.
    """
    course = course_service.fetch_course_by_code(course_code)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course
