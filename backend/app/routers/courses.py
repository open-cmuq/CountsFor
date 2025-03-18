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
                                 CourseFilter, CombinedCourseFilter)

router = APIRouter()

def get_course_service(db: Session = Depends(get_db)) -> CourseService:
    """
    Provides a CourseService instance for handling course-related operations.
    """
    return CourseService(db)

@router.get("/courses", response_model=CourseListResponse)
def get_all_courses(course_service: CourseService = Depends(get_course_service)):
    """
    API route to fetch all courses.
    """
    return course_service.fetch_all_courses()

@router.get("/courses/by-department", response_model=CourseListResponse)
def get_courses_by_department_route(department: str,
                                    course_service: CourseService = Depends(get_course_service)):
    """
    Fetch courses filtered by department.
    """
    return course_service.fetch_courses_by_department(department)

@router.get("/courses/filter", response_model=CourseListResponse)
def get_courses_by_requirement_route(
    course_filter: CourseFilter = Depends(),
    course_service: CourseService = Depends(get_course_service)
):
    """
    Fetch courses based on specified major requirements.
    """
    courses = course_service.fetch_courses_by_requirement(
        course_filter.cs_requirement,
        course_filter.is_requirement,
        course_filter.ba_requirement,
        course_filter.bs_requirement
    )

    if not courses.courses:
        raise HTTPException(status_code=404,
                            detail="No courses found matching the selected requirements")

    return courses

@router.get("/courses/by-prerequisite", response_model=CourseListResponse)
def get_courses_by_prerequisite(
    has_prereqs: bool,
    course_service: CourseService = Depends(get_course_service)
):
    """
    Fetch courses based on whether they have prerequisites.
    Example usage:
      - `/courses/by-prerequisite?has_prereqs=true` → Fetch courses with prerequisites.
      - `/courses/by-prerequisite?has_prereqs=false` → Fetch courses without prerequisites.
    """
    return course_service.fetch_courses_by_prerequisite(has_prereqs)

@router.get("/courses/by-offered_location", response_model=CourseListResponse)
def get_courses_by_offering(
    offered_qatar: bool = None,
    offered_pitts: bool = None,
    course_service: CourseService = Depends(get_course_service)
):
    """
    fetch courses based on whether they are offered in Qatar, Pittsburgh, or both.
    Example usage:
      - `/courses/by-offering?offered_qatar=true` → Courses offered in Qatar
      - `/courses/by-offering?offered_pitts=true` → Courses offered in Pittsburgh
      - `/courses/by-offering?offered_qatar=true&offered_pitts=true` → Courses
         offered in both locations
    """
    return course_service.fetch_courses_by_offered_location(offered_qatar, offered_pitts)

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

@router.get("/courses/by-semester", response_model=CourseListResponse)
def get_courses_by_semester_route(semester: str,
                                  course_service: CourseService = Depends(get_course_service)):
    """
    Fetch courses offered in a given semester.

    Example:
      /courses/by-semester?semester=F24
    """
    courses = course_service.fetch_courses_by_semester(semester)
    if not courses.courses:
         raise HTTPException(status_code=404, detail=f"No courses found for semester {semester}")
    return courses

@router.get("/courses/{course_code}", response_model=CourseResponse)
def get_course(course_code: str, course_service: CourseService = Depends(get_course_service)):
    """
    fetch course details by course code.
    """
    course = course_service.fetch_course_by_code(course_code)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course
