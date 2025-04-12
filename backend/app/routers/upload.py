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
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
import pandas as pd
from backend.scripts.course_extractor import CourseDataExtractor
from backend.scripts.audit_extractor import AuditDataExtractor
from backend.scripts.enrollment_extractor import EnrollmentDataExtractor
from backend.database.load_data import load_data_from_dicts
from backend.database.models import Course
from backend.database.db import SessionLocal
# Import the new file handler utils
from backend.app.utils.file_handler import (
    save_upload_file,
    unzip_and_flatten,
    validate_zip_content,
    organize_audit_files,
    find_json_files,
    UPLOAD_DIR # Import the constant if needed here
)


router = APIRouter()

# Set up logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# UPLOAD_DIR is now defined in file_handler.py
# print(f"Using data directory: {UPLOAD_DIR}")
# os.makedirs(UPLOAD_DIR, exist_ok=True)

# Removed functions moved to file_handler.py:
# - unzip_and_flatten
# - validate_zip_content
# - organize_audit_files
# - find_json_files

async def validate_upload_file(file: Optional[UploadFile] = File(None)) -> Optional[UploadFile]:
    """Validate that the uploaded file is not empty and has a filename."""
    print(f"\nValidating file: {file.filename if file else None}")  # Debug log
    if not file:
        print("No file provided")
        return None

    print(f"File content type: {file.content_type}")
    # Use file.size directly if available
    print(f"File size: {file.size if hasattr(file, 'size') else 'unknown'}")

    if not file.filename:
        print("Error: File has no filename")
        raise HTTPException(status_code=400, detail="File has no filename")

    # Simple check based on filename extension
    if file.filename.endswith('.csv') and not file.content_type in ['text/csv',
                                                                    'application/vnd.ms-excel', 'application/octet-stream']:
        logging.warning(f"CSV file '{file.filename}' has potentially unexpected content type: {file.content_type}")
    elif file.filename.endswith('.zip') and 'zip' not in file.content_type:
        logging.warning(f"ZIP file '{file.filename}' has potentially unexpected content type: {file.content_type}")
    elif (file.filename.endswith('.xlsx') or file.filename.endswith('.xls')) and \
         not ('spreadsheet' in file.content_type or 'excel' in file.content_type or 'octet-stream' in file.content_type):
         logging.warning(f"Excel file '{file.filename}' has potentially unexpected content type: {file.content_type}")

    # You might want to add a check for file size here if needed
    # Example: if file.size > MAX_FILE_SIZE:
    #    raise HTTPException(status_code=413, detail="File too large")

    return file  # Return the file object

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

def clear_existing_data(folders_to_clear: List[str]):
    """Clear existing data in specified subdirectories of UPLOAD_DIR."""
    logging.info("Clearing existing data for folders: %s", folders_to_clear)
    for folder in folders_to_clear:
        folder_path = os.path.join(UPLOAD_DIR, folder)
        if os.path.exists(folder_path):
            try:
                shutil.rmtree(folder_path)
                logging.debug("Removed existing directory: %s", folder_path)
            except OSError as e:
                logging.error("Error removing directory %s: %s", folder_path, e)
                # Decide if this should be a fatal error
                raise HTTPException(status_code=500, detail=f"Could not clear old data in {folder}")
        try:
            os.makedirs(folder_path)
            logging.debug("Recreated directory: %s", folder_path)
        except OSError as e:
             logging.error("Error creating directory %s: %s", folder_path, e)
             raise HTTPException(status_code=500, detail=f"Could not create data directory for {folder}")

