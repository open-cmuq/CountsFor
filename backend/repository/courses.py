"""
This script implements the data access layer for courses.
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from backend.database.models import Course, CountsFor, Requirement, Offering

class CourseRepository:
    """Encapsulates all database operations for the 'Course' entity."""

    def __init__(self, db: Session):
        self.db = db

    def get_course_by_code(self, course_code: str):
        """Fetch course details by course code (raw data only)."""
        return self.db.query(Course).filter(Course.course_code == course_code).first()

    def get_all_courses(self):
        """Fetch all courses with their prerequisites and department (raw data only)."""
        return self.db.query(Course).all()

    def get_courses_by_department(self, department: str):
        """Fetch all courses within a department (raw data only)."""
        return self.db.query(Course).filter(Course.dep_code == department).all()

    def get_offered_semesters(self, course_code: str):
        """Fetch semesters in which a course is offered."""
        offered_semesters = (
            self.db.query(Offering.semester)
            .filter(Offering.course_code == course_code)
            .all()
        )
        return [semester[0] for semester in offered_semesters]

    def get_course_requirements(self, course_code: str):
        """Fetch requirements per major for a course."""
        requirements = {"CS": [], "IS": [], "BA": [], "BS": []}
        requirements_query = (
            self.db.query(CountsFor.requirement, Requirement.audit_id)
            .join(Requirement, CountsFor.requirement == Requirement.requirement)
            .filter(CountsFor.course_code == course_code)
            .all()
        )

        for req, audit_id in requirements_query:
            if audit_id.startswith("cs"):
                requirements["CS"].append(req)
            elif audit_id.startswith("is"):
                requirements["IS"].append(req)
            elif audit_id.startswith("ba"):
                requirements["BA"].append(req)
            elif audit_id.startswith("bio"):
                requirements["BS"].append(req)

        return requirements

    def get_courses_by_requirement(self, cs_requirement=None, is_requirement=None, ba_requirement=None, bs_requirement=None):
        """Fetch courses that match all specified major requirements (AND filtering)."""
        filters = []
        if cs_requirement:
            filters.append(and_(Requirement.audit_id.like("cs%"), CountsFor.requirement == cs_requirement))
        if is_requirement:
            filters.append(and_(Requirement.audit_id.like("is%"), CountsFor.requirement == is_requirement))
        if ba_requirement:
            filters.append(and_(Requirement.audit_id.like("ba%"), CountsFor.requirement == ba_requirement))
        if bs_requirement:
            filters.append(and_(Requirement.audit_id.like("bio%"), CountsFor.requirement == bs_requirement))

        if not filters:
            return []

        query = (
            self.db.query(Course.course_code, Course.name, Course.dep_code, Course.prereqs_text, CountsFor.requirement, Requirement.audit_id)
            .join(CountsFor, Course.course_code == CountsFor.course_code)
            .join(Requirement, CountsFor.requirement == Requirement.requirement)
            .filter(or_(*filters))
        )

        return query.all()

    def get_all_requirements(self):
        """Fetch all requirements grouped by major."""
        requirements = self.db.query(Requirement.requirement, Requirement.audit_id).all()
        categorized = {"BA": [], "BS": [], "CS": [], "IS": []}

        for requirement, audit_id in requirements:
            if audit_id.startswith("ba"):
                categorized["BA"].append(requirement)
            elif audit_id.startswith("bio"):
                categorized["BS"].append(requirement)
            elif audit_id.startswith("cs"):
                categorized["CS"].append(requirement)
            elif audit_id.startswith("is"):
                categorized["IS"].append(requirement)

        return categorized

    def get_all_departments(self):
        """Fetch all unique departments from the database."""
        departments = self.db.query(Course.dep_code).distinct().all()
        return [dept[0] for dept in departments]

