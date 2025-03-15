"""
this script reads data from excel files and inserts them into the database.
"""
import logging
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from .models import Instructor, Course, Offering, Requirement, Audit, CountsFor
from .models import Prereqs, CourseInstructor, Enrollment, Department
from .db import SessionLocal
from .db import init_db

# configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# define the mapping of table names to corresponding sqlalchemy models
tables = {
    "department": Department,
    "instructor": Instructor,
    "course": Course,
    "offering": Offering,
    "requirement": Requirement,
    "audit": Audit,
    "countsfor": CountsFor,
    "prereqs": Prereqs,
    "course_instructor": CourseInstructor,
    "enrollment": Enrollment,
}

def load_excel_data(file_paths=None):
    """loads data from multiple excel files and inserts them into the database."""
    if file_paths is None:
        file_paths = [
            ("department", "data/department/departments.csv"),
            ("instructor", "data/course/Instructor.xlsx"),
            ("course", "data/course/Course.xlsx"),
            ("prereqs", "data/course/Prereqs.xlsx"),
            ("offering", "data/course/Offering.xlsx"),
            ("course_instructor", "data/course/Course_Instructor.xlsx"),
            ("audit", "data/audit/Audit.xlsx"),
            ("requirement", "data/audit/Requirement.xlsx"),
            ("countsfor", "data/audit/CountsFor.xlsx"),
            ("enrollment", "data/enrollment/Enrollment.xlsx"),
        ]

    db: Session = SessionLocal()
    try:
        for table_name, file_path in file_paths:
            model = tables.get(table_name)
            if not model:
                logging.warning("Table %s not found in mapping, skipping", table_name)
                continue

            try:
                if file_path.lower().endswith('.csv'):
                    df = pd.read_csv(file_path)
                else:
                    df = pd.read_excel(file_path)
                records = df.to_dict(orient='records')
            except (OSError, ValueError) as error:
                logging.error("Failed to read file %s: %s", file_path, error)
                continue

            if records:
                try:
                    db.bulk_insert_mappings(model, records)
                    db.commit()
                    logging.info("Successfully inserted data into %s table", table_name)
                except IntegrityError as error:
                    db.rollback()
                    logging.error("Integrity error inserting data into %s: %s", table_name, error)
                except SQLAlchemyError as error:
                    db.rollback()
                    logging.error("SQLAlchemy error inserting data into %s: %s", table_name, error)
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
    load_excel_data()
