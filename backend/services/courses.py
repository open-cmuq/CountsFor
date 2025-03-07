from typing import List, Dict
from sqlalchemy.orm import Session
from backend.repository.courses import CourseRepository
from backend.app.schemas import CourseResponse, CourseListResponse

class CourseService:
    """Encapsulates business logic for handling courses."""

    def __init__(self, db: Session):
        self.course_repo = CourseRepository(db)

    def fetch_course_by_code(self, course_code: str):
        """Fetch a course and format its response."""
        course = self.course_repo.get_course_by_code(course_code)
        if not course:
            return None
        return CourseResponse(
            course_code=course.course_code,
            course_name=course.name,
            requirements={},  # You can add requirement mapping logic here
        )

    def fetch_courses_by_department(self, department: str):
        """Fetch all courses in a department."""
        courses = self.course_repo.get_courses_by_department(department)
        return CourseListResponse(
            courses=[CourseResponse(course_code=c.course_code, course_name=c.name, requirements={}) for c in courses]
        )

    def fetch_courses_by_requirement(self, cs_requirement=None, is_requirement=None, ba_requirement=None, bs_requirement=None):
        """Fetch and process courses matching requirements."""
        raw_results = self.course_repo.get_courses_by_requirement(cs_requirement, is_requirement, ba_requirement, bs_requirement)

        # Process results into structured output
        course_dict: Dict[str, CourseResponse] = {}
        for course_code, course_name, requirement, audit_id in raw_results:
            if course_code not in course_dict:
                course_dict[course_code] = CourseResponse(
                    course_code=course_code,
                    course_name=course_name,
                    requirements={"CS": [], "IS": [], "BA": [], "BS": []},
                )
            if audit_id.startswith("cs"):
                course_dict[course_code].requirements["CS"].append(requirement)
            elif audit_id.startswith("is"):
                course_dict[course_code].requirements["IS"].append(requirement)
            elif audit_id.startswith("ba"):
                course_dict[course_code].requirements["BA"].append(requirement)
            elif audit_id.startswith("bs"):
                course_dict[course_code].requirements["BS"].append(requirement)

        return CourseListResponse(courses=list(course_dict.values()))
