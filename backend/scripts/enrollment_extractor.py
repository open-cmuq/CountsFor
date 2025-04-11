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

    def extract_enrollment_data(self, file_path: str) -> list[dict]:
        """
        Reads and processes enrollment data from the given Excel file.
        Returns a list of enrollment dictionaries for load_data.py.
        """
        try:
            df = pd.read_excel(file_path)
        except (OSError, ValueError) as error:
            logging.error("Failed to read file %s: %s", file_path, error)
            return []

        # Forward fill specific columns
        forward_fill_cols = ["Semester Id (Schedule)", "Course Id", "Section Id",
                             "Department Id", "Class Id"]
        for col in forward_fill_cols:
            if col in df.columns:
                df[col] = df[col].ffill()

        # Rename columns for consistency
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
                logging.warning("Required column '%s' is missing from enrollment data", col)
                df[col] = "" if col != "enrollment_count" and col != "class_" else 0

        # Format course codes and filter invalid codes
        if "course_code" in df.columns:
            df["course_code"] = df["course_code"].apply(self.format_course_code).astype(str)
            # Filter out invalid course codes (those starting with letters)
            df = df[~df["course_code"].str.match(r'^[A-Za-z]{2}')]

        # Ensure class_ is an integer
        df["class_"] = df["class_"].fillna(0).astype(int)

        # Ensure enrollment_count is an integer
        df["enrollment_count"] = df["enrollment_count"].fillna(0).astype(int)

        # Fill any remaining missing semester values with a default
        missing_semester = df["semester"].isna()
        if missing_semester.any():
            for idx in df[missing_semester].index:
                course = df.loc[idx, "course_code"]
                # Look for the same course in rows with non-missing semester
                matching_semesters = df[(~df["semester"].isna()) &
                                     (df["course_code"] == course)]["semester"].unique()
                if len(matching_semesters) > 0:
                    # Use the first matching semester
                    df.loc[idx, "semester"] = matching_semesters[0]

        # Now only filter out rows with missing course codes
        df = df[~df["course_code"].isna()]

        # Convert to records for loading
        records = df.to_dict(orient="records")
        return records
