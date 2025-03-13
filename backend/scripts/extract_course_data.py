"""
This script extracts course data from JSON files and saves them to Excel
files corresponding to database tables.
It extracts course data, prerequisites, offerings, and instructor data.
"""

import os
import json
import re
import logging
import pandas as pd

# configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# paths
COURSE_JSON_DIR = os.path.abspath("data/course/courses")
COURSE_TABLE_DIR = os.path.abspath("data/course/Course.xlsx")
PRERQ_TABLE_DIR = os.path.abspath("data/course/Prereqs.xlsx")
OFFERING_TABLE_DIR = os.path.abspath("data/course/Offering.xlsx")
COURSE_INSTRUCTOR_TABLE_DIR = os.path.abspath("data/course/Course_Instructor.xlsx")
INSTRUCTOR_TABLE_DIR = os.path.abspath("data/course/Instructor.xlsx")

COLUMNS_TO_KEEP = [
    "course_code", "name", "units", "min_units", "max_units",
    "offered_qatar", "offered_pitts", "short_name", "description", "dep_code", "prereqs_text"
]

#--------------------------------------------------------------------------------------------------
# prerequisite extraction helpers
#--------------------------------------------------------------------------------------------------
def extract_req_relationships(req_data):
    """
    recursively extracts course codes from a requirement data structure.
    it looks into "choices", "constraints", and checks "screen_name"
    if it matches a simple course code pattern (e.g., "15-112").
    """
    try:
        codes = []
        if isinstance(req_data, dict):
            if "req_obj" in req_data:
                codes.extend(extract_req_relationships(req_data["req_obj"]))
            if "choices" in req_data:
                for choice in req_data["choices"]:
                    codes.extend(extract_req_relationships(choice))
            if "constraints" in req_data:
                for cons in req_data["constraints"]:
                    if isinstance(cons, dict) and cons.get("type") == "course":
                        course = cons.get("data", {}).get("course", {})
                        code = course.get("code")
                        if code:
                            codes.append(code)
            if "screen_name" in req_data:
                code = req_data["screen_name"]
                if re.match(r"^\d+-\d+$", code):
                    codes.append(code)
        elif isinstance(req_data, list):
            for item in req_data:
                codes.extend(extract_req_relationships(item))
        return codes
    except (KeyError, TypeError) as error:
        logging.error("error extracting requirement relationships: %s", error)
        return []


def get_logic_type(req_obj):
    """
    looks at the constraints in req_obj to see if it specifies 'anyxof' or 'allxof'.
    returns 'ANY' (default) or 'ALL' accordingly.
    """
    try:
        logic_type = "ANY"
        for constraint in req_obj.get("constraints", []):
            if constraint.get("type") in ("anyxof", "allxof"):
                is_and = constraint.get("data", {}).get("is_and", False)
                return "ALL" if is_and else "ANY"
        return logic_type
    except (KeyError, AttributeError, TypeError) as error:
        logging.error("error determining logic type: %s", error)
        return "ANY"

def parse_req_obj(course_code, req_obj, group_id_counter):
    """
    parses a top-level req_obj that might contain multiple sub-choices (groups).
    returns the updated group_id_counter and a list of prerequisite relationships.
    """
    try:
        rows = []
        top_level_logic = get_logic_type(req_obj)
        top_choices = req_obj.get("choices", [])

        if not top_choices:
            prereq_codes = extract_req_relationships(req_obj)
            for code in prereq_codes:
                rows.append({
                    "course_code": course_code,
                    "prerequisite": code,
                    "logic_type": top_level_logic,
                    "group_id": group_id_counter
                })
            group_id_counter += 1
            return group_id_counter, rows

        for choice in top_choices:
            group_logic = get_logic_type(choice) if choice.get("constraints") else top_level_logic
            codes_in_choice = extract_req_relationships(choice)

            for code in set(codes_in_choice):
                rows.append({
                    "course_code": course_code,
                    "prerequisite": code,
                    "logic_type": group_logic,
                    "group_id": group_id_counter
                })
            group_id_counter += 1

        return group_id_counter, rows
    except (KeyError, TypeError) as error:
        logging.error("error parsing requirement object for course %s: %s", course_code, error)
        return group_id_counter, []

