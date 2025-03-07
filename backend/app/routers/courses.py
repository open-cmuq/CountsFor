from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database.db import get_db
from backend.services.courses import CourseService
from backend.app.schemas import CourseResponse, CourseListResponse, CourseFilter

router = APIRouter()

def get_course_service(db: Session = Depends(get_db)) -> CourseService:
    return CourseService(db)

@router.get("/courses/filter", response_model=CourseListResponse)
def get_courses_by_requirement_route(
    course_filter: CourseFilter = Depends(),
    course_service: CourseService = Depends(get_course_service)
):
    courses = course_service.fetch_courses_by_requirement(
        course_filter.cs_requirement,
        course_filter.is_requirement,
        course_filter.ba_requirement,
        course_filter.bs_requirement
    )

    if not courses.courses:
        raise HTTPException(status_code=404, detail="No courses found matching the selected requirements")

    return courses

@router.get("/courses/{course_code}", response_model=CourseResponse)
def get_course(course_code: str, course_service: CourseService = Depends(get_course_service)):
    course = course_service.fetch_course_by_code(course_code)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course

@router.get("/courses", response_model=CourseListResponse)
def get_courses_by_department_route(department: str, course_service: CourseService = Depends(get_course_service)):
    return course_service.fetch_courses_by_department(department)


