"""
Handles database connections and querying using SQLAlchemy.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from database.models import Base, Course, CountsFor, Requirement, Offering, Prereqs
from sqlalchemy import and_

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///database/gened_db.sqlite")

# Create database engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, echo=True)

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Provides a database session dependency for FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def drop_db():
    """Drops all database tables."""
    Base.metadata.drop_all(engine)
    print("Database tables dropped successfully.")

def init_db():
    """Creates database tables based on SQLAlchemy models."""
    Base.metadata.create_all(engine)
    print("Database tables created successfully.")

if __name__ == "__main__":
    drop_db()  # Drop existing tables
    init_db()  # Recreate tables

def get_course_by_code(db: Session, course_code: str):
    """Fetch course details by course code."""
    course = db.query(Course).filter(Course.course_code == course_code).first()

    if not course:
        return None

    # Get requirements
    requirements_query = (
        db.query(CountsFor.requirement, Requirement.audit_id)
        .join(Requirement, CountsFor.requirement == Requirement.requirement)
        .filter(CountsFor.course_code == course_code)
        .all()
    )

    requirements = {"CS": [], "IS": [], "BA": [], "BS": []}
    for req, audit_id in requirements_query:
        if audit_id.startswith("cs"):
            requirements["CS"].append(req)
        elif audit_id.startswith("is"):
            requirements["IS"].append(req)
        elif audit_id.startswith("ba"):
            requirements["BA"].append(req)
        elif audit_id.startswith("bs"):
            requirements["BS"].append(req)

    # Get offered semesters
    offered_semesters = (
        db.query(Offering.semester)
        .filter(Offering.course_code == course_code)
        .all()
    )
    offered = [semester[0] for semester in offered_semesters]

    # Get prerequisites
    prereqs_query = (
        db.query(Prereqs.prerequisite)
        .filter(Prereqs.course_code == course_code)
        .all()
    )
    prerequisites = ", ".join([p[0] for p in prereqs_query]) if prereqs_query else "None"

    return {
        "course_code": course.course_code,
        "course_name": course.name,
        "requirements": requirements,
        "offered": offered,
        "prerequisites": prerequisites,
    }

def get_courses_by_department(db: Session, department: str):
    """Fetch courses that belong to a specific department."""
    courses = db.query(Course).filter(Course.dep_code == department).all()

    result = []
    for course in courses:
        # Get course requirements
        requirements_query = (
            db.query(CountsFor.requirement, Requirement.audit_id)
            .join(Requirement, CountsFor.requirement == Requirement.requirement)
            .filter(CountsFor.course_code == course.course_code)
            .all()
        )

        requirements = {"CS": [], "IS": [], "BA": [], "BS": []}
        for req, audit_id in requirements_query:
            if audit_id.startswith("cs"):
                requirements["CS"].append(req)
            elif audit_id.startswith("is"):
                requirements["IS"].append(req)
            elif audit_id.startswith("ba"):
                requirements["BA"].append(req)
            elif audit_id.startswith("bs"):
                requirements["BS"].append(req)

        # Get offered semesters
        offered_semesters = (
            db.query(Offering.semester)
            .filter(Offering.course_code == course.course_code)
            .all()
        )
        offered = [semester[0] for semester in offered_semesters]

        # Get prerequisites
        prereqs_query = (
            db.query(Prereqs.prerequisite)
            .filter(Prereqs.course_code == course.course_code)
            .all()
        )
        prerequisites = ", ".join([p[0] for p in prereqs_query]) if prereqs_query else "None"

        result.append({
            "course_code": course.course_code,
            "course_name": course.name,
            "requirements": requirements,
            "offered": offered,
            "prerequisites": prerequisites,
        })

    return result

from sqlalchemy import or_

def get_courses_by_requirement(db: Session, cs_requirement=None, is_requirement=None, ba_requirement=None, bs_requirement=None):
    """Fetch courses that match all specified major requirements (AND filtering)."""

    # Collect requirement filters
    filters = []
    if cs_requirement:
        filters.append(and_(Requirement.audit_id.like("cs%"), CountsFor.requirement == cs_requirement))
    if is_requirement:
        filters.append(and_(Requirement.audit_id.like("is%"), CountsFor.requirement == is_requirement))
    if ba_requirement:
        filters.append(and_(Requirement.audit_id.like("ba%"), CountsFor.requirement == ba_requirement))
    if bs_requirement:
        filters.append(and_(Requirement.audit_id.like("bs%"), CountsFor.requirement == bs_requirement))

    if not filters:
        return []

    # Fetch all courses that match any of the selected requirements
    query = (
        db.query(Course.course_code, Course.name, CountsFor.requirement, Requirement.audit_id)
        .join(CountsFor, Course.course_code == CountsFor.course_code)
        .join(Requirement, CountsFor.requirement == Requirement.requirement)
        .filter(or_(*filters))  # Match any selected requirement
    )

    # Fetch all results
    course_results = query.all()

    # Manually enforce AND filtering
    course_counts = {}
    for course_code, course_name, requirement, audit_id in course_results:
        if course_code not in course_counts:
            course_counts[course_code] = {
                "course_code": course_code,
                "course_name": course_name,
                "requirements": {"CS": [], "IS": [], "BA": [], "BS": []},  # Initialize empty
                "matched_requirements": set()
            }

        # Track which requirements this course fulfills
        course_counts[course_code]["matched_requirements"].add(requirement)

        # Organize requirements by major
        if audit_id.startswith("cs"):
            course_counts[course_code]["requirements"]["CS"].append(requirement)
        elif audit_id.startswith("is"):
            course_counts[course_code]["requirements"]["IS"].append(requirement)
        elif audit_id.startswith("ba"):
            course_counts[course_code]["requirements"]["BA"].append(requirement)
        elif audit_id.startswith("bs"):
            course_counts[course_code]["requirements"]["BS"].append(requirement)

    # Filter out courses that don't match all required filters
    required_filters = {cs_requirement, is_requirement, ba_requirement, bs_requirement} - {None}
    filtered_courses = [
        {
            "course_code": course["course_code"],
            "course_name": course["course_name"],
            "requirements": course["requirements"]
        }
        for course in course_counts.values()
        if required_filters.issubset(course["matched_requirements"])
    ]

    return filtered_courses
