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
    """Pydantic schema for a single course response."""
    course_code: str
    course_name: str
    department: str
    prerequisites: Optional[str] = "None"
    offered: List[str]
    requirements: Dict[str, List[str]]

class CourseListResponse(BaseModel):
    """
    represents a list of filtered courses.
    """
    courses: List[CourseResponse]


class RequirementsResponse(BaseModel):
    """Pydantic schema for returning requirements grouped by major."""
    BA: List[str]
    BS: List[str]
    CS: List[str]
    IS: List[str]

class DepartmentListResponse(BaseModel):
    """Pydantic schema for returning a list of departments."""
    departments: List[str]
