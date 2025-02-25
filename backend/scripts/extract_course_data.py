import os
import json
import re
import pandas as pd

# paths
COURSE_JSON_FOLDER = os.path.abspath("data/course/courses")
OUTPUT_COURSE_FILE = os.path.abspath("data/course/Course.xlsx")
OUTPUT_PREREQS_FILE = os.path.abspath("data/course/Prereqs.xlsx")
OUTPUT_OFFERINGS_FILE = os.path.abspath("data/course/Offering.xlsx")
OUTPUT_COURSE_INSTRUCTOR_FILE = os.path.abspath("data/course/Course_Instructor.xlsx")
OUTPUT_INSTRUCTOR_DETAILS_FILE = os.path.abspath("data/course/Instructor.xlsx")

COLUMNS_TO_KEEP = [
    "course_code", "name", "units", "min_units", "max_units",
    "offered_qatar", "offered_pitts", "short_name", "description", "dep_code", "prereqs_text"
]

def extract_req_relationships(req_data):
    """
    Recursively extracts course codes from a requirement data structure.
    It looks into "choices", "constraints", and checks "screen_name"
    if it matches a simple course code pattern (e.g., "15-112").
    """
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

def get_logic_type(req_obj):
    """
    Looks at the constraints in req_obj to see if it specifies 'anyxof' or 'allxof'.
    Returns 'ANY' (default) or 'ALL' accordingly.
    """
    logic_type = "ANY"
    for c in req_obj.get("constraints", []):
        if c.get("type") in ("anyxof", "allxof"):
            is_and = c.get("data", {}).get("is_and", False)
            logic_type = "ALL" if is_and else "ANY"
            break
    return logic_type

def parse_req_obj_with_groups(course_code, req_obj, group_id_counter):
    """
    Parses a top-level req_obj that might contain multiple sub-choices (groups).
    Each top-level 'choice' is treated as one group for that course.
    
    - If the top-level constraint is 'anyxof', then we interpret it as multiple groups (OR).
    - Within each group, we look at the sub-constraint for 'allxof' or 'anyxof' to set logic_type.

    Returns:
      updated_group_id_counter,
      a list of dicts: 
        {
          "course_code": str,
          "prerequisite": str,
          "logic_type": str,
          "group_id": int
        }
    """
    rows = []
    # Check if the top-level is something like "anyxof" => multiple groups, or "allxof" => single group
    # In typical CMU JSON, we see "anyxof" or "allxof" in req_obj["constraints"]
    top_level_logic = get_logic_type(req_obj)  # Usually 'ANY' or 'ALL'
    
    # If there are multiple top-level "choices", each choice can be considered a separate group => OR
    top_choices = req_obj.get("choices", [])
    if not top_choices:
        # If no top-level choices, fallback: flatten
        prereq_codes = extract_req_relationships(req_obj)
        for code in prereq_codes:
            rows.append({
                "course_code": course_code,
                "prerequisite": code,
                "logic_type": top_level_logic,  # fallback
                "group_id": group_id_counter
            })
        group_id_counter += 1
        return group_id_counter, rows

    # For each top-level choice, we treat that as a group
    for choice in top_choices:
        # The group logic is determined by the constraints on this choice
        group_logic = get_logic_type(choice)  # Could be 'ALL' or 'ANY'
        # If none found, fallback to top_level_logic or 'ANY'
        if not choice.get("constraints"):
            group_logic = top_level_logic
        
        # Extract the actual prereq codes in this choice
        codes_in_choice = extract_req_relationships(choice)
        
        # Insert rows for each prereq
        for code in set(codes_in_choice):
            rows.append({
                "course_code": course_code,
                "prerequisite": code,
                "logic_type": group_logic,
                "group_id": group_id_counter
            })
        # Move to the next group ID
        group_id_counter += 1

    return group_id_counter, rows

