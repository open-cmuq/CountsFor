"""
this script contains the business logic for handling courses
"""
from typing import Dict, Optional, List
from sqlalchemy.orm import Session
from backend.repository.courses import CourseRepository
from backend.app.schemas import CourseResponse, CourseListResponse


class CourseService:
    """encapsulates business logic for handling courses."""

    def __init__(self, db: Session):
        self.course_repo = CourseRepository(db)

    def fetch_course_by_code(self, course_code: str) -> Optional[CourseResponse]:
        """fetch a course and format its response."""
        course = self.course_repo.get_course_by_code(course_code)
        if not course:
            return None

        # fetch offered semesters
        offered_semesters = self.course_repo.get_offered_semesters(course_code)

        # fetch course requirements
        requirements = self.course_repo.get_course_requirements(course_code)

        return CourseResponse(
            course_code=course.course_code,
            course_name=course.name,
            department=course.dep_code,
            units=course.units,
            description=course.description,
            prerequisites=course.prereqs_text or "None",
            offered=offered_semesters,
            requirements=requirements,
        )


    def fetch_all_courses(self) -> CourseListResponse:
        """fetch and structure all courses, prioritizing courses that fulfill
        at least one requirement."""
        courses = self.course_repo.get_all_courses()

        for course in courses:
            course["num_requirements"] = sum(len(reqs) for reqs in course["requirements"].values())
            course["num_offered_semesters"] = len(course["offered"])

        sorted_courses = sorted(
            courses,
            key=lambda c: (c["num_requirements"] == 0, -c["num_offered_semesters"]),
            reverse=False
        )

        structured_courses = [
            CourseResponse(
                course_code=course["course_code"],
                course_name=course["course_name"],
                department=course["department"],
                units=course["units"],
                description=course["description"],
                prerequisites=course["prerequisites"],
                offered=course["offered"],
                requirements=course["requirements"],
            )
            for course in sorted_courses
        ]

        return CourseListResponse(courses=structured_courses)




    def fetch_courses_by_requirement(self, cs_requirement=None, is_requirement=None,
                                     ba_requirement=None,
                                     bs_requirement=None) -> CourseListResponse:
        """fetch and process courses matching requirements."""
        raw_results = self.course_repo.get_courses_by_requirement(cs_requirement, is_requirement,
                                                                  ba_requirement, bs_requirement)

        # Process results into structured output
        course_dict: Dict[str, dict] = {}
        for (course_code, course_name, department,
             prerequisites, requirement, audit_id) in raw_results:
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

        return CourseListResponse(courses=[CourseResponse(**course)
                                           for course in course_dict.values()])

    def fetch_courses_by_prerequisite(self, has_prereqs: bool) -> CourseListResponse:
        """fetch and structure courses based on whether they have prerequisites."""
        courses = self.course_repo.get_courses_by_prerequisite(has_prereqs)

        structured_courses = [
            CourseResponse(
                course_code=course["course_code"],
                course_name=course["course_name"],
                department=course["department"],
                units=course["units"],
                description=course["description"],
                prerequisites=course["prerequisites"],
                offered=course["offered"],
                requirements=course["requirements"],
            )
            for course in courses
        ]

        return CourseListResponse(courses=structured_courses)

    def fetch_courses_by_department(self, department: str) -> CourseListResponse:
        """fetch and structure courses filtered by department."""
        courses = self.course_repo.get_courses_by_department(department)

        structured_courses = [
            CourseResponse(
                course_code=course["course_code"],
                course_name=course["course_name"],
                department=course["department"],
                units=course["units"],
                description=course["description"],
                prerequisites=course["prerequisites"],
                offered=course["offered"],
                requirements=course["requirements"],
            )
            for course in courses
        ]

        return CourseListResponse(courses=structured_courses)

    def fetch_all_departments(self) -> List[str]:
        """fetch a distinct list of all departments."""
        return self.course_repo.get_all_departments()
