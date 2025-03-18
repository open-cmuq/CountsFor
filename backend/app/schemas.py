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
    units: Optional[int] = None
    description: Optional[str] = None
    prerequisites: Optional[str] = "None"
    offered: List[str]  # List of semesters the course is offered
    offered_qatar: bool  # True if offered in Qatar
    offered_pitts: bool  # True if offered in Pittsburgh
    requirements: Dict[str, List[str]]



class CourseListResponse(BaseModel):
    """
    represents a list of filtered courses.
    """
    courses: List[CourseResponse]


class RequirementResponse(BaseModel):
    """Pydantic schema for a single requirement."""
    requirement: str
    type: bool
    major: str

class RequirementsResponse(BaseModel):
    """Pydantic schema for returning a list of requirements."""
    requirements: List[RequirementResponse]

class DepartmentResponse(BaseModel):
    """Pydantic schema for a single department."""
    dep_code: str
    name: str

class DepartmentListResponse(BaseModel):
    """Represents a list of departments."""
    departments: List[DepartmentResponse]

class CombinedCourseFilter(BaseModel):
    """Represents a combined course filter."""
    department: Optional[str] = Field(None, description="Filter by department code")
    semester: Optional[str] = Field(None, description="Filter by semester offered, e.g. 'F24'")
    has_prereqs: Optional[bool] = Field(None,
                                        description="Filter by whether courses have prerequisites")
    cs_requirement: Optional[str] = Field(None, description="Filter by CS requirement")
    is_requirement: Optional[str] = Field(None, description="Filter by IS requirement")
    ba_requirement: Optional[str] = Field(None, description="Filter by BA requirement")
    bs_requirement: Optional[str] = Field(None, description="Filter by BS requirement")
    offered_qatar: Optional[bool] = Field(None, description="Filter by courses offered in Qatar")
    offered_pitts: Optional[bool] = Field(None,
                                          description="Filter by courses offered in Pittsburgh")