# -------------------------------------------------------------------------------------------------
# course extraction helpers
# -------------------------------------------------------------------------------------------------

def extract_offerings(data, code, offerings_records):
    """
    extracts course offerings from a course json file and adds them to the offerings_records list.
    """
    try:
        for offering in data.get("offerings", []):
            campus_id = offering.get("campus_id")
            for sem in offering.get("semesters", []):
                semester_num, year = sem.get("semester"), sem.get("year")
                if semester_num and year:
                    sem_map = {1: "F", 2: "S", 3: "M"}
                    sem_letter = sem_map.get(semester_num, "X")
                    sem_str = f"{sem_letter}{str(year)[-2:]}"
                    offerings_records.append({
                        "offering_id": f"{code}_{sem_str}_{campus_id}",
                        "course_code": code,
                        "semester": sem_str,
                        "campus_id": campus_id
                    })
    except KeyError as error:
        logging.error("missing key in offerings extraction for course %s: %s", code, error)
    return offerings_records


def extract_prereqs(data, code, prereq_relationships):
    """
    extracts course prerequisites from a course json file and adds them to the
    prereq_relationships list.
    """
    try:
        prereqs_data = data.get("prereqs")
        group_id_counter = 1
        if prereqs_data:
            if isinstance(prereqs_data, dict) and "req_obj" in prereqs_data:
                req_obj = prereqs_data.get("req_obj")
                if req_obj is not None:
                    group_id_counter, new_rows = parse_req_obj(code, req_obj, group_id_counter)
                    prereq_relationships.extend(new_rows)
                else:
                    flatten_codes = extract_req_relationships(prereqs_data)
                    for ccode in set(flatten_codes):
                        prereq_relationships.append({
                            "course_code": code,
                            "prerequisite": ccode,
                            "logic_type": "ANY",
                            "group_id": group_id_counter
                        })
                    group_id_counter += 1
    except KeyError as error:
        logging.error("missing key in prerequisites extraction for course %s: %s", code, error)
    return prereq_relationships


def extract_instructors(data, code, course_instructor, instructors_data):
    """
    extracts course instructors from a course json file and adds them to the course_instructor list.
    """
    try:
        for instructor in data.get("instructors", []):
            andrew_id = instructor.get("username")
            first_name = instructor.get("first_name")
            last_name = instructor.get("last_name")
            if andrew_id and first_name and last_name:
                course_instructor.append({
                    "course_code": code,
                    "andrew_id": andrew_id
                })
                if andrew_id not in instructors_data:
                    instructors_data[andrew_id] = {
                        "andrew_id": andrew_id,
                        "first_name": first_name,
                        "last_name": last_name
                    }
    except KeyError as error:
        logging.error("missing key in instructor extraction for course %s: %s", code, error)
    return course_instructor

# -------------------------------------------------------------------------------------------------
# data processing helpers
# -------------------------------------------------------------------------------------------------
def handle_missing_values(df):
    """
    handles missing values for each field based on its data type.
    ensures correct types for database insertion.
    """
    try:
        logging.info("handling missing values in dataframe")
        if "units" in df.columns:
            df["units"] = df["units"].fillna(9).astype(int)
        if "min_units" in df.columns:
            df["min_units"] = df["min_units"].fillna(
                df["units"].apply(lambda x: 9 if pd.isna(x) else x)).astype(int)
        if "max_units" in df.columns:
            df["max_units"] = df["max_units"].fillna(
                df["units"].apply(lambda x: 9 if pd.isna(x) else x)).astype(int)
        if "short_name" in df.columns and "name" in df.columns:
            df["short_name"] = df["short_name"].fillna(df["name"])
        if "dep_code" in df.columns:
            df["dep_code"] = df["dep_code"].fillna(-1).astype(int)
        if "offered_qatar" in df.columns:
            df["offered_qatar"] = df["offered_qatar"].fillna(False).astype(bool)
        if "offered_pitts" in df.columns:
            df["offered_pitts"] = df["offered_pitts"].fillna(False).astype(bool)
        logging.info("missing values handled successfully")
    except KeyError as error:
        logging.error("missing expected column in dataframe: %s", error)
    return df


