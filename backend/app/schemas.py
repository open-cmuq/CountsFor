"""
this script contains data models used for API input validation and response serialization,
ensuring type safety and structure for course-related operations.
"""

from typing import Optional, Dict, List
from pydantic import BaseModel, Field

class CourseFilter(BaseModel):
    """
    represents the query parameters for filtering courses.
    """
    cs_requirement: Optional[str] = Field(None, description="CS requirement")
    is_requirement: Optional[str] = Field(None, description="IS requirement")
    ba_requirement: Optional[str] = Field(None, description="BA requirement")
    bs_requirement: Optional[str] = Field(None, description="BS requirement)")

class CourseResponse(BaseModel):
    """
    represents the structured output for a course.
    """
    course_code: str
    course_name: str
    requirements: Dict[str, List[str]]

class CourseListResponse(BaseModel):
    """
    represents a list of filtered courses.
    """
    courses: List[CourseResponse]
