"""
This script implements the data access layer for courses.
"""

from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from backend.database.models import Course, CountsFor, Requirement, Offering, Audit

class CourseRepository:
    """encapsulates all database operations for the 'Course' entity."""

    def __init__(self, db: Session):
        self.db = db

    def get_course_by_code(self, course_code: str):
        """fetch course details by course code (raw data only)."""
        return self.db.query(Course).filter(Course.course_code == course_code).first()

    def get_all_courses(self):
        """fetch all courses with full details including units, description, and locations."""
        courses = self.db.query(
            Course.course_code,
            Course.name,
            Course.dep_code,
            Course.units,
            Course.description,
            Course.offered_qatar,
            Course.offered_pitts,
            Course.prereqs_text
        ).all()

        result = []
        for course in courses:
            offered_semesters = self.get_offered_semesters(course.course_code)
            requirements = self.get_course_requirements(course.course_code)

            result.append({
                "course_code": course.course_code,
                "course_name": course.name,
                "department": course.dep_code,
                "units": course.units,
                "description": course.description,
                "prerequisites": course.prereqs_text or "None",
                "offered_qatar": course.offered_qatar,
                "offered_pitts": course.offered_pitts,
                "offered": offered_semesters,
                "requirements": requirements,
            })

        return result

    def get_courses_by_department(self, department: str):
        """fetch all courses within a department with full details."""
        courses = self.db.query(Course).filter(Course.dep_code == department).all()

        result = []
        for course in courses:
            offered_semesters = self.get_offered_semesters(course.course_code)
            requirements = self.get_course_requirements(course.course_code)

            result.append({
                "course_code": course.course_code,
                "course_name": course.name,
                "department": course.dep_code,
                "units": course.units,
                "description": course.description,
                "prerequisites": course.prereqs_text or "None",
                "offered_qatar": course.offered_qatar,
                "offered_pitts": course.offered_pitts,
                "offered": offered_semesters,
                "requirements": requirements,
            })

        return result

    def get_offered_semesters(self, course_code: str):
        """fetch semesters in which a course is offered."""
        offered_semesters = (
            self.db.query(Offering.semester)
            .filter(Offering.course_code == course_code)
            .all()
        )
        return [semester[0] for semester in offered_semesters]

    def get_course_requirements(self, course_code: str):
        """fetch requirements per major for a course."""
        requirements = {"CS": [], "IS": [], "BA": [], "BS": []}
        requirements_query = (
            self.db.query(CountsFor.requirement, Requirement.audit_id, Audit.type)
            .join(Requirement, CountsFor.requirement == Requirement.requirement)
            .join(Audit, Requirement.audit_id == Audit.audit_id)
            .filter(CountsFor.course_code == course_code)
            .all()
        )

        for req, audit_id, req_bool in requirements_query:
            if audit_id.startswith("cs"):
                requirements["CS"].append({
                    "requirement": req,
                    "type": bool(req_bool),
                    "major": "CS"
                })
            elif audit_id.startswith("is"):
                requirements["IS"].append({
                    "requirement": req,
                    "type": bool(req_bool),
                    "major": "IS"
                })
            elif audit_id.startswith("ba"):
                requirements["BA"].append({
                    "requirement": req,
                    "type": bool(req_bool),
                    "major": "BA"
                })
            elif audit_id.startswith("bio"):
                requirements["BS"].append({
                    "requirement": req,
                    "type": bool(req_bool),
                    "major": "BS"
                })

        return requirements

    def get_courses_by_requirement(self, cs_requirement=None, is_requirement=None,
                                    ba_requirement=None, bs_requirement=None):
        """fetch courses that match all specified major requirements (AND filtering)."""
        if not any([cs_requirement, is_requirement, ba_requirement, bs_requirement]):
            return []

        # Get the course codes that match each requirement filter
        matching_course_codes = set()
        first_filter = True

        if cs_requirement:
            cs_courses = (
                self.db.query(CountsFor.course_code)
                .join(Requirement, CountsFor.requirement == Requirement.requirement)
                .filter(
                    Requirement.audit_id.like("cs%"),
                    CountsFor.requirement == cs_requirement
                )
                .all()
            )
            cs_codes = set(code[0] for code in cs_courses)
            if first_filter:
                matching_course_codes = cs_codes
                first_filter = False
            else:
                matching_course_codes.intersection_update(cs_codes)

        if is_requirement:
            is_courses = (
                self.db.query(CountsFor.course_code)
                .join(Requirement, CountsFor.requirement == Requirement.requirement)
                .filter(
                    Requirement.audit_id.like("is%"),
                    CountsFor.requirement == is_requirement
                )
                .all()
            )
            is_codes = set(code[0] for code in is_courses)
            if first_filter:
                matching_course_codes = is_codes
                first_filter = False
            else:
                matching_course_codes.intersection_update(is_codes)

        if ba_requirement:
            ba_courses = (
                self.db.query(CountsFor.course_code)
                .join(Requirement, CountsFor.requirement == Requirement.requirement)
                .filter(
                    Requirement.audit_id.like("ba%"),
                    CountsFor.requirement == ba_requirement
                )
                .all()
            )
            ba_codes = set(code[0] for code in ba_courses)
            if first_filter:
                matching_course_codes = ba_codes
                first_filter = False
            else:
                matching_course_codes.intersection_update(ba_codes)

        if bs_requirement:
            bs_courses = (
                self.db.query(CountsFor.course_code)
                .join(Requirement, CountsFor.requirement == Requirement.requirement)
                .filter(
                    Requirement.audit_id.like("bio%"),
                    CountsFor.requirement == bs_requirement
                )
                .all()
            )
            bs_codes = set(code[0] for code in bs_courses)
            if first_filter:
                matching_course_codes = bs_codes
                first_filter = False
            else:
                matching_course_codes.intersection_update(bs_codes)

        if not matching_course_codes:
            return []

        # Get the full details for the matched courses
        query = (
            self.db.query(Course.course_code, Course.name, Course.dep_code,
                        Course.prereqs_text, CountsFor.requirement, Requirement.audit_id)
            .join(CountsFor, Course.course_code == CountsFor.course_code)
            .join(Requirement, CountsFor.requirement == Requirement.requirement)
            .filter(Course.course_code.in_(matching_course_codes))
        )

        return query.all()

    def get_courses_by_prerequisite(self, has_prereqs: bool):
        """fetch courses that either have or do not have prerequisites."""
        query = self.db.query(Course).filter(
            (Course.prereqs_text.isnot(None) & (Course.prereqs_text != "")) if has_prereqs else
            ((Course.prereqs_text.is_(None)) | (Course.prereqs_text == ""))
        )

        result = []
        for course in query.all():
            offered_semesters = self.get_offered_semesters(course.course_code)
            requirements = self.get_course_requirements(course.course_code)

            result.append({
                "course_code": course.course_code,
                "course_name": course.name,
                "department": course.dep_code,
                "units": course.units,
                "description": course.description,
                "prerequisites": course.prereqs_text if has_prereqs else "None",
                "offered_qatar": course.offered_qatar,
                "offered_pitts": course.offered_pitts,
                "offered": offered_semesters,
                "requirements": requirements,
            })

        return result

    def get_courses_by_offered_location(self, offered_in_qatar: bool, offered_in_pitts: bool):
        """fetch courses filtered by offering in Qatar and/or Pittsburgh."""
        query = self.db.query(Course)

        # Apply AND conditions based on input
        if offered_in_qatar is not None:
            query = query.filter(Course.offered_qatar == offered_in_qatar)
        if offered_in_pitts is not None:
            query = query.filter(Course.offered_pitts == offered_in_pitts)

        result = []
        for course in query.all():
            offered_semesters = self.get_offered_semesters(course.course_code)
            requirements = self.get_course_requirements(course.course_code)

            result.append({
                "course_code": course.course_code,
                "course_name": course.name,
                "department": course.dep_code,
                "units": course.units,
                "description": course.description,
                "prerequisites": course.prereqs_text or "None",
                "offered_qatar": course.offered_qatar,
                "offered_pitts": course.offered_pitts,
                "offered": offered_semesters,
                "requirements": requirements,
            })

        return result

    def get_courses_by_semester(self, semester: str):
        """fetch courses that are offered in the given semester."""
        courses = (
            self.db.query(Course)
            .join(Offering, Course.course_code == Offering.course_code)
            .filter(Offering.semester == semester)
            .all()
        )
        result = []
        for course in courses:
            offered_semesters = self.get_offered_semesters(course.course_code)
            requirements = self.get_course_requirements(course.course_code)
            result.append({
                "course_code": course.course_code,
                "course_name": course.name,
                "department": course.dep_code,
                "units": course.units,
                "description": course.description,
                "prerequisites": course.prereqs_text or "None",
                "offered_qatar": course.offered_qatar,
                "offered_pitts": course.offered_pitts,
                "offered": offered_semesters,
                "requirements": requirements,
            })
        return result

    def get_all_semesters(self):
        """fetch a distinct list of all semesters from the Offerings table."""
        semesters = self.db.query(Offering.semester).distinct().all()
        # Each row is a tuple (semester,), so extract the first element.
        return [semester[0] for semester in semesters]

    def get_courses_by_filters(self,
                            department: Optional[str] = None,
                            search_query: Optional[str] = None,
                            semester: Optional[str] = None,
                            has_prereqs: Optional[bool] = None,
                            cs_requirement: Optional[str] = None,
                            is_requirement: Optional[str] = None,
                            ba_requirement: Optional[str] = None,
                            bs_requirement: Optional[str] = None,
                            offered_qatar: Optional[bool] = None,
                            offered_pitts: Optional[bool] = None):
        """Fetch courses matching any combination of provided filters."""
        query = self.db.query(Course)

        # Filter by department.
        if department:
            query = query.filter(Course.dep_code == department)

        # Filter by search query on course code.
        if search_query:
            query = query.filter(Course.course_code.ilike(f"%{search_query}%"))

        # Filter by prerequisites.
        if has_prereqs is not None:
            if has_prereqs:
                query = query.filter(
                    Course.prereqs_text.isnot(None),
                    Course.prereqs_text != "",
                    Course.prereqs_text != "None"
                )
            else:
                query = query.filter(
                    (Course.prereqs_text.is_(None)) | (Course.prereqs_text == "")
                      | (Course.prereqs_text == "None")
                )

        # For requirement filtering, we need to get the course codes that match ALL requirements
        # We'll collect them per major and then use the intersection
        requirement_matching_course_codes = []

        # CS requirements
        if cs_requirement:
            cs_reqs = [r.strip() for r in cs_requirement.split(",") if r.strip()]
            if cs_reqs:
                cs_matches = set()
                for cs_req in cs_reqs:
                    cs_subquery = (
                        self.db.query(CountsFor.course_code)
                        .join(Requirement, CountsFor.requirement == Requirement.requirement)
                        .filter(
                            Requirement.audit_id.like("cs%"),
                            CountsFor.requirement == cs_req
                        )
                    )
                    cs_courses = [code[0] for code in cs_subquery.all()]
                    if not cs_matches:
                        cs_matches = set(cs_courses)
                    else:
                        cs_matches.intersection_update(cs_courses)

                if cs_matches:
                    requirement_matching_course_codes.append(list(cs_matches))

        # IS requirements
        if is_requirement:
            is_reqs = [r.strip() for r in is_requirement.split(",") if r.strip()]
            if is_reqs:
                is_matches = set()
                for is_req in is_reqs:
                    is_subquery = (
                        self.db.query(CountsFor.course_code)
                        .join(Requirement, CountsFor.requirement == Requirement.requirement)
                        .filter(
                            Requirement.audit_id.like("is%"),
                            CountsFor.requirement == is_req
                        )
                    )
                    is_courses = [code[0] for code in is_subquery.all()]
                    if not is_matches:
                        is_matches = set(is_courses)
                    else:
                        is_matches.intersection_update(is_courses)

                if is_matches:
                    requirement_matching_course_codes.append(list(is_matches))

        # BA requirements
        if ba_requirement:
            ba_reqs = [r.strip() for r in ba_requirement.split(",") if r.strip()]
            if ba_reqs:
                ba_matches = set()
                for ba_req in ba_reqs:
                    ba_subquery = (
                        self.db.query(CountsFor.course_code)
                        .join(Requirement, CountsFor.requirement == Requirement.requirement)
                        .filter(
                            Requirement.audit_id.like("ba%"),
                            CountsFor.requirement == ba_req
                        )
                    )
                    ba_courses = [code[0] for code in ba_subquery.all()]
                    if not ba_matches:
                        ba_matches = set(ba_courses)
                    else:
                        ba_matches.intersection_update(ba_courses)

                if ba_matches:
                    requirement_matching_course_codes.append(list(ba_matches))

        # BS requirements
        if bs_requirement:
            bs_reqs = [r.strip() for r in bs_requirement.split(",") if r.strip()]
            if bs_reqs:
                bs_matches = set()
                for bs_req in bs_reqs:
                    bs_subquery = (
                        self.db.query(CountsFor.course_code)
                        .join(Requirement, CountsFor.requirement == Requirement.requirement)
                        .filter(
                            Requirement.audit_id.like("bio%"),
                            CountsFor.requirement == bs_req
                        )
                    )
                    bs_courses = [code[0] for code in bs_subquery.all()]
                    if not bs_matches:
                        bs_matches = set(bs_courses)
                    else:
                        bs_matches.intersection_update(bs_courses)

                if bs_matches:
                    requirement_matching_course_codes.append(list(bs_matches))

        # If we have requirement filters, apply them to the main query
        if requirement_matching_course_codes:
            # Start with the first set of matching courses
            matching_course_codes = set(requirement_matching_course_codes[0])

            # Intersect with each additional set to get courses matching ALL requirements
            for codes in requirement_matching_course_codes[1:]:
                matching_course_codes.intersection_update(codes)

            # Apply the filter to the main query
            if matching_course_codes:
                query = query.filter(Course.course_code.in_(matching_course_codes))
            else:
                # If no courses match all requirements, return empty result
                return []

        if offered_qatar is True and offered_pitts is True:
            if semester:
                semester_list = [s.strip() for s in semester.split(",") if s.strip()]
                if semester_list:
                    subq = self.db.query(Offering.course_code).filter(
                        Offering.semester.in_(semester_list)
                    ).subquery()
                    query = query.filter(Course.course_code.in_(subq))
        elif offered_qatar is not None or offered_pitts is not None:
            location_conditions = []
            if offered_qatar:
                location_conditions.append(Offering.campus_id == 2)
            if offered_pitts:
                location_conditions.append(Offering.campus_id == 1)
            subq = self.db.query(Offering.course_code)
            if semester:
                semester_list = [s.strip() for s in semester.split(",") if s.strip()]
                if semester_list:
                    subq = subq.filter(Offering.semester.in_(semester_list))
            if location_conditions:
                subq = subq.filter(or_(*location_conditions))
            subq = subq.subquery()
            query = query.filter(Course.course_code.in_(subq))
        elif semester:
            semester_list = [s.strip() for s in semester.split(",") if s.strip()]
            if semester_list:
                subq = self.db.query(Offering.course_code).filter(
                    Offering.semester.in_(semester_list)
                ).subquery()
                query = query.filter(Course.course_code.in_(subq))
        courses = query.distinct().all()

        result = []
        for course in courses:
            offered_semesters = self.get_offered_semesters(course.course_code)
            requirements = self.get_course_requirements(course.course_code)
            result.append({
                "course_code": course.course_code,
                "course_name": course.name,
                "department": course.dep_code,
                "units": course.units,
                "description": course.description,
                "prerequisites": course.prereqs_text or "None",
                "offered_qatar": course.offered_qatar,
                "offered_pitts": course.offered_pitts,
                "offered": offered_semesters,
                "requirements": requirements,
            })
        return result
