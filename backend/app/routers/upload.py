"""
This file is used to upload data to the database.
It handles the upload of department CSV, course ZIP files, audit ZIP files,
and enrollment Excel file.
"""

import shutil
import os
import zipfile
import logging
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
import pandas as pd
from sqlalchemy.exc import SQLAlchemyError
from backend.scripts.course_extractor import CourseDataExtractor
from backend.scripts.audit_extractor import AuditDataExtractor
from backend.scripts.enrollment_extractor import EnrollmentDataExtractor
from backend.database.load_data import load_data_from_dicts
from backend.database.db import reset_db, SessionLocal
from backend.database.models import Department


router = APIRouter()

# Set up logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Use absolute path for UPLOAD_DIR
UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data"))
print(f"Using data directory: {UPLOAD_DIR}")
os.makedirs(UPLOAD_DIR, exist_ok=True)

def unzip_and_flatten(zip_path: str, extract_to: str):
    """
    Unzips a ZIP file and flattens it into a directory.
    """
    base_name = os.path.splitext(os.path.basename(zip_path))[0]
    temp_extract_path = os.path.join(UPLOAD_DIR, f"{base_name}_temp_extract")
    os.makedirs(temp_extract_path, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(temp_extract_path)

    print("Extracted files:", os.listdir(temp_extract_path))

    for root, dirs, files in os.walk(temp_extract_path):
        # Ignore __MACOSX and hidden files
        dirs[:] = [d for d in dirs if not d.startswith("__MACOSX") and not d.startswith(".")]
        files = [f for f in files if not f.startswith(".")]
        for file in files:
            src = os.path.join(root, file)
            dest = os.path.join(extract_to, os.path.relpath(src, temp_extract_path))
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.move(src, dest)
    shutil.rmtree(temp_extract_path)

async def validate_upload_file(file: Optional[UploadFile] = File(None)) -> Optional[UploadFile]:
    """Validate that the uploaded file is not empty and has a filename."""
    print(f"\nValidating file: {file.filename if file else None}")  # Debug log
    if not file:
        print("No file provided")
        return None

    print(f"File content type: {file.content_type}")
    print(f"File size: {file.size if hasattr(file, 'size') else 'unknown'}")

    if not file.filename:
        print("Error: File has no filename")
        raise HTTPException(status_code=400, detail="File has no filename")

    if file.filename.endswith('.csv') and not file.content_type in ['text/csv',
                                                                    'application/vnd.ms-excel']:
        print(f"Warning: CSV file has unexpected content type: {file.content_type}")

    return file  # Return the file object

def validate_zip_content(zip_path: str, expected_type: str) -> bool:
    """Validate that a ZIP file contains the expected type of data."""
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        file_list = zip_ref.namelist()

        if expected_type == "course":
            # Check for course JSON files
            return any(f.endswith('.json') and not f.startswith('__MACOSX') for f in file_list)
        elif expected_type == "audit":
            # Check for audit JSON files
            return any(f.endswith('.json') and not f.startswith('__MACOSX') for f in file_list)
        return False

@router.post(
    "/upload/init-db/",
    summary="Upload and Initialize Database",
    description="""
    Upload files to initialize or update the database. Accepts:
    - Department CSV file (columns: dep_code, name)
    - Course ZIP files (containing JSON course data)
    - Audit ZIP files (containing JSON audit data)
    - Enrollment Excel file

    You can upload any combination of these files. The department CSV should be uploaded first
    as it's a dependency for courses.
    """,
    response_description="Returns a list of successfully loaded data types"
)
async def initialize_database(
    course_zips: Optional[List[UploadFile]] = File(
        None,
        description="ZIP files containing course JSON data"
    ),
    audit_zips: Optional[List[UploadFile]] = File(
        None,
        description="ZIP files containing audit JSON data"
    ),
    enrollment_file: Optional[UploadFile] = File(
        None,
        description="Excel file containing enrollment data"
    ),
    department_csv: Optional[UploadFile] = File(
        None,
        description="CSV file containing department data (columns: dep_code, name)"
    ),
    reset: bool = Form(
        False,
        description="If true, resets the database before loading new data"
    )
):
    """
    Initialize or update the database with uploaded files.
    """
    logging.info("=== Starting Database Initialization ===")
    logging.info("Received files:")
    logging.info("Course zips: %s", [f.filename for f in course_zips] if course_zips else [])
    logging.info("Audit zips: %s", [f.filename for f in audit_zips] if audit_zips else [])
    logging.info("Enrollment file: %s", enrollment_file.filename if enrollment_file else None)
    logging.info("Department CSV: %s", department_csv.filename if department_csv else None)
    logging.info("Reset flag: %s", reset)

    if reset:
        logging.info("Resetting database...")
        reset_db()
        return {"message": "Database reset successfully"}

    # Filter out None values and empty files
    files_to_process = {
        "course_zips": [f for f in course_zips if f and f.filename] if course_zips else [],
        "audit_zips": [f for f in audit_zips if f and f.filename] if audit_zips else [],
        "enrollment_file": enrollment_file,
        "department_csv": department_csv
    }

    logging.info("Files to process: %s", files_to_process)

    if not any(files_to_process.values()):
        logging.warning("No valid files found in the request")
        raise HTTPException(
            status_code=400,
            detail="No valid files provided for upload. Please ensure at least one file is selected"
        )

    results = {"message": "Data loaded successfully", "loaded_data": []}

    # Handle Department CSV first as it's a dependency for courses
    if files_to_process["department_csv"]:
        logging.info("Processing department CSV...")

        # Ensure temp directory exists and is absolute
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        print(f"Temp directory absolute path: {os.path.abspath(UPLOAD_DIR)}")
        print(f"Temp directory exists: {os.path.exists(UPLOAD_DIR)}")
        print(f"Temp directory is writable: {os.access(UPLOAD_DIR, os.W_OK)}")

        dept_csv_path = os.path.join(UPLOAD_DIR, "departments.csv")
        logging.info("Saving department CSV to: %s", dept_csv_path)

        try:
            # Read the file content
            file = files_to_process["department_csv"]
            print(f"File details - Name: {file.filename}, Content-Type: {file.content_type}")

            contents = await file.read()
            print(f"Read {len(contents)} bytes from department CSV")
            print(f"Content preview: {contents[:200].decode('utf-8')}")

            if len(contents) == 0:
                raise ValueError("Department CSV file is empty")

            # Write contents to temp file
            try:
                with open(dept_csv_path, "wb") as f:
                    f.write(contents)
                print(f"Successfully wrote file to {dept_csv_path}")

                # Verify file was written
                if os.path.exists(dept_csv_path):
                    file_size = os.path.getsize(dept_csv_path)
                    print(f"File exists at {dept_csv_path}, size: {file_size} bytes")

                    # Read back first few bytes to verify content
                    with open(dept_csv_path, "rb") as f:
                        first_bytes = f.read(100)
                        print(f"First 100 bytes of written file: {first_bytes}")
                else:
                    raise ValueError(f"Failed to write file to {dept_csv_path}")
            except IOError as e:
                print(f"Error writing file: {str(e)}")
                raise ValueError(f"Failed to write department CSV: {str(e)}") from e

            # Read and validate CSV
            try:
                print(f"Reading CSV from {dept_csv_path}")
                dept_df = pd.read_csv(dept_csv_path)
                print(f"CSV read successfully with {len(dept_df)} rows")
                print(f"Original columns: {dept_df.columns.tolist()}")

                # Check for required columns with flexible naming
                if 'dep_code' not in dept_df.columns and 'dep_code' not in dept_df.columns:
                    raise ValueError("Missing department code column. Expected 'dep_code'")
                if 'name' not in dept_df.columns:
                    raise ValueError("Missing name column. Expected 'name'")

                # Ensure correct column order and names
                dept_df = dept_df[['name', 'dep_code']]
                dept_df.columns = ['name', 'dep_code']  # Standardize column names

                # Remove any empty rows
                dept_df = dept_df.dropna(subset=['dep_code', 'name'])
                print(f"After removing empty rows: {len(dept_df)} rows")
                print("Sample of processed data:")
                print(dept_df.head().to_string())

                if len(dept_df) == 0:
                    raise ValueError("No valid department records found in CSV")

                # Convert to records
                dept_records = dept_df.to_dict(orient="records")
                print(f"First few records: {dept_records[:2]}")

                # Load into database
                print("Loading records into database...")
                try:
                    # Create a new session for this operation
                    db = SessionLocal()
                    try:
                        # First, try to load using load_data_from_dicts
                        load_data_from_dicts({"department": dept_records})
                        print("Successfully loaded department data using load_data_from_dicts")

                        # Verify the data was loaded
                        loaded_depts = db.query(Department).all()
                        print(f"Verified {len(loaded_depts)} departments in database:")
                        for dept in loaded_depts[:5]:  # Show first 5 as sample
                            print(f"  - {dept.dep_code}: {dept.name}")

                    except SQLAlchemyError as db_error:
                        print(f"Error during database load with load_data_from_dicts: \
                              {str(db_error)}")
                        print("Attempting direct database insert...")

                        # Fallback: Try direct insert/update
                        for record in dept_records:
                            try:
                                # Check if department already exists
                                existing = db.query(Department).filter(
                                    Department.dep_code == record['dep_code']
                                ).first()

                                if existing:
                                    print(f"Updating existing department: {record['dep_code']}")
                                    existing.name = record['name']
                                else:
                                    print(f"Creating new department: {record['dep_code']}")
                                    new_dept = Department(**record)
                                    db.add(new_dept)

                                db.commit()
                                print(f"Successfully processed department: {record['dep_code']}")

                            except SQLAlchemyError as e:
                                db.rollback()
                                print(f"Error processing department {record['dep_code']}: {str(e)}")
                                raise

                    finally:
                        db.close()

                    results["loaded_data"].append("departments")
                    print("Successfully loaded department data")

                except SQLAlchemyError as e:
                    print(f"Error during database load: {str(e)}")
                    raise ValueError(f"Failed to load department data into database:\
                                      {str(e)}") from e

            except pd.errors.EmptyDataError as exc:
                raise HTTPException(status_code=400,
                                    detail="The department CSV file is empty") from exc
            except pd.errors.ParserError as e:
                raise HTTPException(status_code=400,
                                    detail=f"Invalid CSV format: {str(e)}") from e
            except ValueError as e:
                print(f"Validation error: {str(e)}")
                raise HTTPException(status_code=400, detail=str(e)) from e
            except SQLAlchemyError as e:
                print(f"Error processing department CSV: {str(e)}")
                raise HTTPException(status_code=400,
                                    detail=f"Error processing department CSV: {str(e)}") from e
            except Exception as e:
                print(f"Unexpected error processing department CSV: {str(e)}")
                raise HTTPException(status_code=400,
                        detail=f"Unexpected error processing department CSV: {str(e)}") from e
        except Exception as e:
            print(f"Error processing department CSV: {str(e)}")
            raise HTTPException(status_code=400,
                                detail=f"Error processing department CSV: {str(e)}") from e
        finally:
            # Reset file pointer
            await file.seek(0)

            # Clean up temp file
            try:
                if os.path.exists(dept_csv_path):
                    os.remove(dept_csv_path)
                    print(f"Cleaned up temporary file: {dept_csv_path}")
            except OSError as e:
                print(f"Warning: Could not remove temporary file {dept_csv_path}: {str(e)}")

    # Handle Course Data
    if files_to_process["course_zips"]:
        logging.info("Processing course ZIP files...")
        course_dir = os.path.join(UPLOAD_DIR, "courses")
        os.makedirs(course_dir, exist_ok=True)
        for zip_file in files_to_process["course_zips"]:
            path = os.path.join(course_dir, zip_file.filename)
            logging.info("Saving course ZIP to: %s", path)
            with open(path, "wb") as f:
                shutil.copyfileobj(zip_file.file, f)
            logging.info("Successfully saved course ZIP: %s", zip_file.filename)

            # Validate ZIP content before processing
            if not validate_zip_content(path, "course"):
                raise HTTPException(
                    status_code=400,
                    detail=(f"Invalid course data in {zip_file.filename}. \
                            The file must contain course JSON files.")
                )

            unzip_and_flatten(path, course_dir)

            # Delete the ZIP file after processing
            try:
                os.remove(path)
                logging.info("Deleted course ZIP file: %s", path)
            except OSError as e:
                logging.error("Error deleting course ZIP file %s: %s", path, str(e))

        course_extractor = CourseDataExtractor(folder_path=course_dir, base_dir=UPLOAD_DIR)
        course_extractor.process_all_courses()
        load_data_from_dicts(course_extractor.get_results())
        results["loaded_data"].append("courses")

    # Handle Audit Data
    if files_to_process["audit_zips"]:
        logging.info("Processing audit ZIP files...")
        audit_root = os.path.join(UPLOAD_DIR, "audit")
        os.makedirs(audit_root, exist_ok=True)
        for zip_file in files_to_process["audit_zips"]:
            zip_path = os.path.join(audit_root, zip_file.filename)
            logging.info("Saving audit ZIP to: %s", zip_path)
            with open(zip_path, "wb") as f:
                shutil.copyfileobj(zip_file.file, f)
            logging.info("Successfully saved audit ZIP: %s", zip_file.filename)

            # Validate ZIP content before processing
            if not validate_zip_content(zip_path, "audit"):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid audit data in {zip_file.filename}. \
                         The file must contain audit JSON files."
                )

            unzip_and_flatten(zip_path, audit_root)

            # Delete the ZIP file after processing
            try:
                os.remove(zip_path)
                logging.info("Deleted audit ZIP file: %s", zip_path)
            except OSError as e:
                logging.error("Error deleting audit ZIP file %s: %s", zip_path, str(e))

        audit_extractor = AuditDataExtractor(
            audit_base_path=audit_root,
            course_base_path=os.path.join(UPLOAD_DIR, "courses"),
        )
        load_data_from_dicts(audit_extractor.get_results())
        results["loaded_data"].append("audits")

    # Handle Enrollment Data
    if files_to_process["enrollment_file"]:
        logging.info("Processing enrollment file...")
        # Check if course data is present
        if not files_to_process["course_zips"]:
            raise HTTPException(
                status_code=400,
                detail="Course data is required when uploading enrollment data. \
                    Please upload course ZIP files along with the enrollment file."
            )

        enrollment_path = os.path.join(UPLOAD_DIR, "enrollment.xlsx")
        logging.info("Saving enrollment file to: %s", enrollment_path)
        with open(enrollment_path, "wb") as f:
            shutil.copyfileobj(files_to_process["enrollment_file"].file, f)
        logging.info("Successfully saved enrollment file: %s",
                     files_to_process["enrollment_file"].filename)

        try:
            print("Creating enrollment extractor...")
            enrollment_extractor = EnrollmentDataExtractor()
            print("About to extract enrollment data...")
            enrollment_records = enrollment_extractor.extract_enrollment_data(enrollment_path)

            if not enrollment_records:
                raise ValueError("No valid enrollment records were extracted from the file")

            print(f"Extracted {len(enrollment_records)} enrollment records")
            print("First few records:", enrollment_records[:2])
            print("About to load enrollment records into database...")
            load_data_from_dicts({"enrollment": enrollment_records})
            results["loaded_data"].append("enrollment")
            print("Successfully loaded enrollment data")
        except ValueError as e:
            print(f"Value error processing enrollment: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e)) from e
        except Exception as e:
            print(f"Error processing enrollment: {str(e)}")
            raise HTTPException(status_code=400,
                                detail=f"Error processing enrollment file: {str(e)}"
                                ) from e

    # Update the success message to include all loaded data
    if results["loaded_data"]:
        results["message"] = f"Successfully loaded: {', '.join(results['loaded_data'])}"
        print(f"Final results: {results}")
    else:
        results["message"] = "No data was loaded"

    logging.info("=== Finished Database Initialization ===")
    return results
