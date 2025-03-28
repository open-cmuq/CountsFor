"""
This file is used to load data from a dictionary of table names and list-of-dict records.
It updates existing records and inserts new ones.

The data is loaded from the endpoints instead of Excel files,
and inserts the results into the database.
"""

import logging
import pandas as pd
import os
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from backend.scripts.audit_extractor import AuditDataExtractor
from backend.scripts.course_extractor import CourseDataExtractor
from backend.scripts.enrollment_extractor import EnrollmentDataExtractor
from .models import Instructor, Course, Offering, Requirement, Audit, CountsFor
from .models import Prereqs, CourseInstructor, Enrollment, Department
from .db import SessionLocal


UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../temp_uploads"))
print(f"Using upload directory: {UPLOAD_DIR}")
os.makedirs(UPLOAD_DIR, exist_ok=True)

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

primary_keys = {
    "department": ["dep_code"],
    "instructor": ["andrew_id"],
    "course": ["course_code"],
    "offering": ["offering_id"],
    "requirement": ["requirement"],
    "audit": ["audit_id"],
    "countsfor": ["course_code", "requirement"],
    "prereqs": ["course_code", "prerequisite", "group_id"],
    "course_instructor": ["andrew_id", "course_code"],
    "enrollment": ["enrollment_id"]
}

def load_data_from_dicts(data_dict: dict[str, list[dict]]) -> None:
    """
    Loads data from a dictionary of table names and list-of-dict records.
    Updates existing records and inserts new ones.
    """
    db: Session = SessionLocal()
    try:
        print("\n=== Starting data loading process ===")
        print(f"Tables to process: {list(data_dict.keys())}")

        for table_name, records in data_dict.items():
            if table_name == "department":
                print("\nProcessing department table...")
                print(f"Got {len(records)} department records")
                print(f"First record sample: {records[0] if records else None}")
            else:
                print(f"\nProcessing {table_name}...")

            model = tables.get(table_name)
            if not model:
                print(f"Error: No model found for table {table_name}")
                continue
            if not records:
                print(f"Warning: No records for table {table_name}; skipping.")
                continue

            df = pd.DataFrame(records).drop_duplicates()
            deduped_records = df.to_dict(orient="records")
            # Only show deduplication info for department table
            if table_name == "department":
                print(f"After deduplication: {len(deduped_records)} department records")
                if len(deduped_records) < len(records):
                    print(f"Dropped {len(records) - len(deduped_records)} duplicate departments")

            try:
                # Get primary keys for this table
                keys = primary_keys.get(table_name, [])
                # Only show primary key info for department table
                if table_name == "department":
                    print(f"Primary keys for department: {keys}")

                if keys:  # If table has defined primary keys, handle updates
                    for record in deduped_records:
                        # Build filter conditions for all primary keys
                        filter_conditions = []
                        has_all_keys = True
                        for key in keys:
                            if key in record:
                                filter_conditions.append(getattr(model, key) == record[key])
                                # Only show filter conditions for department table
                                if table_name == "department":
                                    print(f"Added filter condition for {key}: {record[key]}")
                            else:
                                has_all_keys = False
                                if table_name == "department":
                                    print(f"Warning: Missing key {key} in record")
                                break

                        if has_all_keys:
                            # Try to find existing record
                            existing = db.query(model).filter(*filter_conditions).first()

                            if existing:
                                # Update existing record
                                key_values = "-".join(str(record.get(key)) for key in keys)
                                if table_name == "department":
                                    print(f"Updating existing department: {key_values}")
                                for key, value in record.items():
                                    setattr(existing, key, value)
                            else:
                                # Insert new record
                                key_values = "-".join(str(record.get(key)) for key in keys)
                                if table_name == "department":
                                    print(f"Creating new department: {key_values}")
                                    print(f"Department data: {record}")
                                new_record = model(**record)
                                db.add(new_record)

                else:
                    if table_name == "department":
                        print(f"Bulk inserting {len(deduped_records)} departments")
                    db.bulk_insert_mappings(model, deduped_records)

                db.commit()
                if table_name == "department":
                    print(f"Successfully processed {len(deduped_records)} departments")

                if keys and table_name == "department":
                    for record in deduped_records:
                        filter_conditions = ([getattr(model, key) == record[key]
                                               for key in keys if key in record])
                        saved_record = db.query(model).filter(*filter_conditions).first()
                        if saved_record:
                            print(f"Verified saved department exists: \
                                  {[f'{k}={getattr(saved_record, k)}' for k in keys]}")
                        else:
                            print(f"Warning: Could not verify saved department:\
                                   {[f'{k}={record[k]}' for k in keys]}")

            except IntegrityError as error:
                db.rollback()
                print(f"Integrity error processing {table_name}: {error}")
                raise
            except SQLAlchemyError as error:
                db.rollback()
                print(f"SQLAlchemy error processing {table_name}: {error}")
                raise
            except Exception as error:
                db.rollback()
                print(f"Unexpected error processing {table_name}: {error}")
                raise
    finally:
        db.close()
        print("\n=== Finished data loading process ===")

def load_data_from_endpoint() -> None:
    """
    Loads data directly from the new extractor endpoints instead of Excel files,
    and inserts the results into the database.
    """
    audit_extractor = AuditDataExtractor(audit_base_path=os.path.join(UPLOAD_DIR, "audit"),
                                          course_base_path=os.path.join(UPLOAD_DIR, "course"))
    course_extractor = CourseDataExtractor(folder_path=os.path.join(UPLOAD_DIR, "course/courses"),
                                            base_dir=os.path.join(UPLOAD_DIR, "course"))
    enrollment_extractor = EnrollmentDataExtractor()

    audit_results = audit_extractor.get_results()
    course_results = course_extractor.get_results()
    enrollment_data = enrollment_extractor.extract_enrollment_data(
        file_path=os.path.join(UPLOAD_DIR, "enrollment/Enrollment.xlsx"))

    logging.info("Audit extractor results: %s", audit_results)
    logging.info("Course extractor results: %s", course_results)
    logging.info("Enrollment data extracted: %s", enrollment_data
                 if enrollment_data else "No enrollment data")

    data_dict = {}
    data_dict.update(audit_results)
    data_dict.update(course_results)
    data_dict["enrollment"] = (enrollment_data
                               if isinstance(enrollment_data, list) else [])

    try:
        dept_df = pd.read_csv(os.path.join(UPLOAD_DIR, "department/departments.csv"))
        data_dict["department"] = dept_df.to_dict(orient="records")
    except FileNotFoundError as e:
        logging.error("Department data file not found: %s", e)
        data_dict["department"] = []
    except pd.errors.EmptyDataError as e:
        logging.error("Department data file is empty: %s", e)
        data_dict["department"] = []
    except Exception as e: # pylint: disable=broad-except
        logging.error("Unexpected error loading department data: %s", e)
        data_dict["department"] = []

    logging.info("Combined data to be loaded: %s", {k: len(v) for k, v in data_dict.items()})

    load_data_from_dicts(data_dict)

if __name__ == "__main__":
    load_data_from_endpoint()
