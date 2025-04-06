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
from fastapi import APIRouter, UploadFile, File, HTTPException
import pandas as pd
from backend.scripts.course_extractor import CourseDataExtractor
from backend.scripts.audit_extractor import AuditDataExtractor
from backend.scripts.enrollment_extractor import EnrollmentDataExtractor
from backend.database.load_data import load_data_from_dicts


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

def standardize_folder_name(folder_name: str) -> str:
    """Standardize folder names for data uploads."""
    folder_mapping = {
        "course-details": "courses",
        "audit-files": "audit",
        "enrollment-data": "enrollment",
        "department-data": "departments",  # New mapping for department data
        # Add more mappings as needed
    }
    return folder_mapping.get(folder_name, folder_name)  # Default to the original name if not found

def clear_existing_data():
    """Clear existing data in the data directory."""
    for folder in ["departments", "courses", "audit", "enrollment"]:
        folder_path = os.path.join(UPLOAD_DIR, folder)
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
        os.makedirs(folder_path)  # Recreate the folder after clearing

@router.post(
    "/upload/init-db/",
    summary="Upload and Initialize Database",
    description="""
    Upload files to initialize or update the database. Accepts:
    - Department CSV file (columns: dep_code, name)
    - Course ZIP files (containing JSON course data)
    - Audit ZIP files (containing JSON audit data)
    - Enrollment Excel file
    """,
    response_description="Returns a list of successfully loaded data types"
)
async def initialize_database(
    course_zips: Optional[List[UploadFile]] = File(None,
                description="ZIP files containing course JSON data"),
    audit_zips: Optional[List[UploadFile]] = File(None,
                description="ZIP files containing audit JSON data"),
    enrollment_file: Optional[UploadFile] = File(None,
                description="Excel file containing enrollment data"),
    department_csv: Optional[UploadFile] = File(None,
                description="CSV file containing department data (columns: dep_code, name)")
):
    """Initialize or update the database with uploaded files."""
    logging.info("=== Starting Database Initialization ===")

    # Validate and standardize uploads
    files_to_process = {
        "course_zips": [f for f in course_zips if f and f.filename] if course_zips else [],
        "audit_zips": [f for f in audit_zips if f and f.filename] if audit_zips else [],
        "enrollment_file": enrollment_file,
        "department_csv": department_csv
    }

    if not any(files_to_process.values()):
        logging.warning("No valid files found in the request")
        raise HTTPException(status_code=400,
        detail="No valid files provided for upload.\
              Please ensure at least one file is selected")

    results = {"message": "Data loaded successfully", "loaded_data": []}

    # Handle Department CSV
    if files_to_process["department_csv"]:
        logging.info("Processing department CSV...")
        clear_existing_department_data()

        dept_dir = os.path.join(UPLOAD_DIR, "departments")
        os.makedirs(dept_dir, exist_ok=True)

        dept_csv_path = os.path.join(dept_dir, "departments.csv")

        try:
            file = files_to_process["department_csv"]
            contents = await file.read()

            if len(contents) == 0:
                raise ValueError("Department CSV file is empty")

            with open(dept_csv_path, "wb") as f:
                f.write(contents)

            dept_df = pd.read_csv(dept_csv_path)
            if 'dep_code' not in dept_df.columns or 'name' not in dept_df.columns:
                raise ValueError("Missing required columns in department CSV")

            dept_df = dept_df[['name', 'dep_code']].dropna(subset=['dep_code', 'name'])
            dept_records = dept_df.to_dict(orient="records")

            load_data_from_dicts({"department": dept_records})
            results["loaded_data"].append("departments")

        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

    # Handle Course Data
    if files_to_process["course_zips"]:
        logging.info("Processing course ZIP files...")
        clear_existing_course_data()  # Clear existing course data if needed
        course_dir = os.path.join(UPLOAD_DIR, "courses")
        os.makedirs(course_dir, exist_ok=True)

        for zip_file in files_to_process["course_zips"]:
            standardized_name = standardize_folder_name(zip_file.filename)
            path = os.path.join(course_dir, standardized_name)
            with open(path, "wb") as f:
                shutil.copyfileobj(zip_file.file, f)

            # Validate the ZIP content
            if not validate_zip_content(path, "course"):
                raise HTTPException(status_code=400,
                                    detail=f"Invalid course data in {zip_file.filename}.")

            # Unzip and validate course structure
            unzip_and_flatten(path, course_dir)
            os.remove(path)

            # Check for JSON files in the course directory and its subdirectories
            json_files = find_json_files(course_dir)
            logging.info("Found %d course JSON files", len(json_files))
            if len(json_files) == 0:
                raise HTTPException(status_code=400,
                                   detail=f"No course JSON files found in {zip_file.filename}.")

        # Use the main course directory instead of looking for a specific subfolder
        course_extractor = CourseDataExtractor(folder_path=course_dir, base_dir=UPLOAD_DIR)
        course_extractor.process_all_courses()
        load_data_from_dicts(course_extractor.get_results())
        results["loaded_data"].append("courses")

    # Handle Audit Data
    if files_to_process["audit_zips"]:
        logging.info("Processing audit ZIP files...")
        clear_existing_audit_data()  # Clear existing audit data if needed
        audit_root = os.path.join(UPLOAD_DIR, "audit")
        os.makedirs(audit_root, exist_ok=True)

        for zip_file in files_to_process["audit_zips"]:
            standardized_name = standardize_folder_name(zip_file.filename)
            zip_path = os.path.join(audit_root, standardized_name)
            try:
                with open(zip_path, "wb") as f:
                    shutil.copyfileobj(zip_file.file, f)

                if not validate_zip_content(zip_path, "audit"):
                    raise HTTPException(status_code=400, detail=f"Invalid audit \
                                        data in {zip_file.filename}.")

                # Unzip and validate audit structure
                unzip_and_flatten(zip_path, audit_root)
                os.remove(zip_path)

                # Check for JSON files in the audit directory and its subdirectories
                json_files = find_json_files(audit_root)
                logging.info("Found %d audit JSON files", len(json_files))
                if len(json_files) == 0:
                    raise HTTPException(status_code=400,
                                      detail=f"No audit JSON files found in {zip_file.filename}.")

                # Ensure only allowed major folders exist
                ALLOWED_MAJORS = {'ba', 'cs', 'is', 'bio'}
                found_dirs = set()

                for root, dirs, _ in os.walk(audit_root):
                    for dir_name in dirs:
                        dir_lower = dir_name.lower()
                        found_dirs.add(dir_lower)

                non_main_majors = found_dirs - ALLOWED_MAJORS
                if non_main_majors:
                    logging.warning("Found non-main major directories: %s. These will be ignored.",
                                   ", ".join(non_main_majors))
                    results["message"] = f"Note: Found directories for non-main majors ({', '.join(non_main_majors)}). " \
                                        f"Only BA, CS, IS, and BIO majors will be processed."

                main_majors = found_dirs & ALLOWED_MAJORS
                if not main_majors:
                    raise HTTPException(status_code=400,
                                       detail=f"Audit ZIP must contain at least one of the required major folders: BA, CS, IS, or BIO.")


            except Exception as e:
                logging.error("Error processing audit ZIP file %s: %s", zip_file.filename, str(e))
                raise HTTPException(status_code=400, detail=str(e)) from e

        audit_extractor = AuditDataExtractor(audit_base_path=audit_root,
                                             course_base_path=os.path.join(UPLOAD_DIR, "courses"))
        load_data_from_dicts(audit_extractor.get_results())
        results["loaded_data"].append("audits")

    # Handle Enrollment Data
    if files_to_process["enrollment_file"]:
        logging.info("Processing enrollment file...")
        clear_existing_enrollment_data()  # Clear existing enrollment data if needed
        enrollment_path = os.path.join(UPLOAD_DIR, "enrollment", "enrollment.xlsx")
        os.makedirs(os.path.dirname(enrollment_path), exist_ok=True)
        try:
            with open(enrollment_path, "wb") as f:
                shutil.copyfileobj(files_to_process["enrollment_file"].file, f)

            enrollment_extractor = EnrollmentDataExtractor()
            enrollment_records = enrollment_extractor.extract_enrollment_data(enrollment_path)

            if not enrollment_records:
                raise ValueError("No valid enrollment records were extracted from the file")

            load_data_from_dicts({"enrollment": enrollment_records})
            results["loaded_data"].append("enrollment")

        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

    if results["loaded_data"]:
        results["message"] = f"Successfully loaded: {', '.join(results['loaded_data'])}"
    else:
        results["message"] = "No data was loaded"

    logging.info("=== Finished Database Initialization ===")
    return results

