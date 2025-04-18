"""
This script contains the business logic for handling courses.
"""

from typing import Optional
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
    search_query: Optional[str] = None,
    sort_by_reqs: Optional[bool] = False
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

        if sort_by_reqs:
            # Helper to calculate sort keys: (majors_covered, total_reqs_count)
            def calculate_sort_keys(course_dict):
                majors_covered = 0
                total_reqs_count = 0
                reqs_dict = course_dict.get('requirements', {})
                for _, req_list in reqs_dict.items():
                    if req_list: # If the list of requirements for this major is not empty
                        majors_covered += 1
                        total_reqs_count += len(req_list)
                return majors_covered, total_reqs_count

            # Sort using multiple keys:
            # 1. Majors covered (descending)
            # 2. Total requirements count (descending)
            # 3. Course code (ascending - use negative numeric value)
            sorted_courses = sorted(
                courses,
                key=lambda c: (
                    calculate_sort_keys(c)[0], # Majors covered
                    calculate_sort_keys(c)[1], # Total reqs count
                    -int(c["course_code"].replace("-", "")) # Course code (ascending)
                ),
                reverse=True # Apply descending order to primary and secondary keys
            )
        else:
            # Default sort by course code
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
