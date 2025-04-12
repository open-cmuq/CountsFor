"""
This file is used to load data from a dictionary of table names and list-of-dict records.
It updates existing records and inserts new ones.

The data is loaded from the endpoints instead of Excel files,
and inserts the results into the database.
"""

import logging
import os
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from backend.scripts.audit_extractor import AuditDataExtractor
from backend.scripts.course_extractor import CourseDataExtractor
from backend.scripts.enrollment_extractor import EnrollmentDataExtractor
from .models import Instructor, Course, Offering, Requirement, Audit, CountsFor
from .models import Prereqs, CourseInstructor, Enrollment, Department
from .db import SessionLocal
from .to_csv import export_tables_to_csv

# Set up logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define the centralized data directory
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data"))
os.makedirs(DATA_DIR, exist_ok=True)

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

def _ensure_offerings_exist(db: Session, enrollment_records: list[dict]) -> None:
    """
    Checks enrollment records and creates missing Offering records in the database.
    This ensures that enrollment data can be linked to a valid offering.
    """
    if not enrollment_records:
        return

    logging.info("Ensuring necessary Offering records exist for enrollment data...")
    semester_course_combos = set()
    courses_to_check = set()

    for record in enrollment_records:
        semester = record.get('semester')
        course_code = record.get('course_code')
        if semester and course_code:
            semester_course_combos.add((semester, course_code))
            courses_to_check.add(course_code)

    if not semester_course_combos:
        logging.warning("No valid semester/course combinations found in enrollment records.")
        return

    # Pre-fetch existing courses to minimize DB calls inside loop
    existing_db_courses = set()
    if courses_to_check:
        course_results = db.query(Course.course_code).filter(Course.course_code.in_(courses_to_check)).all()
        existing_db_courses = {c[0] for c in course_results}

    # Pre-fetch existing offerings
    existing_offerings = set()
    if semester_course_combos:
        # Build query dynamically might be complex, fetch all relevant and filter in memory
        # Or fetch in chunks if memory is a concern
        relevant_offerings = db.query(Offering.semester, Offering.course_code).filter(
            Offering.course_code.in_(courses_to_check)
        ).all()
        existing_offerings = {(o.semester, o.course_code) for o in relevant_offerings}

    offerings_to_add = []
    for semester, course_code in semester_course_combos:
        if (semester, course_code) not in existing_offerings:
            # Check if the course itself exists in the database before creating offering
            if course_code in existing_db_courses:
                offering_id = f"{course_code}_{semester}_2" # Assume campus_id 2 (Qatar)
                offerings_to_add.append(Offering(
                    offering_id=offering_id,
                    semester=semester,
                    course_code=course_code,
                    campus_id=2  # Default campus_id for Qatar
                ))
            else:
                logging.warning("Cannot create offering for (%s, %s) because Course %s does not exist.",
                                semester, course_code, course_code)

    if offerings_to_add:
        try:
            db.bulk_save_objects(offerings_to_add)
            db.commit()
            logging.info("Created %d missing Offering records.", len(offerings_to_add))
        except (IntegrityError, SQLAlchemyError) as e:
            db.rollback()
            logging.error("Error creating missing Offering records: %s", e)
            # Propagate the error or handle as needed - potentially raise?

