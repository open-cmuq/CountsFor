from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.db import get_course_by_code, get_courses_by_department, get_db
from backend.app.schemas import CourseResponse, CourseListResponse

router = APIRouter()

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