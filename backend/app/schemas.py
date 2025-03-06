from pydantic import BaseModel
from typing import List, Dict, Optional

class CourseResponse(BaseModel):
    course_code: str
    course_name: str
    requirements: Dict[str, List[str]]
    offered: List[str]
    prerequisites: str
