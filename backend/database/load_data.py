import logging
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from .models import Instructor, Course, Offering, Requirement, Audit, CountsFor
from .models import Prereqs, CourseInstructor, Enrollment, Department
from .db import SessionLocal
from .db import init_db

# Define the mapping of table names to corresponding SQLAlchemy models
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

def load_data_from_dicts(data_dict: dict[str, list[dict]]) -> None:
    """
    Loads data from a dictionary of table names and list-of-dict records.
    Deduplicates the records before insertion to avoid UNIQUE constraint failures.
    """
    db: Session = SessionLocal()
    try:
        for table_name, records in data_dict.items():
            model = tables.get(table_name)
            if not model or not records:
                logging.info("No records for table %s; skipping.", table_name)
                continue

            df = pd.DataFrame(records).drop_duplicates()
            deduped_records = df.to_dict(orient="records")

            if len(deduped_records) < len(records):
                logging.warning("Dropped %d duplicate rows before inserting into %s",
                                len(records) - len(deduped_records), table_name)

            try:
                db.bulk_insert_mappings(model, deduped_records)
                db.commit()
                logging.info("Inserted %d records into %s table", len(deduped_records), table_name)
            except IntegrityError as error:
                db.rollback()
                logging.error("Integrity error inserting into %s: %s", table_name, error)
            except SQLAlchemyError as error:
                db.rollback()
                logging.error("SQLAlchemy error inserting into %s: %s", table_name, error)
    finally:
        db.close()

def load_data_from_endpoint() -> None:
    """
    Loads data directly from the new extractor endpoints instead of Excel files,
    and inserts the results into the database.
    """
    # Import your new extractor classes
    from backend.scripts.audit_extractor import AuditDataExtractor
    from backend.scripts.course_extractor import CourseDataExtractor
    from backend.scripts.enrollment_extractor import EnrollmentDataExtractor

    # Instantiate the extractors using appropriate paths
    audit_extractor = AuditDataExtractor(audit_base_path="data/audit", course_base_path="data/course")
    course_extractor = CourseDataExtractor(folder_path="data/course/courses", base_dir="data/course")
    enrollment_extractor = EnrollmentDataExtractor()

    # Get data from the endpoints.
    audit_results = audit_extractor.get_results()  # expected keys: "audit", "requirement", "countsfor"
    course_results = course_extractor.get_results()  # expected keys: "course", "prereqs", "offering", "course_instructor", "instructor"
    # For enrollment, if you have an endpoint now, update the call; if not, it still uses Excel.
    enrollment_data = enrollment_extractor.extract_enrollment_data(file_path="data/enrollment/Enrollment.xlsx")

    # Log the results for debugging
    logging.info("Audit extractor results: %s", audit_results)
    logging.info("Course extractor results: %s", course_results)
    logging.info("Enrollment data extracted: %s", enrollment_data if enrollment_data else "No enrollment data")

    # Combine results into a single dictionary mapping table names to records.
    data_dict = {}
    data_dict.update(audit_results)       # keys: audit, requirement, countsfor
    data_dict.update(course_results)      # keys: course, prereqs, offering, course_instructor, instructor
    data_dict["enrollment"] = enrollment_data if isinstance(enrollment_data, list) else []

    # Load department data (if available) from CSV or endpoint
    try:
        dept_df = pd.read_csv("data/department/departments.csv")
        data_dict["department"] = dept_df.to_dict(orient="records")
    except Exception as e:
        logging.error("Error loading department data: %s", e)
        data_dict["department"] = []

    logging.info("Combined data to be loaded: %s", {k: len(v) for k, v in data_dict.items()})

    # Now insert the combined data into the database
    load_data_from_dicts(data_dict)

if __name__ == "__main__":
    # Optionally initialize the database:
    # init_db()
    load_data_from_endpoint()
