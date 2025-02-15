import os
import json
import re
import pandas as pd

# paths
COURSE_JSON_FOLDER = os.path.abspath("data/course/courses")
OUTPUT_EXCEL_FILE = os.path.abspath("data/course/course_dataset.xlsx")
OUTPUT_PREREQS_FILE = os.path.abspath("data/course/course_prerequisites.xlsx")

COLUMNS_TO_KEEP = [
    "code", "name", "units", "min_units", "max_units",
    "offered_qatar", "offered_pitts", "short_name", "description", "dep_code"
]

def extract_req_relationships(req_data):
    """
    Recursively extracts course codes from a requirement data structure.
    It looks into "choices", "constraints", and checks the "screen_name"
    if it matches a simple course code pattern (e.g., "15-112").
    """
    codes = []
    if isinstance(req_data, dict):
        # if req_obj exists, process that instead
        if "req_obj" in req_data:
            codes.extend(extract_req_relationships(req_data["req_obj"]))
        # process nested choices if present
        if "choices" in req_data:
            for choice in req_data["choices"]:
                codes.extend(extract_req_relationships(choice))
        # look into constraints for objects of type "course"
        if "constraints" in req_data:
            for cons in req_data["constraints"]:
                if isinstance(cons, dict) and cons.get("type") == "course":
                    course = cons.get("data", {}).get("course", {})
                    code = course.get("code")
                    if code:
                        codes.append(code)
        # as a fallback, check if screen_name looks like a course code
        if "screen_name" in req_data:
            code = req_data["screen_name"]
            if re.match(r"^\d+-\d+$", code):
                codes.append(code)
    elif isinstance(req_data, list):
        for item in req_data:
            codes.extend(extract_req_relationships(item))
    return codes

def extract_courses_from_json(folder_path):
    """
    Reads all course JSON files in a folder, extracts course data using filtering
    rules, and also extracts prerequisite, corequisite, and anti-requisite relationships.
    Returns four lists: courses_data, prereq_relationships, coreq_relationships, antireq_relationships.
    """
    courses_data = []
    prereq_relationships = []

    if not os.path.exists(folder_path):
        print(f"⚠️ Folder not found: {folder_path}")
        return courses_data, prereq_relationships

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

                # filter out any courses where code or name is missing
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
                    "description": data.get("long_desc"),
                    "dep_code": dep_code
                }
                courses_data.append(course_info)

                course_code = data.get("code")

                # extract prerequisite relationships
                prereqs_data = data.get("prereqs")
                if prereqs_data:
                    # if the structure is nested, use req_obj
                    if isinstance(prereqs_data, dict) and "req_obj" in prereqs_data:
                        prereqs_data = prereqs_data["req_obj"]
                    prereq_codes = extract_req_relationships(prereqs_data)
                    for req in set(prereq_codes):
                        if req:
                            prereq_relationships.append({"course_code": course_code, "prerequisite": req})


            except KeyError as e:
                print(f"[Error] Missing key {e} in file: {filename}")
            except Exception as e:
                print(f"[Error] Failed to process file {filename}: {e}")

    return courses_data, prereq_relationships

def handle_missing_values(df):
    """
    Handles missing values for each field based on its data type.
    Ensures correct types for database insertion.
    """
    print("\n🔍 Handling Missing Values...")

    # fill missing units with 9
    df["units"] = df["units"].fillna(9).astype(int)

    # fill missing min_units and max_units with units
    df["min_units"] = df["min_units"].fillna(df["units"].apply(lambda x: 9 if pd.isna(x) else x)).astype(int)
    df["max_units"] = df["max_units"].fillna(df["units"].apply(lambda x: 9 if pd.isna(x) else x)).astype(int)

    # fill missing short names with the course name
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

def save_relationships_to_excel(data, output_file, relation_type):
    """
    Saves relationship data (prerequisites, corequisites, or antirequisites)
    to an Excel file.
    """
    if data:
        df = pd.DataFrame(data)
        df.to_excel(output_file, index=False)
        print(f"✅ {relation_type.capitalize()} data successfully saved to {output_file}")
    else:
        print(f"⚠️ No valid {relation_type} data found to save.")

if __name__ == "__main__":
    courses_data, prereq_relationships,= extract_courses_from_json(COURSE_JSON_FOLDER)
    save_to_excel(courses_data, OUTPUT_EXCEL_FILE)
    save_relationships_to_excel(prereq_relationships, OUTPUT_PREREQS_FILE, "prerequisite")