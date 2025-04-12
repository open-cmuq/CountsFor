"""
Extracts and processes enrollment data from Excel files.
"""

import logging
import pandas as pd
from backend.scripts.data_extractor import DataExtractor

class EnrollmentDataExtractor(DataExtractor):
    """
    Extracts and processes enrollment data from Excel files.
    """
    @staticmethod
    def format_course_code(code: any) -> str:
        """
        Formats the course code to a standardized format.
        """
        try:
            code_str = str(code).strip()
            if code_str.isdigit():
                code_str = code_str.zfill(5)
                return f"{code_str[:2]}-{code_str[2:]}"
            return code_str
        except (ValueError, TypeError) as error:
            logging.warning("Failed to format course code: %s, error: %s", code, error)
            return str(code)

    def process_enrollment_dataframe(self, df: pd.DataFrame) -> list[dict]:
        """
        Processes enrollment data from the given DataFrame.
        Returns a list of enrollment dictionaries for load_data.py.
        """
        if df.empty:
            logging.warning("Received empty DataFrame for enrollment processing.")
            return []

        try:
            df = df.copy()

            # Forward fill specific columns
            forward_fill_cols = ["Semester Id (Schedule)", "Course Id", "Section Id",
                                 "Department Id", "Class Id"]
            for col in forward_fill_cols:
                if col in df.columns:
                    df[col] = df[col].ffill()
                else:
                     logging.warning("Expected forward-fill column '%s' not found in enrollment DataFrame.", col)

            # Rename columns
            rename_dict = {
                "Semester Id (Schedule)": "semester",
                "Course Id": "course_code",
                "Section Id": "section",
                "Department Id": "department",
                "Class Id": "class_",
                "Count of Class Id": "enrollment_count"
            }
            df.rename(columns=rename_dict, inplace=True)

            # Ensure required columns exist
            required_columns = ["semester", "course_code", "class_", "enrollment_count",
                                "department", "section"]
            for col in required_columns:
                if col not in df.columns:
                    logging.warning("Required column '%s' is missing from enrollment DataFrame, adding default.", col)
                    df[col] = 0 if col in ["enrollment_count", "class_"] else ""

            # Format course codes
            if "course_code" in df.columns:
                df["course_code"] = df["course_code"].apply(self.format_course_code).astype(str)
                valid_codes = df["course_code"].notna() & ~df["course_code"].str.match(r'^[A-Za-z]{2}')
                df = df[valid_codes]

            # Ensure numeric types
            df["class_"] = pd.to_numeric(df["class_"], errors='coerce').fillna(0).astype(int)
            df["enrollment_count"] = pd.to_numeric(df["enrollment_count"], errors='coerce').fillna(0).astype(int)

            # Fill missing semesters
            missing_semester = df["semester"].isna()
            if missing_semester.any():
                 logging.warning("Found %d rows with missing semester. Attempting to fill...", missing_semester.sum())
                 semester_map = df.dropna(subset=["semester"]).groupby("course_code")["semester"].first()
                 df["semester"] = df["semester"].fillna(df["course_code"].map(semester_map))
                 still_missing = df["semester"].isna().sum()
                 if still_missing > 0:
                     logging.warning("Could not determine semester for %d records.", still_missing)

            # Filter rows with essential missing data
            df = df.dropna(subset=["course_code", "semester"])

            records = df.to_dict(orient="records")
            logging.info("Processed %d valid enrollment records from DataFrame.", len(records))
            return records

        except Exception as e:
            logging.exception("Error processing enrollment DataFrame: %s", e)
            return []

    # Deprecated - Reads file first, then calls new method
    def extract_enrollment_data(self, file_path: str) -> list[dict]:
        logging.warning("Using deprecated extract_enrollment_data(file_path). Prefer process_enrollment_dataframe(df).")
        try:
            df = pd.read_excel(file_path)
            return self.process_enrollment_dataframe(df)
        except Exception as e:
            logging.error("Failed to read/process Excel file %s: %s", file_path, e)
            return []
