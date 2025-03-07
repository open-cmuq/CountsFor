from pydantic import BaseModel, Field
from typing import Optional, Dict, List

class CourseFilter(BaseModel):
    """
    Represents the query parameters for filtering courses.
    """
    cs_requirement: Optional[str] = Field(None, description="CS requirement (e.g. 'Humanities Elective')")
    is_requirement: Optional[str] = Field(None, description="IS requirement (e.g. 'English Requirement')")
    ba_requirement: Optional[str] = Field(None, description="BA requirement (e.g. 'Economics')")
    bs_requirement: Optional[str] = Field(None, description="BS requirement (e.g. 'Mathematics')")

class CourseResponse(BaseModel):
    """
    Represents the structured output for a course.
    """
    course_code: str
    course_name: str
    requirements: Dict[str, List[str]]

class CourseListResponse(BaseModel):
    """
    Represents a list of filtered courses.
    """
    courses: List[CourseResponse]
