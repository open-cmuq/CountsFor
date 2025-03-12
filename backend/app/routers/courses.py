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
                                 CourseFilter, RequirementsResponse,
                                 DepartmentListResponse, RequirementResponse)

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

@router.get("/courses/{course_code}", response_model=CourseResponse)
def get_course(course_code: str, course_service: CourseService = Depends(get_course_service)):
    """
    Fetch course details by course code.
    """
    course = course_service.fetch_course_by_code(course_code)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course

@router.get("/requirements", response_model=RequirementsResponse)
def get_requirements(course_service: CourseService = Depends(get_course_service)):
    """API route to fetch all course requirements with type and major."""
    return course_service.fetch_all_requirements()

@router.get("/departments", response_model=DepartmentListResponse)
def get_departments(course_service: CourseService = Depends(get_course_service)):
    """
    API route to fetch all available departments.
    """
    return DepartmentListResponse(departments=course_service.fetch_all_departments())

@router.get("/requirements/{requirement_name}", response_model=RequirementResponse)
def get_requirement(requirement_name: str,
                    course_service: CourseService = Depends(get_course_service)):
    """API route to fetch a single requirement with its type and major."""
    requirement = course_service.fetch_requirement(requirement_name)
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")
    return requirement
