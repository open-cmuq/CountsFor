"""
this script implements the data access layer for courses.
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from backend.database.models import Course, CountsFor, Requirement

class CourseRepository:
    """ encapsulates all database operations for the 'Course' entity. """
    def __init__(self, db: Session):
        self.db = db

    def get_course_by_code(self, course_code: str):
        """fetch course details by course code."""
        return (
            self.db.query(Course)
            .filter(Course.course_code == course_code)
            .first()
        )

    def get_courses_by_department(self, department: str):
        """fetch all courses within a department."""
        return self.db.query(Course).filter(Course.dep_code == department).all()

    def get_courses_by_requirement(self, cs_requirement=None, is_requirement=None,
                                   ba_requirement=None, bs_requirement=None):
        """fetch courses that match all specified major requirements (AND filtering)."""
        filters = []
        if cs_requirement:
            filters.append(and_(Requirement.audit_id.like("cs%"),
                                CountsFor.requirement == cs_requirement))
        if is_requirement:
            filters.append(and_(Requirement.audit_id.like("is%"),
                                CountsFor.requirement == is_requirement))
        if ba_requirement:
            filters.append(and_(Requirement.audit_id.like("ba%"),
                                CountsFor.requirement == ba_requirement))
        if bs_requirement:
            filters.append(and_(Requirement.audit_id.like("bs%"),
                                CountsFor.requirement == bs_requirement))

        if not filters:
            return []

        query = (
            self.db.query(Course.course_code, Course.name, CountsFor.requirement,
                           Requirement.audit_id)
            .join(CountsFor, Course.course_code == CountsFor.course_code)
            .join(Requirement, CountsFor.requirement == Requirement.requirement)
            .filter(or_(*filters))  # Match any selected requirement
        )

        return query.all()

    def get_all_requirements(self):
        """Fetch all requirements grouped by major."""
        requirements = self.db.query(Requirement.requirement, Requirement.audit_id).all()
        print(requirements)
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
