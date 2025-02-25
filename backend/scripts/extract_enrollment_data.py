import os
import pandas as pd

# paths
ENROLLMENT_EXCEL_FILE = os.path.abspath("data/enrollment/CourseEnrollmentByMajorClassS20-S25.xlsx")
OUTPUT_EXCEL_FILE = os.path.abspath("data/enrollment/Enrollment.xlsx")

def format_course_code(code):
    """
    reformat course code to be in the format xx-xxx
    """
    try:
        code_str = str(code).strip()
        if code_str.isdigit():
            # ensure the code has 5 digits (pad with leading zeros if needed)
            code_str = code_str.zfill(5)
            # format as xx-xxx
            return code_str[:2] + "-" + code_str[2:]
        else:
            return code_str
    except Exception as e:
        return code
        
def extract_enrollment_data(file_path):
    """
    reads the enrollment Excel file and processes the data.
    """
    try:
        df = pd.read_excel(file_path)
    except Exception as e:
        print(f"[error] failed to read file {file_path}: {e}")
        return None

    # forward fill merged cells in specific columns
    forward_fill_cols = ["Semester Id (Schedule)", "Course Id", "Section Id", "Department Id"]
    for col in forward_fill_cols:
        if col in df.columns:
            df[col] = df[col].ffill()
        else:
            print(f"[warning] column {col} not found in file.")

    # rename columns to final output names
    rename_dict = {
        "Semester Id (Schedule)": "semester",
        "Course Id": "course_code",
        "Section Id": "section",
        "Department Id": "department",  # added forward fill for Department Id
        "Class Id": "class",
        "Count of Class Id": "enrollment_count"
    }
    df.rename(columns=rename_dict, inplace=True)

    if "course_code" in df.columns:
        df["course_code"] = df["course_code"].apply(format_course_code)
        df["course_code"] = df["course_code"].astype(object)
        # filter out courses whose course_code starts with 2 letters
        df = df[~df["course_code"].str.match(r'^[A-Za-z]{2}')]
    else:
        print("[warning] course_code column not found after renaming.")
    df["section"] = df["section"].astype(str)
    df["department"] = df["department"].astype(str)
    df["class"] = df["class"].astype(int)
    df["enrollment_count"] = df["enrollment_count"].astype(int)
    df["enrollment_id"] = df["course_code"].astype(str) + "_" + df["semester"].astype(str) + "_" + df["class"].astype(str) + "_" + df["section"].astype(str) + "_" + df["department"].astype(str)

    desired_order = ["enrollment_id", "course_code", "semester", "section", "department", "class", "enrollment_count"]
    for col in df.columns:
        if col not in desired_order:
            desired_order.append(col)
    df = df[desired_order]

    return df

def save_to_excel(data, output_file):
    """
    saves extracted enrollment data to an Excel file.
    """
    if data is not None:
        data.to_excel(output_file, index=False)
        print(f"✅ data successfully saved to {output_file}")
    else:
        print("⚠️ no valid data found to save.")

if __name__ == "__main__":
    enrollment_df = extract_enrollment_data(ENROLLMENT_EXCEL_FILE)
    save_to_excel(enrollment_df, OUTPUT_EXCEL_FILE)