def load_data_from_dicts(data_dict: dict[str, list[dict]]) -> None:
    """
    Loads data from a dictionary of table names and list-of-dict records.
    Updates existing records and inserts new ones.
    """
    db: Session = SessionLocal()
    try:
        logging.info("Loading data from dictionaries...")

        # Pre-process: Ensure offerings exist for enrollment data
        if "enrollment" in data_dict:
            _ensure_offerings_exist(db, data_dict["enrollment"])

        # Process tables in a specific order to handle dependencies
        table_order = ["department", "instructor", "course", "offering", "audit",
                       "requirement", "prereqs", "countsfor", "course_instructor", "enrollment"]

        # Cache fetched offerings to reduce DB lookups inside the enrollment loop
        offering_cache = {}

        # --- Temporarily reduce logging --- #
        # log_tables = {"course", "offering", "audit", "requirement", "prereqs", "countsfor", "course_instructor", "instructor"}
        # Enable logging specifically for audit related tables
        log_tables = {"audit", "requirement", "countsfor"}

        for table_name in table_order:
            records = data_dict.get(table_name, [])
            if not records:
                continue

            # --- Temporarily reduce logging --- #
            if table_name in log_tables:
                logging.info("Processing table: %s with %d records", table_name, len(records))

            model = tables.get(table_name)
            if not model:
                # --- Temporarily reduce logging --- #
                # logging.warning("No model found for table: %s. Skipping.", table_name)
                continue

            # Basic deduplication based on all columns before processing
            try:
                df = pd.DataFrame(records)
                df.dropna(axis=1, how='all', inplace=True)
                pk = primary_keys.get(table_name)
                if pk and all(k in df.columns for k in pk):
                    df.drop_duplicates(subset=pk, keep='last', inplace=True)
                else:
                    df.drop_duplicates(keep='last', inplace=True)
                deduped_records = df.to_dict(orient="records")
            except Exception as e:
                # --- Temporarily reduce logging --- #
                # logging.error("Error during DataFrame processing for %s: %s. Using raw records.", table_name, e)
                deduped_records = records

            if not deduped_records:
                # --- Temporarily reduce logging --- #
                # logging.info("No records remaining for %s after deduplication.", table_name)
                continue

            # Special handling for enrollment (linking offering_id)
            if table_name == "enrollment":
                processed_enrollment = []
                for record in deduped_records:
                    record["class_"] = int(record.get("class_", 0))
                    record["enrollment_count"] = int(record.get("enrollment_count", 0))

                    semester = record.get("semester")
                    course_code = record.get("course_code")
                    offering_id = None

                    if semester and course_code:
                        cache_key = (semester, course_code)
                        if cache_key in offering_cache:
                            offering_id = offering_cache[cache_key]
                        else:
                            offering = db.query(Offering.offering_id).filter(
                                Offering.course_code == course_code,
                                Offering.semester == semester
                            ).first()
                            if offering:
                                offering_id = offering.offering_id
                                offering_cache[cache_key] = offering_id
                            # else:
                                # logging.warning("Offering not found for enrollment record (%s, %s), skipping record.", semester, course_code)
                                # continue
                    # else:
                        # logging.warning("Enrollment record missing semester/course_code: %s", record)
                        # continue

                    if not offering_id:
                        continue # Skip if offering couldn't be found

                    record["offering_id"] = offering_id

                    original_keys = list(record.keys())
                    for key in original_keys:
                        if not hasattr(model, key) and key != 'class_':
                            del record[key]

                    if "enrollment_id" not in record and record.get("offering_id"):
                        section = record.get("section", "")
                        class_val = record.get("class_", "")
                        department = record.get("department", "")
                        record["enrollment_id"] = f"{record['offering_id']}_{class_val}_{section}_{department}"
                    elif "enrollment_id" not in record:
                        # logging.warning("Could not generate enrollment_id for record: %s", record)
                        continue

                    processed_enrollment.append(record)
                deduped_records = processed_enrollment

            keys = primary_keys.get(table_name)
            if not keys:
                # --- Temporarily reduce logging --- #
                # logging.warning("No primary keys defined for %s. Bulk inserting...", table_name)
                try:
                    db.bulk_insert_mappings(model, deduped_records)
                    db.commit()
                except (IntegrityError, SQLAlchemyError) as error:
                    db.rollback()
                    # logging.error("Error bulk inserting into %s: %s", table_name, error)
                continue

            successful_upserts = 0
            failed_upserts = 0
            for record in deduped_records:
                try:
                    filter_conditions = {}
                    has_all_keys = True
                    for key in keys:
                        if key in record and record[key] is not None:
                            filter_conditions[key] = record[key]
                        else:
                            # logging.warning("Skipping record in %s due to missing PK '%s': %s", table_name, key, record)
                            has_all_keys = False
                            break

                    if not has_all_keys:
                        failed_upserts += 1
                        continue

                    instance_data = record.copy()
                    for key in filter_conditions:
                        if key in instance_data:
                            del instance_data[key]

                    instance_to_merge = model(**filter_conditions)
                    for key, value in instance_data.items():
                        attr_name = 'class_' if table_name == 'enrollment' and key == 'class' else key
                        if hasattr(instance_to_merge, attr_name):
                            setattr(instance_to_merge, attr_name, value)
                        # else:
                            # logging.warning("Model %s missing attr %s from key %s", table_name, attr_name, key)

                    db.merge(instance_to_merge)
                    successful_upserts += 1

                except SQLAlchemyError as e:
                    # logging.error("Error merging record into %s: %s Record: %s", table_name, e, record)
                    failed_upserts += 1
                    db.rollback()

            try:
                db.commit() # Commit all successful merges for the table
                # --- Temporarily reduce logging --- #
                # Log commit success specifically for offering and enrollment
                if table_name in log_tables or table_name in ["offering", "enrollment"]:
                    logging.info("COMMIT SUCCEEDED for table %s: %d records successfully merged, %d failed.",
                                 table_name, successful_upserts, failed_upserts)
            except SQLAlchemyError as e:
                # logging.error("Error committing merges for table %s: %s", table_name, e)
                db.rollback()

    except Exception as e:
        logging.exception("An unexpected error occurred during data loading: %s", e)
        db.rollback()
    finally:
        # --- Temporarily reduce logging --- #
        # logging.info("Exporting tables to CSV...")
        # try:
        #     export_tables_to_csv(session=db)
        # except Exception as csv_e:
        #      logging.error("CSV Export failed: %s", csv_e)
        db.close()
        logging.info("Database session closed.")