def clear_existing_department_data():
    """Clear existing department data."""
    dept_dir = os.path.join(UPLOAD_DIR, "departments")
    if os.path.exists(dept_dir):
        shutil.rmtree(dept_dir)
    os.makedirs(dept_dir)  # Recreate the folder after clearing

def clear_existing_course_data():
    """Clear existing course data."""
    course_dir = os.path.join(UPLOAD_DIR, "courses")
    if os.path.exists(course_dir):
        shutil.rmtree(course_dir)
    os.makedirs(course_dir)  # Recreate the folder after clearing

def clear_existing_audit_data():
    """Clear existing audit data."""
    audit_dir = os.path.join(UPLOAD_DIR, "audit")
    if os.path.exists(audit_dir):
        shutil.rmtree(audit_dir)
    os.makedirs(audit_dir)  # Recreate the folder after clearing

def clear_existing_enrollment_data():
    """Clear existing enrollment data."""
    enrollment_dir = os.path.join(UPLOAD_DIR, "enrollment")
    if os.path.exists(enrollment_dir):
        shutil.rmtree(enrollment_dir)
    os.makedirs(enrollment_dir)  # Recreate the folder after clearing

def find_json_files(directory):
    """Find all JSON files in the given directory and its subdirectories."""
    json_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.json') and not file.startswith('__MACOSX'):
                json_files.append(os.path.join(root, file))
    return json_files
