import pandas as pd
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import *  # Import all models

# Define the mapping of table names to corresponding SQLAlchemy models
TABLES = {  
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

def load_excel_data(file_paths):
    """Loads data from multiple Excel files and inserts them into the database in a controlled order."""
    db: Session = SessionLocal()

    try:
        for table_name, file_path in file_paths:
            model = TABLES[table_name]
            df = pd.read_excel(file_path)
            records = df.to_dict(orient='records')

            if records:
                db.bulk_insert_mappings(model, records)
                db.commit()  # ✅ Ensure commit before the next table

            print(f"✅ Successfully inserted data into {table_name} table.")

    except Exception as e:
        db.rollback()
        print(f"❌ Error inserting data into {table_name}: {e}")

    finally:
        db.close()


if __name__ == "__main__":
    file_paths = [
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

    load_excel_data(file_paths)
