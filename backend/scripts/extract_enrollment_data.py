"""
this script reads the enrollment data from the excel file and processes it.
the processed data is then saved to a new excel file corresponding to the tables in the database
"""

import os
import logging
import pandas as pd

# configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# paths
OG_ENROLLMENT_DIR = os.path.abspath("data/enrollment/CourseEnrollmentByMajorClassS20-S25.xlsx")
ENROLLMENT_DIR = os.path.abspath("data/enrollment/Enrollment.xlsx")

def format_course_code(code):
    """
    reformat course code to be in the format xx-xxx
    """
    try:
        code_str = str(code).strip()
        if code_str.isdigit():
            code_str = code_str.zfill(5)
            return code_str[:2] + "-" + code_str[2:]
        return code_str
    except (ValueError, TypeError) as error:
        logging.warning("failed to format course code: %s, error: %s", code, error)
        return code

def save_to_excel(data, output_file):
    """
    saves extracted enrollment data to an excel file.
    """
    try:
        if data is not None:
            data.to_excel(output_file, index=False)
            logging.info("data successfully saved to %s", output_file)
        else:
            logging.warning("no valid data found to save")
    except (OSError, ValueError) as error:
        logging.error("failed to save data to %s: %s", output_file, error)

def extract_enrollment_data(file_path=ENROLLMENT_DIR):
    """
    reads the enrollment excel file and processes the data.
    """
    try:
        df = pd.read_excel(file_path)
    except (OSError, ValueError) as error:
        logging.error("failed to read file %s: %s", file_path, error)
        return None

    forward_fill_cols = ["Semester Id (Schedule)", "Course Id", "Section Id", "Department Id"]
    for col in forward_fill_cols:
        if col in df.columns:
            df[col] = df[col].ffill()
        else:
            logging.warning("column %s not found in file", col)

    rename_dict = {
        "Semester Id (Schedule)": "semester",
        "Course Id": "course_code",
        "Section Id": "section",
        "Department Id": "department",
        "Class Id": "class",
        "Count of Class Id": "enrollment_count"
    }
    df.rename(columns=rename_dict, inplace=True)

    if "course_code" in df.columns:
        df["course_code"] = df["course_code"].apply(format_course_code).astype(object)
        df = df[~df["course_code"].str.match(r'^[A-Za-z]{2}')]
    else:
        logging.warning("course_code column not found after renaming")

    try:
        df["section"] = df["section"].astype(str)
        df["department"] = df["department"].astype(str)
        df["class"] = df["class"].astype(int)
        df["enrollment_count"] = df["enrollment_count"].astype(int)
    except ValueError as error:
        logging.error("data type conversion error: %s", error)
        return None

    df["enrollment_id"] = (
        df["course_code"].astype(str) + "_" +
        df["semester"].astype(str) + "_" +
        df["class"].astype(str) + "_" +
        df["section"].astype(str) + "_" +
        df["department"].astype(str)
    )

    desired_order = ["enrollment_id", "course_code", "semester", "section", "department",
                     "class", "enrollment_count"]
    df = df[[col for col in desired_order if col in df.columns]]
    save_to_excel(df, ENROLLMENT_DIR)



if __name__ == "__main__":
    extract_enrollment_data()
