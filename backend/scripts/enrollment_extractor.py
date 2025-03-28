"""
Extracts and processes enrollment data from Excel files.
"""

import os
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

    def extract_enrollment_data(self, file_path: str) -> str:
        """
        Reads and processes enrollment data from the given Excel file.
        Returns the path of the saved Excel file.
        """
        try:
            df = pd.read_excel(file_path)
        except (OSError, ValueError) as error:
            logging.error("Failed to read file %s: %s", file_path, error)
            return ""

        # Forward fill specific columns
        forward_fill_cols = ["Semester Id (Schedule)", "Course Id", "Section Id", "Department Id"]
        for col in forward_fill_cols:
            if col in df.columns:
                df[col] = df[col].ffill()
            else:
                logging.warning("Column %s not found in file", col)

        # Rename columns for consistency
        rename_dict = {
            "Semester Id (Schedule)": "semester",
            "Course Id": "course_code",
            "Section Id": "section",
            "Department Id": "department",
            "Class Id": "class",
            "Count of Class Id": "enrollment_count"
        }
        df.rename(columns=rename_dict, inplace=True)

        # Format course codes and filter invalid codes
        if "course_code" in df.columns:
            df["course_code"] = df["course_code"].apply(self.format_course_code).astype(str)
            df = df[~df["course_code"].str.match(r'^[A-Za-z]{2}')]
        else:
            logging.warning("course_code column not found after renaming")

        try:
            df["section"] = df["section"].astype(str)
            df["department"] = df["department"].astype(str)
            df["class"] = df["class"].astype(int)
            df["enrollment_count"] = df["enrollment_count"].astype(int)
        except ValueError as error:
            logging.error("Data type conversion error: %s", error)
            return ""

        # Generate enrollment ID
        df["enrollment_id"] = (
            df["course_code"].astype(str) + "_" +
            df["semester"].astype(str) + "_" +
            df["class"].astype(str) + "_" +
            df["section"].astype(str) + "_" +
            df["department"].astype(str)
        )

        desired_order = ["enrollment_id", "course_code", "semester", "section",
                     "department", "class", "enrollment_count"]
        df = df[[col for col in desired_order if col in df.columns]]

        return df.to_dict(orient="records")


