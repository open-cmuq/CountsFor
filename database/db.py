"""
Handles database connections and querying using SQLAlchemy.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from database.models import Base, Course, CountsFor, Requirement, Offering, Prereqs

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