def extract_courses_from_json(folder_path):
    """
    Reads all course JSON files in a folder, extracts:
      - Course data
      - A more advanced Prereqs table with (course_code, prerequisite, logic_type, group_id)
      - Offerings
      - Instructor data
    """
    courses_data = []
    prereq_relationships = []  # Now each row includes group_id
    offerings_records = []
    course_instructor_mapping = []
    instructors_data = {}

    if not os.path.exists(folder_path):
        print(f"⚠️ Folder not found: {folder_path}")
        return courses_data, prereq_relationships, offerings_records, course_instructor_mapping, list(instructors_data.values())

    for filename in os.listdir(folder_path):
        if filename.endswith(".json"):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)

            # ignore invalid course files
            if not data.get("success", True):
                continue

            try:
                code = data.get("code")
                name = data.get("name")
                if not code or not name:
                    continue

                dep_code_str = code.split("-")[0]
                dep_code = int(dep_code_str) if dep_code_str.isdigit() and len(dep_code_str) == 2 else None

                # check if course is undergraduate
                is_undergraduate = any(s.get("name") == "undergraduate" for s in data.get("student_sets", []))

                # check offered campuses
                offered_qatar = 1 in data.get("offered_in_campuses", [])
                offered_pitts = 2 in data.get("offered_in_campuses", [])

                # convert units to int (defaulting to 0 if missing)
                units = int(data.get("units", 0))

                # filter out cross-registered, non-undergraduate, or courses not offered
                if dep_code is None or not is_undergraduate or not (offered_qatar or offered_pitts):
                    continue

                # get prereqs_text 
                prereqs = data.get("prereqs")
                if isinstance(prereqs, dict):
                    prereqs_text = prereqs.get("text", "")
                else:
                    prereqs_text = ""


                # build course record
                course_info = {
                    "course_code": data.get("code"),
                    "name": data.get("name"),
                    "units": units,
                    "min_units": int(data.get("min_units")) if data.get("min_units") else None,
                    "max_units": int(data.get("max_units")) if data.get("max_units") else None,
                    "offered_qatar": offered_qatar,
                    "offered_pitts": offered_pitts,
                    "short_name": data.get("short_name"),
                    "description": data.get("long_desc"),
                    "dep_code": dep_code,
                    "prereqs_text": prereqs_text  
                }
                courses_data.append(course_info)

                # Prereqs with group_id
                prereqs_data = data.get("prereqs")
                group_id_counter = 1
                if prereqs_data:
                    if isinstance(prereqs_data, dict) and "req_obj" in prereqs_data:
                        req_obj = prereqs_data.get("req_obj")
                        if req_obj is not None:
                            group_id_counter, new_rows = parse_req_obj_with_groups(code, req_obj, group_id_counter)
                            prereq_relationships.extend(new_rows)
                        else:
                            # Fallback: if req_obj is None, just flatten prereqs_data
                            flatten_codes = extract_req_relationships(prereqs_data)
                            for ccode in set(flatten_codes):
                                prereq_relationships.append({
                                    "course_code": code,
                                    "prerequisite": ccode,
                                    "logic_type": "ANY",
                                    "group_id": group_id_counter
                                })
                            group_id_counter += 1


                # Offerings
                if "offerings" in data:
                    for offering in data["offerings"]:
                        campus_id = offering.get("campus_id")
                        if "semesters" in offering:
                            for sem in offering["semesters"]:
                                semester_num = sem.get("semester")
                                year = sem.get("year")
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

                # Instructors
                if "instructors" in data:
                    for instructor in data["instructors"]:
                        andrew_id = instructor.get("username")
                        first_name = instructor.get("first_name")
                        last_name = instructor.get("last_name")
                        if andrew_id and first_name and last_name:
                            course_instructor_mapping.append({
                                "course_code": code,
                                "andrew_id": andrew_id
                            })
                            if andrew_id not in instructors_data:
                                instructors_data[andrew_id] = {
                                    "andrew_id": andrew_id,
                                    "first_name": first_name,
                                    "last_name": last_name
                                }

            except Exception as e:
                print(f"[Error] Failed to process file {filename}: {e}")

    instructors_list = list(instructors_data.values())
    return (courses_data,
            prereq_relationships,
            offerings_records,
            course_instructor_mapping,
            instructors_list)

def handle_missing_values(df):
    """
    Handles missing values for each field based on its data type.
    Ensures correct types for database insertion.
    """
    print("\n🔍 Handling Missing Values...")
    if "units" in df.columns:
        df["units"] = df["units"].fillna(9).astype(int)
    if "min_units" in df.columns:
        df["min_units"] = df["min_units"].fillna(df["units"].apply(lambda x: 9 if pd.isna(x) else x)).astype(int)
    if "max_units" in df.columns:
        df["max_units"] = df["max_units"].fillna(df["units"].apply(lambda x: 9 if pd.isna(x) else x)).astype(int)
    if "short_name" in df.columns and "name" in df.columns:
        df["short_name"] = df["short_name"].fillna(df["name"])
    if "dep_code" in df.columns:
        df["dep_code"] = df["dep_code"].fillna(-1).astype(int)
    if "offered_qatar" in df.columns:
        df["offered_qatar"] = df["offered_qatar"].fillna(False).astype(bool)
    if "offered_pitts" in df.columns:
        df["offered_pitts"] = df["offered_pitts"].fillna(False).astype(bool)
    print("✅ Missing values handled successfully!\n")
    return df

def save_to_excel(data, output_file, columns=None):
    """
    Saves data to an Excel file. If 'columns' is provided, only those columns will be saved.
    """
    if data:
        df = pd.DataFrame(data)
        if columns:
            df = df[columns]
            df = handle_missing_values(df)
        df.to_excel(output_file, index=False)
        print(f"✅ Data successfully saved to {output_file}")
    else:
        print(f"⚠️ No valid data found to save for {output_file}")

if __name__ == "__main__":
    # Unpack the results
    (courses_data, prereq_relationships, offerings_records,
     course_instructor_mapping, instructors_list) = extract_courses_from_json(COURSE_JSON_FOLDER)

    # Save the course data
    save_to_excel(courses_data, OUTPUT_COURSE_FILE, COLUMNS_TO_KEEP)

    # Save the advanced prerequisites table (with group_id)
    # Columns: course_code, prerequisite, logic_type, group_id
    save_to_excel(prereq_relationships, OUTPUT_PREREQS_FILE)

    # Save offerings
    save_to_excel(offerings_records, OUTPUT_OFFERINGS_FILE)

    # Save course-instructor mapping
    save_to_excel(course_instructor_mapping, OUTPUT_COURSE_INSTRUCTOR_FILE)

    # Save unique instructor details
    save_to_excel(instructors_list, OUTPUT_INSTRUCTOR_DETAILS_FILE)