def save_to_excel(data, output_file, columns=None):
    """
    saves data to an excel file. if 'columns' is provided, only those columns will be saved.
    """
    try:
        if not data:
            logging.warning("no data to save for %s", output_file)
            return

        df = pd.DataFrame(data)
        if columns:
            df = df[columns]
            df = handle_missing_values(df)
        df.to_excel(output_file, index=False)
        logging.info("data successfully saved to %s", output_file)
    except ValueError as error:
        logging.error("invalid data format for saving to %s: %s", output_file, error)
    except PermissionError as error:
        logging.error("permission denied when saving to %s: %s", output_file, error)
    except OSError as error:
        logging.error("os error occurred while saving to %s: %s", output_file, error)

# -------------------------------------------------------------------------------------------------
# main function
# -------------------------------------------------------------------------------------------------
def process_all_courses(folder_path=COURSE_JSON_DIR):
    """
    reads all course json files in a folder and extracts course data, prerequisites, offerings,
    and instructor data.
    """
    courses_data = []
    prereq_relationships = []
    offerings_records = []
    course_instructor = []
    instructors_data = {}

    if not os.path.exists(folder_path):
        logging.warning("folder not found: %s", folder_path)
        return

    try:
        for filename in os.listdir(folder_path):
            if not filename.endswith(".json"):
                continue

            file_path = os.path.join(folder_path, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    data = json.load(file)
                if not data.get("success", True):
                    continue

                try:
                    code = data.get("code")
                    name = data.get("name")

                    if not code or not name:
                        continue

                    dep_code_str = code.split("-")[0]
                    dep_code = int(dep_code_str) if (dep_code_str.isdigit()
                                                     and len(dep_code_str) == 2) else None
                    is_undergraduate = any(s.get("name") == "undergraduate"
                                           for s in data.get("student_sets", []))
                    offered_qatar = 1 in data.get("offered_in_campuses", [])
                    offered_pitts = 2 in data.get("offered_in_campuses", [])
                    units = data.get("units", 0)

                    try:
                        units = int(units) if units is not None else 0
                    except ValueError:
                        logging.warning("invalid unit value for course %s: %s, defaulting to 0",
                                        code, units)
                        units = 0

                    if (dep_code is None or not is_undergraduate
                    or not (offered_qatar or offered_pitts)):
                        continue

                    prereqs = data.get("prereqs")
                    prereqs_text = prereqs.get("text", "") if isinstance(prereqs, dict) else ""

                    course_info = {
                        "course_code": data.get("code"),
                        "name": data.get("name"),
                        "units": units,
                        "min_units": int(data.get("min_units", 0)),
                        "max_units": int(data.get("max_units", 0)),
                        "offered_qatar": offered_qatar,
                        "offered_pitts": offered_pitts,
                        "short_name": data.get("short_name"),
                        "description": data.get("long_desc"),
                        "dep_code": dep_code,
                        "prereqs_text": prereqs_text
                    }
                    courses_data.append(course_info)

                    prereq_relationships = extract_prereqs(data, code, prereq_relationships)
                    offerings_records = extract_offerings(data, code, offerings_records)
                    course_instructor = extract_instructors(data, code, course_instructor,
                                                            instructors_data)
                except KeyError as error:
                    logging.error("missing expected key in file %s: %s", filename, error)
            except (OSError, json.JSONDecodeError) as error:
                logging.warning("skipping file %s due to error: %s", filename, error)
    except OSError as error:
        logging.error("failed to list files in %s: %s", folder_path, error)

    instructors_list = list(instructors_data.values())
    save_to_excel(courses_data, COURSE_TABLE_DIR, COLUMNS_TO_KEEP)
    save_to_excel(prereq_relationships, PRERQ_TABLE_DIR)
    save_to_excel(offerings_records, OFFERING_TABLE_DIR)
    save_to_excel(course_instructor, COURSE_INSTRUCTOR_TABLE_DIR)
    save_to_excel(instructors_list, INSTRUCTOR_TABLE_DIR)

if __name__ == "__main__":
    process_all_courses()
