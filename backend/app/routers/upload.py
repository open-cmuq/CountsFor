from fastapi import APIRouter, UploadFile, File
import shutil, os, zipfile, json
import pandas as pd
from backend.scripts.course_extractor import CourseDataExtractor
from backend.scripts.audit_extractor import AuditDataExtractor
from backend.scripts.enrollment_extractor import EnrollmentDataExtractor
from backend.database.load_data import load_data_from_dicts
from backend.database.db import reset_db  # optional reset before init

router = APIRouter()
UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def unzip_and_flatten(zip_path: str, extract_to: str):
    base_name = os.path.splitext(os.path.basename(zip_path))[0]
    temp_extract_path = os.path.join(UPLOAD_DIR, f"{base_name}_temp_extract")
    os.makedirs(temp_extract_path, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(temp_extract_path)

    # Optionally log extracted files:
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

@router.post("/upload/init-db/")
async def initialize_database(
    course_zips: list[UploadFile] = File(...),
    audit_zips: list[UploadFile] = File(...),
    enrollment_file: UploadFile = File(...),
    department_csv: UploadFile = File(...)
):
    reset_db()

    # ✅ Step 1: Unzip and flatten course JSONs
    course_dir = os.path.join(UPLOAD_DIR, "courses")
    os.makedirs(course_dir, exist_ok=True)
    for zip_file in course_zips:
        path = os.path.join(course_dir, zip_file.filename)
        with open(path, "wb") as f:
            shutil.copyfileobj(zip_file.file, f)
        unzip_and_flatten(path, course_dir)

    course_extractor = CourseDataExtractor(folder_path=course_dir, base_dir=UPLOAD_DIR)
    course_extractor.process_all_courses()
    load_data_from_dicts(course_extractor.get_results())

    # ✅ Step 2: Unzip and flatten audits
    audit_root = os.path.join(UPLOAD_DIR, "audit")
    os.makedirs(audit_root, exist_ok=True)
    for zip_file in audit_zips:
        zip_path = os.path.join(audit_root, zip_file.filename)
        with open(zip_path, "wb") as f:
            shutil.copyfileobj(zip_file.file, f)
        unzip_and_flatten(zip_path, audit_root)

    audit_extractor = AuditDataExtractor(
        audit_base_path=audit_root,
        course_base_path=course_dir,
    )
    load_data_from_dicts(audit_extractor.get_results())

    # ✅ Step 3: Enrollment
    enrollment_path = os.path.join(UPLOAD_DIR, "enrollment.xlsx")
    with open(enrollment_path, "wb") as f:
        shutil.copyfileobj(enrollment_file.file, f)

    enrollment_extractor = EnrollmentDataExtractor()
    enrollment_records = enrollment_extractor.extract_enrollment_data(enrollment_path)
    load_data_from_dicts({"enrollment": enrollment_records})

    # ✅ Step 4: Department CSV (direct upload, no zip)
    dept_csv_path = os.path.join(UPLOAD_DIR, "departments.csv")
    with open(dept_csv_path, "wb") as f:
        shutil.copyfileobj(department_csv.file, f)
    try:
        dept_df = pd.read_csv(dept_csv_path)
    except Exception as e:
        print(f"Error reading department CSV: {e}")
        dept_df = pd.DataFrame()
    load_data_from_dicts({"department": dept_df.to_dict(orient="records")})

    return {"message": "✅ Database initialized successfully"}
