"""
this script contains the business logic for handling courses
"""
from typing import Dict, Optional
from sqlalchemy.orm import Session
from backend.repository.courses import CourseRepository
from backend.app.schemas import CourseResponse, CourseListResponse


class CourseService:
    """Encapsulates business logic for handling courses."""

    def __init__(self, db: Session):
        self.course_repo = CourseRepository(db)

    def fetch_course_by_code(self, course_code: str) -> Optional[CourseResponse]:
        """Fetch a course and format its response."""
        course = self.course_repo.get_course_by_code(course_code)
        if not course:
            return None

        # Fetch offered semesters
        offered_semesters = self.course_repo.get_offered_semesters(course_code)

        # Fetch course requirements
        requirements = self.course_repo.get_course_requirements(course_code)

        return CourseResponse(
            course_code=course.course_code,
            course_name=course.name,
            department=course.dep_code,
            prerequisites=course.prereqs_text or "None",
            offered=offered_semesters,
            requirements=requirements,
        )

    def fetch_courses_by_department(self, department: str) -> CourseListResponse:
        """Fetch all courses in a department."""
        courses = self.course_repo.get_courses_by_department(department)

        structured_courses = []
        for course in courses:
            offered_semesters = self.course_repo.get_offered_semesters(course.course_code)
            requirements = self.course_repo.get_course_requirements(course.course_code)

            structured_courses.append(CourseResponse(
                course_code=course.course_code,
                course_name=course.name,
                department=course.dep_code,
                prerequisites=course.prereqs_text or "None",
                offered=offered_semesters,
                requirements=requirements,
            ))

        return CourseListResponse(courses=structured_courses)

    def fetch_courses_by_requirement(self, cs_requirement=None, is_requirement=None, ba_requirement=None, bs_requirement=None) -> CourseListResponse:
        """Fetch and process courses matching requirements."""
        raw_results = self.course_repo.get_courses_by_requirement(cs_requirement, is_requirement, ba_requirement, bs_requirement)

        # Process results into structured output
        course_dict: Dict[str, dict] = {}
        for course_code, course_name, department, prerequisites, requirement, audit_id in raw_results:
            if course_code not in course_dict:
                offered_semesters = self.course_repo.get_offered_semesters(course_code)

                course_dict[course_code] = {
                    "course_code": course_code,
                    "course_name": course_name,
                    "department": department,
                    "prerequisites": prerequisites or "None",
                    "offered": offered_semesters,
                    "requirements": {"CS": [], "IS": [], "BA": [], "BS": []},
                }

            if audit_id.startswith("cs"):
                course_dict[course_code]["requirements"]["CS"].append(requirement)
            elif audit_id.startswith("is"):
                course_dict[course_code]["requirements"]["IS"].append(requirement)
            elif audit_id.startswith("ba"):
                course_dict[course_code]["requirements"]["BA"].append(requirement)
            elif audit_id.startswith("bio"):
                course_dict[course_code]["requirements"]["BS"].append(requirement)

        return CourseListResponse(courses=[CourseResponse(**course) for course in course_dict.values()])

    def fetch_all_requirements(self):
        """Retrieve and structure requirements for the frontend."""
        return self.course_repo.get_all_requirements()