def load_data_from_endpoint() -> None:
    """
    Placeholder function to simulate loading data fetched from an endpoint.
    Loads data sequentially: Courses first, then Audits, ensuring dependencies.
    """
    logging.info("--- Starting Data Loading from Endpoint Simulation ---")

    # --- 0. Process and Load Department Data --- #
    department_dir = os.path.join(DATA_DIR, "departments")
    department_data_path = None
    if os.path.exists(department_dir) and os.path.isdir(department_dir):
        csv_files = [f for f in os.listdir(department_dir) if f.endswith('.csv') and os.path.isfile(os.path.join(department_dir, f))]
        if len(csv_files) == 1:
            department_data_path = os.path.join(department_dir, csv_files[0])
            logging.info(f"Found department CSV: {csv_files[0]}")
        elif len(csv_files) > 1:
            logging.warning(f"Multiple CSV files found in {department_dir}. Using the first one found: {csv_files[0]}")
            department_data_path = os.path.join(department_dir, csv_files[0])
        else:
            logging.warning(f"No CSV file found in department directory: {department_dir}")
    else:
        logging.warning(f"Department data directory not found or is not a directory: {department_dir}")

    if department_data_path:
        try:
            logging.info("Processing Department data from %s", department_data_path)
            dept_df = pd.read_csv(department_data_path)
            # Ensure columns match the Department model (name, dep_code)
            if "name" in dept_df.columns and "dep_code" in dept_df.columns:
                # Convert dep_code to string if it's not already, handle potential float conversion from CSV read
                dept_df["dep_code"] = dept_df["dep_code"].astype(str)
                department_records = dept_df[["name", "dep_code"]].to_dict(orient="records")
                if department_records:
                    logging.info("Loading Department data into the database...")
                    load_data_from_dicts({"department": department_records})
                    logging.info("Finished loading Department data.")
                else:
                    logging.warning("No department records found in the CSV.")
            else:
                logging.warning("Department CSV missing required columns ('name', 'dep_code').")
        except Exception as e:
            logging.error("Failed to process or load department data from %s: %s", department_data_path, e)
    # else: Department data path was not set, warnings logged above

    all_course_data = {}
    all_audit_data = {}
    db_course_codes = set()

    # --- 1. Process and Load Course Data --- #
    course_data_dir = os.path.join(DATA_DIR, "courses")
    if os.path.exists(course_data_dir):
        try:
            logging.info("Processing Course data from %s", course_data_dir)
            course_extractor = CourseDataExtractor(folder_path=course_data_dir, base_dir=DATA_DIR)
            course_extractor.process_all_courses()
            all_course_data = course_extractor.get_results()

            if all_course_data:
                logging.info("Loading Course related data into the database...")
                # Select only course-related keys for the first load
                course_keys = {"course", "instructor", "offering", "prereqs", "course_instructor"}
                data_to_load_now = {k: v for k, v in all_course_data.items() if k in course_keys}
                if data_to_load_now:
                    load_data_from_dicts(data_to_load_now)
                    logging.info("Finished loading Course related data.")
                else:
                    logging.warning("No course-related data found to load initially.")
            else:
                logging.warning("Course extractor returned no data.")

        except Exception as e:
            logging.error("Failed to process or load course data from %s: %s", course_data_dir, e)
    else:
        logging.warning("Course data directory not found or empty: %s", course_data_dir)

    # --- 2. Fetch Course Codes (after loading course data) --- #
    db_session = SessionLocal()
    try:
        logging.info("Fetching existing course codes from database...")
        course_results = db_session.query(Course.course_code).all()
        db_course_codes = {c[0] for c in course_results}
        logging.info("Found %d existing course codes.", len(db_course_codes))
        if not db_course_codes:
            logging.warning("No course codes found in DB after attempting course load! Audit data cannot be linked.")
    except Exception as e:
        logging.error("Failed to fetch course codes from database: %s. Audit results may be incomplete.", e)
    finally:
        if db_session:
            db_session.close()

    # --- 3. Process and Load Audit Data --- #
    audit_data_dir = os.path.join(DATA_DIR, "audit")
    if os.path.exists(audit_data_dir):
        # Only proceed if we have course codes to validate against
        if db_course_codes:
            try:
                logging.info("Processing Audit data from %s", audit_data_dir)
                audit_extractor = AuditDataExtractor(audit_base_path=audit_data_dir)
                # Pass the fetched course codes
                all_audit_data = audit_extractor.get_results(db_course_codes=db_course_codes)

                if all_audit_data:
                    logging.info("Loading Audit related data into the database...")
                    # Select only audit-related keys for the second load
                    audit_keys = {"audit", "requirement", "countsfor"}
                    data_to_load_now = {k: v for k, v in all_audit_data.items() if k in audit_keys}
                    if data_to_load_now:
                        # Log counts before loading
                        logging.info("Audit Extractor produced counts: %s",
                                     {k: len(v) for k, v in data_to_load_now.items()})
                        load_data_from_dicts(data_to_load_now)
                        logging.info("Finished loading Audit related data.")
                    else:
                        logging.warning("No audit-related data found to load.")
                else:
                    logging.warning("Audit extractor returned no data.")

            except Exception as e:
                logging.error("Failed to process or load audit data from %s: %s", audit_data_dir, e)
        else:
            logging.warning("Skipping Audit data processing because no course codes were found in the database.")
    else:
        logging.warning("Audit data directory not found: %s", audit_data_dir)

    # --- 4. Process and Load Other Data (Optional - Deprecated Logging/Loading) --- #
    # Load Enrollment data if needed (currently commented out)

    logging.info("--- Finished Data Loading from Endpoint Simulation ---")

# Example usage (optional, for testing)
if __name__ == "__main__":
    # You might want to reset the DB before loading if needed
    from .db import reset_db
    reset_db()
    load_data_from_endpoint()
