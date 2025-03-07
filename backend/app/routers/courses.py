from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.db import get_course_by_code, get_courses_by_department, get_db, get_courses_by_requirement
from backend.app.schemas import CourseResponse, CourseListResponse, CourseFilter

router = APIRouter()

@router.get("/courses/filter", response_model=CourseListResponse)
def get_courses_by_requirement_route(
    course_filter: CourseFilter = Depends(),
    db: Session = Depends(get_db)
):
    """
    API route to fetch courses matching major requirements (strict AND filtering).
    Example:
      - /courses/filter?cs_requirement=Humanities Elective&is_requirement=English Requirement
      - The result includes courses that fulfill **both** CS=Humanities Elective **AND** IS=English Requirement.
    """
    courses = get_courses_by_requirement(
        db,
        cs_requirement=course_filter.cs_requirement,
        is_requirement=course_filter.is_requirement,
        ba_requirement=course_filter.ba_requirement,
        bs_requirement=course_filter.bs_requirement
    )

    if not courses:
        raise HTTPException(status_code=404, detail="No courses found matching the selected requirements")

    return {"courses": courses}


@router.get("/courses/{course_code}", response_model=CourseResponse)
def get_course(course_code: str, db: Session = Depends(get_db)):
    """API route to fetch a course by its code."""
    course = get_course_by_code(db, course_code)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course

@router.get("/courses", response_model=CourseListResponse)
def get_courses_by_department_route(department: str, db: Session = Depends(get_db)):
    """API route to fetch all courses in a specific department."""
    courses = get_courses_by_department(db, department)
    if not courses:
        raise HTTPException(status_code=404, detail="No courses found for this department")
    return {"courses": courses}

