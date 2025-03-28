"""
This script contains the business logic for handling courses.
"""

from typing import Dict, Optional
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

        return CourseResponse(
            course_code=course.course_code,
            course_name=course.name,
            department=course.dep_code,
            units=course.units,
            description=course.description,
            prerequisites=course.prereqs_text or "None",
            offered=self.course_repo.get_offered_semesters(course_code),
            offered_qatar=course.offered_qatar,
            offered_pitts=course.offered_pitts,
            requirements=self.course_repo.get_course_requirements(course_code),
        )

    def fetch_all_courses(self) -> CourseListResponse:
        """fetch and structure all courses, prioritizing those fulfilling at least one requirement."""
        courses = self.course_repo.get_all_courses()

        for course in courses:
            course["num_requirements"] = sum(len(reqs) for reqs in course["requirements"].values())
            course["num_offered_semesters"] = len(course["offered"])

        # Sort courses by the numeric value of course_code (after removing the dash)
        sorted_courses = sorted(
            courses,
            key=lambda c: int(c["course_code"].replace("-", ""))
        )

        return CourseListResponse(
            courses=[
                CourseResponse(
                    course_code=course["course_code"],
                    course_name=course["course_name"],
                    department=course["department"],
                    units=course["units"],
                    description=course["description"],
                    prerequisites=course["prerequisites"],
                    offered=course["offered"],
                    offered_qatar=course["offered_qatar"],
                    offered_pitts=course["offered_pitts"],
                    requirements=course["requirements"],
                )
                for course in sorted_courses
            ]
        )


    def fetch_courses_by_requirement(self, cs_requirement=None,
                                     is_requirement=None,
                                     ba_requirement=None,
                                     bs_requirement=None) -> CourseListResponse:
        """fetch and process courses matching requirements."""
        raw_results = self.course_repo.get_courses_by_requirement(cs_requirement, is_requirement,
                                                                  ba_requirement, bs_requirement)

        course_dict: Dict[str, dict] = {}
        for (course_code, course_name, department,
             prerequisites, requirement, audit_id) in raw_results:
            if course_code not in course_dict:
                course_dict[course_code] = {
                    "course_code": course_code,
                    "course_name": course_name,
                    "department": department,
                    "prerequisites": prerequisites or "None",
                    "offered": self.course_repo.get_offered_semesters(course_code),
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

        return CourseListResponse(
            courses=[CourseResponse(**course) for course in course_dict.values()]
        )

    def fetch_courses_by_prerequisite(self, has_prereqs: bool) -> CourseListResponse:
        """fetch and structure courses based on whether they have prerequisites."""
        courses = self.course_repo.get_courses_by_prerequisite(has_prereqs)

        return CourseListResponse(
            courses=[
                CourseResponse(
                    course_code=course["course_code"],
                    course_name=course["course_name"],
                    department=course["department"],
                    units=course["units"],
                    description=course["description"],
                    prerequisites=course["prerequisites"],
                    offered=course["offered"],
                    offered_qatar=course["offered_qatar"],
                    offered_pitts=course["offered_pitts"],
                    requirements=course["requirements"],
                )
                for course in courses
            ]
        )

    def fetch_courses_by_department(self, department: str) -> CourseListResponse:
        """fetch and structure courses filtered by department."""
        courses = self.course_repo.get_courses_by_department(department)

        return CourseListResponse(
            courses=[
                CourseResponse(
                    course_code=course["course_code"],
                    course_name=course["course_name"],
                    department=course["department"],
                    units=course["units"],
                    description=course["description"],
                    prerequisites=course["prerequisites"],
                    offered=course["offered"],
                    offered_qatar=course["offered_qatar"],
                    offered_pitts=course["offered_pitts"],
                    requirements=course["requirements"],
                )
                for course in courses
            ]
        )

    def fetch_courses_by_offered_location(self, offered_in_qatar: bool,
                                          offered_in_pitts: bool) -> CourseListResponse:
        """fetch and process courses filtered by offering location."""
        raw_courses = self.course_repo.get_courses_by_offered_location(offered_in_qatar,
                                                                       offered_in_pitts)
        return CourseListResponse(
            courses=[
                CourseResponse(
                    course_code=c["course_code"],
                    course_name=c["course_name"],
                    department=c["department"],
                    units=c["units"],
                    description=c["description"],
                    prerequisites=c["prerequisites"],
                    offered=c["offered"],
                    offered_qatar=c["offered_qatar"],
                    offered_pitts=c["offered_pitts"],
                    requirements=c["requirements"],
                )
                for c in raw_courses
            ]
        )

    def fetch_courses_by_semester(self, semester: str) -> CourseListResponse:
        """fetch and structure courses offered in the specified semester."""
        courses = self.course_repo.get_courses_by_semester(semester)
        return CourseListResponse(
            courses=[
                CourseResponse(
                    course_code=course["course_code"],
                    course_name=course["course_name"],
                    department=course["department"],
                    units=course["units"],
                    description=course["description"],
                    prerequisites=course["prerequisites"],
                    offered=course["offered"],
                    offered_qatar=course["offered_qatar"],
                    offered_pitts=course["offered_pitts"],
                    requirements=course["requirements"],
                )
                for course in courses
            ]
        )

    def fetch_all_semesters(self):
        """fetch a list of all semesters available in the offerings table."""
        return self.course_repo.get_all_semesters()


    def fetch_courses_by_filters(
    self,
    department: Optional[str] = None,
    semester: Optional[str] = None,
    has_prereqs: Optional[bool] = None,
    cs_requirement: Optional[str] = None,
    is_requirement: Optional[str] = None,
    ba_requirement: Optional[str] = None,
    bs_requirement: Optional[str] = None,
    offered_qatar: Optional[bool] = None,
    offered_pitts: Optional[bool] = None,
    search_query: Optional[str] = None
) -> CourseListResponse:
        """
        Fetch courses based on a combination of filters, sorted by the numeric part
        of the course code.
        """
        courses = self.course_repo.get_courses_by_filters(
            department=department,
            search_query=search_query,
            semester=semester,
            has_prereqs=has_prereqs,
            cs_requirement=cs_requirement,
            is_requirement=is_requirement,
            ba_requirement=ba_requirement,
            bs_requirement=bs_requirement,
            offered_qatar=offered_qatar,
            offered_pitts=offered_pitts
        )

        sorted_courses = sorted(
            courses,
            key=lambda c: int(c["course_code"].replace("-", ""))
        )

        return CourseListResponse(
            courses=[
                CourseResponse(
                    course_code=course["course_code"],
                    course_name=course["course_name"],
                    department=course["department"],
                    units=course["units"],
                    description=course["description"],
                    prerequisites=course["prerequisites"],
                    offered=course["offered"],
                    offered_qatar=course["offered_qatar"],
                    offered_pitts=course["offered_pitts"],
                    requirements=course["requirements"],
                )
                for course in sorted_courses
            ]
        )
