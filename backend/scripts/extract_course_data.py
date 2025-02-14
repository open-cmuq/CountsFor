import os
import json
import pandas as pd

#paths
COURSE_JSON_FOLDER = os.path.abspath("data/course/courses")  
OUTPUT_EXCEL_FILE = os.path.abspath("data/course/course_dataset.xlsx")

COLUMNS_TO_KEEP = [
    "code", "name", "units", "min_units", "max_units",
    "offered_qatar", "offered_pitts", "short_name", "dep_code"
]

def extract_courses_from_json(folder_path):
    """
    reads all course JSON files in a folder and extracts relevant data.
    """
    courses_data = []  

    if not os.path.exists(folder_path):
        print(f"⚠️ Folder not found: {folder_path}")
        return []

    for filename in os.listdir(folder_path):
        if filename.endswith(".json"):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)

            # ignore invalid course files
            if not data.get("success", True):
                continue

            try:
                # extract department code as an integer if not cross registered
                dep_code_str = data["code"].split("-")[0] if data.get("code") else None
                dep_code = int(dep_code_str) if dep_code_str and dep_code_str.isdigit() and len(dep_code_str) == 2 else None

                # check if course is undergraduate
                is_undergraduate = any(s.get("name") == "undergraduate" for s in data.get("student_sets", []))

                # check if is offered in Qatar or Pittsburgh
                offered_qatar = 1 in data.get("offered_in_campuses", [])
                offered_pitts = 2 in data.get("offered_in_campuses", [])

                # checking courses with 0 units
                units = int(data.get("units", 0))

                # filter out cross-registered courses
                if dep_code is None:  
                    continue

                # filter out non-undergraduate courses
                if not is_undergraduate:  
                    continue

                # filter out courses not offered in Qatar or Pittsburgh
                if not (offered_qatar or offered_pitts):  
                    continue

                # filter out any courses where code, name, or offered campuses are missing
                if not data.get("code") or not data.get("name"):
                    continue

                # extract course details (keeping only selected fields)
                course_info = {
                    "code": data.get("code"),
                    "name": data.get("name"),
                    "units": units,
                    "min_units": int(data.get("min_units")) if data.get("min_units") else None,
                    "max_units": int(data.get("max_units")) if data.get("max_units") else None,
                    "offered_qatar": offered_qatar,
                    "offered_pitts": offered_pitts,
                    "short_name": data.get("short_name"),
                    "dep_code": dep_code
                }

                courses_data.append(course_info)

            except KeyError as e:
                print(f"[Error] Missing key {e} in file: {filename}")
            except Exception as e:
                print(f"[Error] Failed to process file {filename}: {e}")

    return courses_data


def handle_missing_values(df):
    """
    handles missing values for each field based on its data type.
    ensures correct types for database insertion.
    """
    print("\n🔍 Handling Missing Values...")

    # fill missing units with 9
    df["units"] = df["units"].fillna(9).astype(int)

    # fill missing min_units and max_units with units
    df["min_units"] = df["min_units"].fillna(df["units"].apply(lambda x: 9 if pd.isna(x) else x)).astype(int)
    df["max_units"] = df["max_units"].fillna(df["units"].apply(lambda x: 9 if pd.isna(x) else x)).astype(int)


    # fill missing short names with good old name
    df["short_name"] = df["short_name"].fillna(df["name"])

    # fill missing department codes with the first two digits of the course code
    df.loc[:, "dep_code"] = df["dep_code"].fillna(
        df["code"].apply(lambda x: int(x.split("-")[0]) if "-" in x and x.split("-")[0].isdigit() else -1)
    ).astype(int)

    df["offered_qatar"] = df["offered_qatar"].astype(bool)
    df["offered_pitts"] = df["offered_pitts"].astype(bool)


    print("✅ Missing values handled successfully!\n")
    return df


def save_to_excel(data, output_file):
    """
    Saves extracted and filtered course data to an Excel file.
    """
    if data:
        df = pd.DataFrame(data)
        df = df[COLUMNS_TO_KEEP]
        df = handle_missing_values(df)
        df.to_excel(output_file, index=False)
        print(df.dtypes)
        print(f"✅ Data successfully saved to {output_file}")
    else:
        print("⚠️ No valid data found to save.")



if __name__ == "__main__":
    extracted_courses = extract_courses_from_json(COURSE_JSON_FOLDER)
    save_to_excel(extracted_courses, OUTPUT_EXCEL_FILE)