@router.post(
    "/upload/init-db/",
    summary="Upload and Initialize Database",
    description=(
        """Upload files to initialize or update the database. Accepts:\n"
        "- Department CSV file (columns: dep_code, name)\n"
        "- Course ZIP files (containing JSON course data)\n"
        "- Audit ZIP files (containing JSON audit data)\n"
        "- Enrollment Excel file"""
    ),
    response_description="Returns a list of successfully loaded data types"
)
async def initialize_database(
    # Use Depends for validation?
    course_zips: Optional[List[UploadFile]] = File(default=None,
                                                description="ZIP files containing course JSON data"),
    audit_zips: Optional[List[UploadFile]] = File(default=None,
                                              description="ZIP files containing audit JSON data"),
    enrollment_file: Optional[UploadFile] = File(default=None,
                                               description="Excel file containing enrollment data"),
    department_csv: Optional[UploadFile] = File(default=None,
                                              description="CSV file containing department data (columns: dep_code, name)")
):
    """Initialize or update the database with uploaded files."""
    logging.info("=== Starting Database Initialization Request ===")

    # --- File Validation and Preparation --- (Moved to separate section)
    # Create dictionaries to store paths of prepared data
    prepared_paths = {
        "dept_csv": None,
        "course_dir": None,
        "audit_root": None,
        "enrollment_excel": None
    }
    folders_to_clear = []

    try:
        # 1. Department CSV
        if department_csv and department_csv.filename:
            await validate_upload_file(department_csv) # Basic validation
            dept_dir = os.path.join(UPLOAD_DIR, "departments")
            folders_to_clear.append("departments")
            prepared_paths["dept_csv"] = Path(dept_dir) / "departments.csv"
            # Save handled later after clearing dirs
        else:
            department_csv = None # Ensure it's None if no valid file

        # 2. Course ZIPs
        valid_course_zips = [await validate_upload_file(f) for f in course_zips if f and f.filename]
        if valid_course_zips:
            prepared_paths["course_dir"] = os.path.join(UPLOAD_DIR, "courses")
            folders_to_clear.append("courses")
            # Save/unzip handled later
        else:
             valid_course_zips = [] # Ensure it's an empty list

        # 3. Audit ZIPs
        valid_audit_zips = [await validate_upload_file(f) for f in audit_zips if f and f.filename]
        if valid_audit_zips:
            prepared_paths["audit_root"] = os.path.join(UPLOAD_DIR, "audit")
            folders_to_clear.append("audit")
            # Save/unzip/organize handled later
        else:
            valid_audit_zips = [] # Ensure it's an empty list

        # 4. Enrollment Excel
        if enrollment_file and enrollment_file.filename:
            await validate_upload_file(enrollment_file)
            enrollment_dir = os.path.join(UPLOAD_DIR, "enrollment")
            folders_to_clear.append("enrollment")
            prepared_paths["enrollment_excel"] = Path(enrollment_dir) / enrollment_file.filename
            # Save handled later
        else:
             enrollment_file = None # Ensure it's None if no valid file

        # Check if any files were actually provided
        if not any([department_csv, valid_course_zips, valid_audit_zips, enrollment_file]):
            logging.warning("No valid files found in the request")
            raise HTTPException(status_code=400,
                                detail="No valid files provided for upload. Please select at least one file.")

        # Clear relevant directories *before* saving new files
        if folders_to_clear:
            clear_existing_data(folders_to_clear)

        # Save and process uploaded files
        if department_csv:
             await save_upload_file(department_csv.file, department_csv.filename, prepared_paths["dept_csv"])

        if valid_course_zips:
            course_dir = prepared_paths["course_dir"]
            for zip_file in valid_course_zips:
                 # Save temporarily for validation/unzipping
                 temp_zip_path = Path(course_dir) / zip_file.filename
                 await save_upload_file(zip_file.file, zip_file.filename, temp_zip_path)
                 if not validate_zip_content(str(temp_zip_path), "course"):
                     temp_zip_path.unlink(missing_ok=True) # Clean up invalid zip
                     raise HTTPException(status_code=400, detail=f"Invalid course data content in {zip_file.filename}.")
                 unzip_and_flatten(str(temp_zip_path), course_dir)
                 temp_zip_path.unlink() # Clean up temporary zip
            # Post-validation: check if JSON files actually exist after unzipping
            if not find_json_files(course_dir):
                 raise HTTPException(status_code=400, detail="No course JSON files found after extracting ZIP(s).")

        if valid_audit_zips:
            audit_root = prepared_paths["audit_root"]
            for zip_file in valid_audit_zips:
                temp_zip_path = Path(audit_root) / zip_file.filename
                await save_upload_file(zip_file.file, zip_file.filename, temp_zip_path)
                if not validate_zip_content(str(temp_zip_path), "audit"):
                    temp_zip_path.unlink(missing_ok=True)
                    raise HTTPException(status_code=400, detail=f"Invalid audit data content in {zip_file.filename}.")
                unzip_and_flatten(str(temp_zip_path), audit_root)
                temp_zip_path.unlink()
            organize_audit_files(audit_root)
            # Post-validation
            if not find_json_files(audit_root):
                 raise HTTPException(status_code=400, detail="No audit JSON files found after extracting/organizing ZIP(s).")

        if enrollment_file:
             await save_upload_file(enrollment_file.file, enrollment_file.filename, prepared_paths["enrollment_excel"])

    except (HTTPException, ValueError, IOError) as e: # Catch specific errors from validation/saving
        logging.error("File preparation error: %s", e)
        # If it's already HTTPException, re-raise, otherwise wrap
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=400, detail=f"File handling error: {e}") from e
    except Exception as e:
        logging.exception("Unexpected error during file preparation: %s", e)
        raise HTTPException(status_code=500, detail=f"Internal server error during file handling.")

    # --- Data Extraction and Loading --- (Now uses prepared paths)
    results = {"message": "Data loading initiated", "loaded_data": []}
    all_data_to_load = {}

    try:
        # Fetch course codes ONCE if needed for audit
        db_course_codes = None
        if prepared_paths["audit_root"]:
            db = SessionLocal()
            try:
                logging.info("Fetching course codes for audit processing...")
                course_results = db.query(Course.course_code).all()
                db_course_codes = {c[0] for c in course_results}
                logging.info("Found %d existing course codes.", len(db_course_codes))
                if not db_course_codes: logging.warning("No courses found in DB!")
            except Exception as e:
                logging.error("DB Error fetching course codes for audit: %s", e)
                # Decide if fatal - maybe allow audit processing without codes?
            finally:
                db.close()

        # Department Data
        if prepared_paths["dept_csv"]:
            logging.info("Processing department CSV...")
            try:
                dept_df = pd.read_csv(prepared_paths["dept_csv"])
                if 'dep_code' in dept_df.columns and 'name' in dept_df.columns:
                    dept_df = dept_df[['name', 'dep_code']].dropna(subset=['dep_code', 'name'])
                    all_data_to_load["department"] = dept_df.to_dict(orient="records")
                    # results["loaded_data"].append("departments") # Add only after successful DB load
                else:
                    raise ValueError("Department CSV missing required columns (dep_code, name)")
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error processing department CSV: {e}")

        # Course Data
        if prepared_paths["course_dir"]:
            logging.info("Processing course data...")
            try:
                course_extractor = CourseDataExtractor(folder_path=prepared_paths["course_dir"], base_dir=UPLOAD_DIR)
                course_extractor.process_all_courses()
                all_data_to_load.update(course_extractor.get_results())
                # results["loaded_data"].append("courses")
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error processing course data: {e}")

        # Audit Data
        if prepared_paths["audit_root"]:
            logging.info("Processing audit data...")
            if db_course_codes is None: # Check if fetching failed earlier
                 logging.warning("Cannot process audit data because course codes could not be fetched.")
                 # Optionally raise HTTPException here?
            else:
                try:
                    audit_extractor = AuditDataExtractor(audit_base_path=prepared_paths["audit_root"])
                    audit_results = audit_extractor.get_results(db_course_codes=db_course_codes or set())
                    all_data_to_load.update(audit_results)
                    # results["loaded_data"].append("audits")
                except Exception as e:
                    raise HTTPException(status_code=400, detail=f"Error processing audit data: {e}")

        # Enrollment Data
        if prepared_paths["enrollment_excel"]:
            logging.info("Processing enrollment file...")
            try:
                enrollment_df = pd.read_excel(prepared_paths["enrollment_excel"])
                enrollment_extractor = EnrollmentDataExtractor()
                enrollment_records = enrollment_extractor.process_enrollment_dataframe(enrollment_df)
                if enrollment_records:
                    all_data_to_load["enrollment"] = enrollment_records
                    # results["loaded_data"].append("enrollment")
                else:
                    logging.warning("No valid enrollment records extracted from %s", enrollment_file.filename)
            except Exception as e:
                detail = f"Error processing enrollment file: {e}"
                if isinstance(e, ValueError):
                    detail = f"Invalid data in enrollment file: {e}"
                elif 'Excel file format cannot be determined' in str(e):
                    detail = "Invalid file format. Please upload Excel (.xlsx/.xls)."
                raise HTTPException(status_code=400, detail=detail)

        # Load all collected data into the database
        if all_data_to_load:
            logging.info("Loading processed data into the database... Tables: %s", list(all_data_to_load.keys()))
            try:
                # Pass the relevant subset of loaded data types to the message
                loaded_keys = list(all_data_to_load.keys())
                # Map internal keys to user-friendly names if desired
                type_map = {
                    "department": "departments",
                    "course": "courses", "prereqs": "courses", "offering": "courses",
                    "instructor": "courses", "course_instructor": "courses",
                    "audit": "audits", "requirement": "audits", "countsfor": "audits",
                    "enrollment": "enrollment"
                }
                loaded_types_display = sorted(list(set(type_map[k] for k in loaded_keys if k in type_map)))

                load_data_from_dicts(all_data_to_load)
                results["loaded_data"] = loaded_types_display
                results["message"] = f"Successfully loaded: {', '.join(loaded_types_display)}"
                logging.info("Database load successful for: %s", loaded_types_display)
            except Exception as e:
                logging.exception("Database loading failed: %s", e)
                raise HTTPException(status_code=500, detail=f"Database loading failed: {e}")
        else:
            results["message"] = "No data was processed to load."
            # Raise error if files were uploaded but nothing was processed
            if any([department_csv, valid_course_zips, valid_audit_zips, enrollment_file]):
                raise HTTPException(status_code=400,
                                    detail="Provided files could not be processed or contained no data.")

    except HTTPException as e:
         # Log and re-raise HTTP exceptions from processing steps
         logging.error("Data processing/loading error: %s (Detail: %s)", e.status_code, e.detail)
         raise e
    except Exception as e:
        logging.exception("Unexpected error during data processing/loading: %s", e)
        raise HTTPException(status_code=500, detail=f"Internal server error during data processing.")

    logging.info("=== Finished Database Initialization Request ===")
    return results

# Removed clear_existing_department_data, clear_existing_course_data, clear_existing_audit_data
# Use clear_existing_data(folders) instead

# Removed organize_audit_files (moved to file_handler.py)
