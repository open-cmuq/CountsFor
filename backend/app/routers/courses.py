from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.db import get_course_by_code, get_db
from backend.app.schemas import CourseResponse

router = APIRouter()

@router.get("/courses/{course_code}", response_model=CourseResponse)
def get_course(course_code: str, db: Session = Depends(get_db)):
    """API route to fetch a course by its code."""
    course = get_course_by_code(db, course_code)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course
