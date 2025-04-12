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
    unzip_preserve_structure,
    validate_zip_content,
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

ALLOWED_AUDIT_MAJORS = {'ba', 'bio', 'cs', 'is'} # Define allowed majors

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
    course_zips: Optional[List[UploadFile]] = File(default=None, description="ZIP files containing course JSON data"),
    audit_zips: Optional[List[UploadFile]] = File(default=None, description="ZIP files containing audit JSON data"),
    enrollment_file: Optional[UploadFile] = File(default=None, description="Excel file containing enrollment data"),
    department_csv: Optional[UploadFile] = File(default=None, description="CSV file containing department data (columns: dep_code, name)")
):
    """Initialize or update the database with uploaded files."""
    logging.info("=== Starting Database Initialization Request ===")

    prepared_paths = {
        "dept_csv_path": None,
        "course_dir": None,
        "audit_root": None,
        "enrollment_excel_path": None
    }
    folders_to_clear = []
    upload_content = {"departments": False, "courses": False, "audits": False, "enrollment": False}

    # --- 1. Validate and Prepare File Paths ---
    try:
        # Department CSV
        if department_csv and department_csv.filename:
            await validate_upload_file(department_csv)
            dept_dir = os.path.join(UPLOAD_DIR, "departments")
            folders_to_clear.append("departments")
            prepared_paths["dept_csv_path"] = Path(dept_dir) / "departments.csv" # Use a consistent name
            upload_content["departments"] = True
        else: department_csv = None

        # Course ZIPs
        # Check if course_zips is None before iterating
        valid_course_zips = []
        if course_zips is not None:
            valid_course_zips = [await validate_upload_file(f) for f in course_zips if f and f.filename]

        if valid_course_zips:
            prepared_paths["course_dir"] = os.path.join(UPLOAD_DIR, "courses")
            folders_to_clear.append("courses")
            upload_content["courses"] = True
        # else: valid_course_zips is already []

        # Audit ZIPs
        # Check if audit_zips is None before iterating
        valid_audit_zips = []
        if audit_zips is not None:
            valid_audit_zips = [await validate_upload_file(f) for f in audit_zips if f and f.filename]

        if valid_audit_zips:
            prepared_paths["audit_root"] = os.path.join(UPLOAD_DIR, "audit")
            folders_to_clear.append("audit")
            upload_content["audits"] = True
        else: valid_audit_zips = []

        # Enrollment Excel
        if enrollment_file and enrollment_file.filename:
            await validate_upload_file(enrollment_file)
            enrollment_dir = os.path.join(UPLOAD_DIR, "enrollment")
            folders_to_clear.append("enrollment")
            # Use a consistent name, e.g., enrollment.xlsx
            prepared_paths["enrollment_excel_path"] = Path(enrollment_dir) / "enrollment.xlsx"
            upload_content["enrollment"] = True
        else: enrollment_file = None

        if not any(upload_content.values()):
            raise HTTPException(status_code=400, detail="No valid files provided.")

        # --- Dependencies Check ---
        if upload_content["audits"] and not upload_content["courses"]:
             raise HTTPException(status_code=400, detail="Audit data requires course data.")
        if upload_content["enrollment"] and not upload_content["courses"]:
            raise HTTPException(status_code=400, detail="Enrollment data requires course data.")

        # --- 2. Clear Directories and Save Files ---
        if folders_to_clear:
            clear_existing_data(folders_to_clear)

        # Save Department CSV
        if department_csv and prepared_paths["dept_csv_path"]:
             await save_upload_file(department_csv.file, department_csv.filename, prepared_paths["dept_csv_path"])

        # Save and Unzip Course ZIPs
        if valid_course_zips and prepared_paths["course_dir"]:
            course_dir = prepared_paths["course_dir"]
            for zip_file in valid_course_zips:
                 temp_zip_path = Path(course_dir) / zip_file.filename
                 await save_upload_file(zip_file.file, zip_file.filename, temp_zip_path)
                 if not validate_zip_content(str(temp_zip_path), "course"): raise HTTPException(status_code=400, detail=f"Invalid course ZIP: {zip_file.filename}")
                 unzip_and_flatten(str(temp_zip_path), course_dir)
                 temp_zip_path.unlink()
            if not find_json_files(course_dir): raise HTTPException(status_code=400, detail="No course JSONs extracted.")

        # Save and Unzip/Organize Audit ZIPs
        if valid_audit_zips and prepared_paths["audit_root"]:
            audit_final_dest = Path(prepared_paths["audit_root"])
            temp_extract_dir = Path(UPLOAD_DIR) / f"audit_temp_extract_{os.urandom(4).hex()}"
            os.makedirs(temp_extract_dir, exist_ok=True)
            logging.debug(f"Created temporary audit extraction dir: {temp_extract_dir}")
            extracted_correctly = False

            try:
                for zip_file in valid_audit_zips:
                    temp_zip_path = temp_extract_dir / zip_file.filename
                    await save_upload_file(zip_file.file, zip_file.filename, temp_zip_path)
                    if not validate_zip_content(str(temp_zip_path), "audit"): raise HTTPException(status_code=400, detail=f"Invalid audit ZIP: {zip_file.filename}")
                    # Extract preserving structure into the temp dir
                    unzip_preserve_structure(str(temp_zip_path), str(temp_extract_dir))
                    temp_zip_path.unlink() # Remove the temporary zip file

                # Find the directory containing major subfolders within the temp extraction dir
                source_audit_dir = None
                potential_dirs = [d for d in temp_extract_dir.iterdir() if d.is_dir()] # Look one level deep first
                if potential_dirs:
                    for potential_dir in potential_dirs:
                        subdirs = {sd.name for sd in potential_dir.iterdir() if sd.is_dir()}
                        if ALLOWED_AUDIT_MAJORS.issubset(subdirs) or any(m in subdirs for m in ALLOWED_AUDIT_MAJORS):
                             source_audit_dir = potential_dir
                             logging.info(f"Found major folders within subdirectory: {potential_dir.name}")
                             break
                # If not found one level deep, check the temp dir itself
                if not source_audit_dir:
                     root_subdirs = {sd.name for sd in temp_extract_dir.iterdir() if sd.is_dir()}
                     if ALLOWED_AUDIT_MAJORS.issubset(root_subdirs) or any(m in root_subdirs for m in ALLOWED_AUDIT_MAJORS):
                         source_audit_dir = temp_extract_dir
                         logging.info("Found major folders directly within temp extraction dir.")

                if not source_audit_dir:
                     raise HTTPException(status_code=400, detail="Could not find expected major subfolders (ba, bio, cs, is) within the extracted audit ZIP content.")

                # Move only the allowed major folders to the final destination
                for major_folder in source_audit_dir.iterdir():
                    if major_folder.is_dir() and major_folder.name in ALLOWED_AUDIT_MAJORS:
                        dest_path = audit_final_dest / major_folder.name
                        try:
                            # Ensure the destination doesn't exist from a previous run (covered by clear_existing_data)
                            # shutil.rmtree(dest_path, ignore_errors=True)
                            shutil.move(str(major_folder), str(dest_path))
                            logging.info(f"Moved audit major folder: {major_folder.name} to {dest_path}")
                        except Exception as move_error:
                            logging.error(f"Error moving audit major folder {major_folder.name}: {move_error}")
                            # Decide if this is fatal
                            raise HTTPException(status_code=500, detail=f"Failed to move processed audit folder {major_folder.name}")

                # Removed call to organize_audit_files
                # organize_audit_files(audit_root)
                if not find_json_files(str(audit_final_dest)):
                    # Check the final destination AFTER moving
                    raise HTTPException(status_code=400, detail="No audit JSONs found in final destination after processing.")
                extracted_correctly = True
            finally:
                # Clean up the temporary extraction directory
                if temp_extract_dir.exists():
                    shutil.rmtree(temp_extract_dir)
                    logging.debug(f"Cleaned up temporary audit extraction dir: {temp_extract_dir}")

            # Check if extraction was successful before proceeding
            if not extracted_correctly:
                 raise HTTPException(status_code=500, detail="Audit file extraction failed unexpectedly.")

        # Save Enrollment Excel
        if enrollment_file and prepared_paths["enrollment_excel_path"]:
             await save_upload_file(enrollment_file.file, enrollment_file.filename, prepared_paths["enrollment_excel_path"])

    except (HTTPException, ValueError, IOError) as e:
        logging.error("File preparation error: %s", e)
        raise e if isinstance(e, HTTPException) else HTTPException(status_code=400, detail=f"File handling error: {e}") from e
    except Exception as e:
        logging.exception("Unexpected error during file preparation: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error during file handling.")

    # --- 3. Data Extraction and Staged Loading ---
    loaded_types_display = []
    try:
        # Stage 1: Load Departments
        if upload_content["departments"] and prepared_paths["dept_csv_path"]:
            logging.info("Processing and loading department CSV...")
            try:
                dept_df = pd.read_csv(prepared_paths["dept_csv_path"])
                if 'dep_code' in dept_df.columns and 'name' in dept_df.columns:
                    dept_df = dept_df[['name', 'dep_code']].dropna(subset=['dep_code', 'name'])
                    dept_records = dept_df.to_dict(orient="records")
                    if dept_records:
                        load_data_from_dicts({"department": dept_records})
                        if "departments" not in loaded_types_display: loaded_types_display.append("departments")
                    else: logging.warning("No department records found in CSV.")
                else: raise ValueError("Department CSV missing required columns (dep_code, name)")
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error processing/loading department CSV: {e}")

        # Stage 2: Load Courses
        course_related_data = {}
        if upload_content["courses"] and prepared_paths["course_dir"]:
            logging.info("Processing and loading course data...")
            try:
                course_extractor = CourseDataExtractor(folder_path=prepared_paths["course_dir"], base_dir=UPLOAD_DIR)
                course_extractor.process_all_courses()
                course_results = course_extractor.get_results()
                # Extract only course-related tables for immediate loading
                course_keys = {"course", "instructor", "offering", "prereqs", "course_instructor"}
                course_related_data = {k: v for k, v in course_results.items() if k in course_keys and v}
                if course_related_data:
                    load_data_from_dicts(course_related_data)
                    if "courses" not in loaded_types_display: loaded_types_display.append("courses")
                else: logging.warning("Course extractor returned no data to load.")
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error processing/loading course data: {e}")

        # Stage 3: Fetch Course Codes (NOW courses are loaded)
        db_course_codes = set()
        if upload_content["audits"] and prepared_paths["audit_root"]:
            db = SessionLocal()
            try:
                logging.info("Fetching latest course codes for audit processing...")
                course_results = db.query(Course.course_code).all()
                db_course_codes = {c[0] for c in course_results}
                logging.info("Found %d course codes after course load.", len(db_course_codes))
            except Exception as e:
                logging.error("DB Error fetching course codes: %s", e)
                # Potentially raise or allow audit to proceed without codes? For now, let it proceed.
            finally:
                db.close()

        # Stage 4: Load Audits
        if upload_content["audits"] and prepared_paths["audit_root"]:
            logging.info("Processing and loading audit data...")
            if not db_course_codes:
                 logging.warning("Proceeding with audit processing, but no course codes were found in DB. 'countsfor' links may be incomplete.")
            try:
                audit_base_path = prepared_paths["audit_root"]
                logging.info(f"Calling AuditDataExtractor with base_path: {audit_base_path} and {len(db_course_codes)} course codes.") # Log input
                audit_extractor = AuditDataExtractor(audit_base_path=audit_base_path)
                audit_results = audit_extractor.get_results(db_course_codes=db_course_codes)

                # Log output of the extractor
                log_audit_counts = {k: len(v) for k, v in audit_results.items()} if audit_results else {}
                logging.info(f"AuditDataExtractor returned: {log_audit_counts}")

                # Extract only audit-related tables
                audit_keys = {"audit", "requirement", "countsfor"}
                audit_related_data = {k: v for k, v in audit_results.items() if k in audit_keys and v}

                # Log data being sent to load_data_from_dicts
                log_audit_load_counts = {k: len(v) for k, v in audit_related_data.items()} if audit_related_data else {}
                logging.info(f"Preparing to load audit data: {log_audit_load_counts}")

                if audit_related_data:
                    load_data_from_dicts(audit_related_data)
                    if "audits" not in loaded_types_display: loaded_types_display.append("audits")
                else: logging.warning("Audit extractor returned no data to load.")
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error processing/loading audit data: {e}")

        # Stage 5: Load Enrollment
        if upload_content["enrollment"] and prepared_paths["enrollment_excel_path"]:
            logging.info("Processing and loading enrollment file...")
            try:
                enrollment_df = pd.read_excel(prepared_paths["enrollment_excel_path"])
                enrollment_extractor = EnrollmentDataExtractor()
                enrollment_records = enrollment_extractor.process_enrollment_dataframe(enrollment_df)
                if enrollment_records:
                    # _ensure_offerings_exist is called within load_data_from_dicts now
                    load_data_from_dicts({"enrollment": enrollment_records})
                    if "enrollment" not in loaded_types_display: loaded_types_display.append("enrollment")
                else:
                    logging.warning("No valid enrollment records extracted from Excel.")
            except Exception as e:
                # ... (error handling as before) ...
                raise HTTPException(status_code=400, detail=f"Error processing/loading enrollment file: {e}")


    except HTTPException as e:
         logging.error("Data processing/loading error: %s (Detail: %s)", e.status_code, e.detail)
         raise e
    except Exception as e:
        logging.exception("Unexpected error during staged data loading: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error during data loading.")

    final_message = f"Successfully loaded: {', '.join(loaded_types_display)}" if loaded_types_display else "No data was processed or loaded."
    logging.info("=== Finished Database Initialization Request: %s ===", final_message)
    return {"message": final_message, "loaded_data": loaded_types_display}

# Removed clear_existing_department_data, clear_existing_course_data, clear_existing_audit_data
# Use clear_existing_data(folders) instead

# Removed organize_audit_files (moved to file_handler.py)
