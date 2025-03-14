"""
This script extracts course and requirement details from audit JSON files and saves them to
Excel files corresponding to the tables in the database.
"""

import os
import re
import logging
import json
import pandas as pd
import utils

pd.set_option('display.max_colwidth', None)

# configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# paths
AUDIT_DIR = "../data/audit"
COURSE_DIR = "../data/course/courses"
COURSE_TABLE_DIR = "../data/course/Course.xlsx"

# -------------------------------------------------------------------------------------------------
# file and directory helpers
# -------------------------------------------------------------------------------------------------
def get_audit_files(folder_path):
    """
    get the two json files in the given folder and determine which is core and which is gen-ed.
    if a file name contains a year (e.g., '2021'), it is classified as the core audit; otherwise
    it is gen-ed. if the check fails, it falls back to the file size method.
    returns a dictionary with the core and gen-ed file paths.
    """
    try:
        json_files = [f for f in os.listdir(folder_path) if f.endswith(".json")]
        if len(json_files) != 2:
            logging.warning("expected 2 json files in %s, found %d", folder_path, len(json_files))
            return None
    except OSError as error:
        logging.error("failed to list files in %s: %s", folder_path, error)
        return None

    core_file, gened_file = None, None
    try:
        # check each file name for a year (e.g., 1990-2099)
        for f in json_files:
            if re.search(r"(19|20)\d{2}", f):
                core_file = f
            else:
                gened_file = f

        # fallback: if one of the files wasn't identified, sort by file size.
        if not core_file or not gened_file:
            file_sizes = {f: os.path.getsize(os.path.join(folder_path, f)) for f in json_files}
            sorted_files = sorted(file_sizes.items(), key=lambda x: x[1], reverse=True)
            core_file, gened_file = sorted_files[0][0], sorted_files[1][0]
    except OSError as error:
        logging.error("failed to determine file sizes in %s: %s", folder_path, error)
        return None

    return {
        "core": os.path.join(folder_path, core_file),
        "gened": os.path.join(folder_path, gened_file)
    }


def get_course_codes():
    """
    retrieves all course codes from course_dir based on filenames.
    assumes course files are named like '02-201.json'.
    """
    codes = set()
    try:
        for filename in os.listdir(COURSE_DIR):
            if filename.endswith(".json"):
                file_path = os.path.join(COURSE_DIR, filename)
                try:
                    with open(file_path, "r", encoding="utf-8") as file:
                        data = json.load(file)
                    if not data.get("success", True):
                        continue
                    codes.add(filename.replace(".json", ""))
                except (OSError, json.JSONDecodeError) as error:
                    logging.warning("skipping %s due to error: %s", filename, error)
    except OSError as error:
        logging.error("failed to list files in %s: %s", COURSE_DIR, error)
    return codes


def get_courses_from_code(dept_code, course_codes):
    """
    finds all courses that start with the given department code.
    example: if dept_code='02', returns all courses like '02-201', '02-202'.
    """
    return [c for c in course_codes if c.startswith(dept_code)]


# -------------------------------------------------------------------------------------------------
# course extraction functions
# -------------------------------------------------------------------------------------------------
def get_courses_from_range(begin, end, req_chain, parent_min_units=None):
    """
    generate course identifiers from a code range, attaching the parent's min_units.
    Returns tuples: (Course or code, Requirement, Inclusion/Exclusion, Type, Min Units)
    """
    courses = []
    try:
        if begin[:2] != end[:2] or begin[:2] == 'XX':
            logging.warning("not including course range: %s to %s", begin, end)
            return courses

        code = begin[:2]
        begin_num = int(begin[3:])
        end_num = int(end[3:])

        if begin_num == 1 and end_num == 999:
            # Use the course range notation as the "code"
            courses = [(code, req_chain, 'Inclusion', 'Code', parent_min_units)]
        else:
            for n in range(begin_num, end_num + 1):
                course_num = f"{code}-{str(n).zfill(3)}"
                courses.append((course_num, req_chain, 'Inclusion', 'Course', parent_min_units))
    except (ValueError, IndexError) as error:
        logging.error("invalid course range format: %s to %s, error: %s", begin, end, error)
    return courses


def get_courses_from_constraint(constraint, req_chain, parent_min_units=None):
    """
    Extracts courses and their required units from constraints.
    Returns tuples: (Course or code, Requirement, Inclusion/Exclusion, Type, Min Units)
    """
    courses = []
    min_units = parent_min_units  # Default to passed value if available
    course_codes = get_course_codes()  # Retrieve available course codes

    try:
        constraint_type = constraint.get("type", "")
        constraint_data = constraint.get("data", {})

        print(f"Processing constraint: {constraint_type}")  # Debug: Show constraint type

        if constraint_type == "course":
            # Direct course constraint
            course_info = constraint_data.get("course", {})
            if course_info:
                course_code = course_info.get("code", "Unknown Course")
                units = course_info.get("units", min_units)
                # Return tuple in the expected order
                extracted_course = (course_code, req_chain, "Inclusion", "Course", units)
                courses.append(extracted_course)
                print(f"Extracted direct course: {extracted_course}")
            else:
                print("ERROR: Missing expected course information in constraint")

        elif constraint_type == "xfromcourseset":
            # Extract courses from course sets
            course_sets = constraint_data.get("conditional_course_sets", [])
            print(f"Found {len(course_sets)} course sets in xfromcourseset")  # Debug: Show count
            for cs in course_sets:
                if "courses" in cs:
                    for course in cs["courses"]:
                        extracted_course = (course, req_chain, "Inclusion", "Course", min_units)
                        courses.append(extracted_course)
                        # Debug line if needed:
                        # print(f"Extracted from courseset: {extracted_course}")
                else:
                    print("ERROR: Missing expected key in constraint: 'courses'")

        elif constraint_type == "xfromdepts":
            # Extract department-based courses
            depts = constraint_data.get("depts", [])
            print(f"Found {len(depts)} departments in xfromdepts")  # Debug: Show count

            for dept in depts:
                dept_code = dept.get("code", "")
                if dept_code:
                    # Generate all possible course codes in the department
                    possible_courses = [f"{dept_code}-{str(i).zfill(3)}" for i in range(1, 1000)]

                    # Filter only the ones that exist in course_dir
                    valid_courses = [c for c in possible_courses if c in course_codes]
                    print(f"Generated {len(possible_courses)} possible courses for dept {dept_code}")  # Debug
                    print(f"Filtered to {len(valid_courses)} valid courses")  # Debug

                    for course in valid_courses:
                        extracted_course = (course, req_chain, "Inclusion", "Course", min_units)
                        courses.append(extracted_course)
                        # Debug line if needed:
                        # print(f"Extracted from department: {extracted_course}")
                else:
                    print("WARNING: Skipping department with missing code")

            # Handle specific course ranges if provided
            code_ranges = constraint_data.get("code_ranges", [])
            print(f"Processing {len(code_ranges)} course ranges")  # Debug

            for range_pair in code_ranges:
                if len(range_pair) == 2:
                    begin, end = range_pair
                    print(f"Generating courses from range: {begin} to {end}")  # Debug
                    range_courses = get_courses_from_range(begin, end, req_chain, min_units)

                    for course_tuple in range_courses:
                        course_code = course_tuple[0]
                        if course_code in course_codes:  # Ensure it exists in course_dir
                            # Use the tuple from range_courses directly
                            courses.append(course_tuple)
                            print(f"Extracted from range: {course_tuple}")  # Debug
                else:
                    print(f"ERROR: Invalid code range format in constraint: {range_pair}")

        elif constraint_type in ["anyxof", "minxunits", "notcountcourseset"]:
            print(f"Skipping non-course constraint: {constraint_type}")  # Debug

        else:
            print(f"WARNING: Unknown constraint type: {constraint_type}")  # Debug

    except Exception as e:
        print(f"ERROR: Exception while processing constraint: {str(e)}")  # Debug

    print(f"Total extracted courses from constraint: {len(courses)}")  # Debug summary
    return courses



def get_courses(data, req_chain, parent_min_units=None):
    """
    Recursively extract courses from audit data.
    Propagates a "min_units" property if available.
    Returns tuples: (Course or code, Requirement, Inclusion/Exclusion, Type, Min Units)
    """
    try:
        current_min_units = data.get("min_units", parent_min_units)
        req = data.get('screen_name', '')
        req = "GenEd" if "General Education" in req else req
        new_req_chain = req if not req_chain else f"{req_chain}---{req}"

        courses = []
        # Process choices if they exist.
        if 'choices' in data and data['choices']:
            for choice in data['choices']:
                courses.extend(get_courses(choice, new_req_chain, current_min_units))

        # Process constraints regardless of choices.
        for constraint in data.get('constraints', []):
            courses.extend(get_courses_from_constraint(constraint, new_req_chain, current_min_units))

        # If no choices or constraints exist, return a default tuple.
        if not courses:
            courses = [(data.get('screen_name', 'Unknown'), req_chain, 'Inclusion', 'Course', current_min_units)]
        return courses

    except KeyError as error:
        logging.error("missing expected key in audit data: %s", error)
        return []


def get_audit(json_path):
    """
    Extracts relevant fields from the audit JSON file,
    returning a list of course tuples and the requirements they satisfy.
    """
    try:
        with open(json_path, "r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError) as error:
        logging.error("failed to read or parse json file %s: %s", json_path, error)
        return []

    try:
        req_major = get_courses(data['requirement'], '')
        req_programs = []

        if data.get('uni_req_tree'):
            for program in data['uni_req_tree'].get('programs', []):
                if ("Degree Check" not in program['screen_name'] and
                    "Total Units" not in program['screen_name']):
                    req_programs.extend(get_courses(program, ''))

        return req_major + req_programs
    except KeyError as error:
        logging.error("missing expected key in audit data: %s", error)
        return []


def extract_audit_data(json_path, course_codes):
    """
    Extracts course and requirement details (including min_units) from an audit JSON file.
    Standardizes the data to tuples in the order:
      (Course or code, Requirement, Inclusion/Exclusion, Type, Min Units)
    """
    try:
        audit_data = get_audit(json_path)
        df = make_data_frame(audit_data)
        cleaned_data = []

        for _, row in df.iterrows():
            processed_req = post_process_requirement(row["Requirement"])

            if row["Inclusion/Exclusion"] == "Inclusion":
                if row["Type"] == "Code":
                    for match in get_courses_from_code(row["Course or code"], course_codes):
                        cleaned_data.append({
                            "requirement": processed_req,
                            "course": match,
                            "min_units": row["Min Units"]
                        })
                else:
                    cleaned_data.append({
                        "requirement": processed_req,
                        "course": row["Course or code"],
                        "min_units": row["Min Units"]
                    })
        print(f"Final extracted courses count: {len(cleaned_data)}")  # Debugging output
        return cleaned_data

    except KeyError as error:
        logging.error("missing expected key in audit data: %s", error)
        return []


# -------------------------------------------------------------------------------------------------
# requirement post-processing
# -------------------------------------------------------------------------------------------------
def post_process_requirement(req):
    """
    Post process the requirement string.
    """
    try:
        parts = req.split('---')
        number_words = {"one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"}
        new_req = req

        # case 1
        if req.startswith("BS in Business Administration") and "select" in parts[1].lower():
            if len(parts) == 6:
                part0 = parts[0].strip()
                cleaned_part1 = re.sub(r'\s*-\s*select.*', '', parts[1],
                                       flags=re.IGNORECASE).strip()
                tokens = [t for t in cleaned_part1.split() if t.lower() not in number_words]
                cleaned_part1 = " ".join(tokens)

                part2, part3 = parts[2].strip(), parts[3].strip()
                tokens_p4 = parts[4].split()
                if tokens_p4 and tokens_p4[0].lower() in number_words:
                    processed_part4 = " ".join(tokens_p4[1:]).strip()
                else:
                    processed_part4 = parts[4].strip()
                part5 = parts[5].strip()
                new_req = "---".join([part0, cleaned_part1, part2, part3, processed_part4, part5])
            elif len(parts) == 5:
                part0 = parts[0].strip()
                cleaned_part1 = re.sub(r'\s*-\s*select.*', '', parts[1],
                                       flags=re.IGNORECASE).strip()
                tokens = [t for t in cleaned_part1.split() if t.lower() not in number_words]
                cleaned_part1 = " ".join(tokens)

                part2 = parts[2].strip()
                tokens_p4 = parts[4].split()
                if tokens_p4 and tokens_p4[0].lower() in number_words:
                    processed_part4 = " ".join(tokens_p4[1:]).strip()
                else:
                    processed_part4 = parts[4].strip()
                new_req = "---".join([part0, cleaned_part1, part2, processed_part4])

        # case 2
        elif req.startswith("BS in Information Systems---Concentration") and len(parts) == 5:
            (part0, part1, part2, part4) = (parts[0].strip(), parts[1].strip(),
                                          parts[2].strip(), parts[4].strip())
            if part4.startswith(part2):
                part4 = part4[len(part2):].strip()
                part4 = part4[1:].strip() if part4.startswith('-') else part4
            new_req = "---".join([part0, part1, part2, part4])

        # case 3
        course_code_pattern = r'\b(?:\d{5}|\d{2}-\d{3}|[a-zA-Z]{2}-\d{3})\b'
        final_parts = []
        for part in new_req.split('---'):
            stripped = part.strip()
            if not (re.search(course_code_pattern, stripped) or
                    re.search(r'\bchoose\b', stripped, flags=re.IGNORECASE) or
                    re.search(r'\bselect\b', stripped, flags=re.IGNORECASE)):
                final_parts.append(stripped)

        return "---".join(final_parts)

    except (IndexError, AttributeError, TypeError) as error:
        logging.error("error processing requirement string: %s", error)
        return req


# -------------------------------------------------------------------------------------------------
# DataFrame and Excel output
# -------------------------------------------------------------------------------------------------
def make_data_frame(audit):
    """
    Convert audit list into a structured DataFrame with additional course info,
    including the new "min units" field.
    Expects each record to be a tuple:
      (Course or code, Requirement, Inclusion/Exclusion, Type, Min Units)
    """
    try:
        df = pd.DataFrame(
            audit,
            columns=[
                'Course or code', 'Requirement', 'Inclusion/Exclusion', 'Type', 'Min Units'
            ]
        )
        df["Pre-reqs"] = df["Course or code"].apply(utils.getPreReqs)
        df["Title"] = df["Course or code"].apply(utils.getCourseTitle)
        df["Units"] = df["Course or code"].apply(utils.getCourseUnits)

        return df[[
            "Type", "Inclusion/Exclusion", "Course or code", "Title",
            "Units", "Pre-reqs", "Requirement", "Min Units"
        ]]
    except KeyError as error:
        logging.error("missing expected column in audit data: %s", error)
        return pd.DataFrame()


def save_to_excel(data, output_path):
    """
    Saves extracted and cleaned data to an Excel file.
    """
    try:
        if not data:
            logging.warning("no data to save for %s", output_path)
            return
        pd.DataFrame(data).to_excel(output_path, index=False)
        logging.info("data successfully saved to %s", output_path)

    except ValueError as error:
        logging.error("invalid data format for saving to %s: %s", output_path, error)
    except PermissionError as error:
        logging.error("permission denied when saving to %s: %s", output_path, error)
    except OSError as error:
        logging.error("os error occurred while saving to %s: %s", output_path, error)


# -------------------------------------------------------------------------------------------------
# Main function
# -------------------------------------------------------------------------------------------------
def process_all_audits():
    """
    Processes all audit JSON files in each major folder and saves three Excel files:
      - countsfor: columns: requirement, course_code
      - requirement: columns: requirement, audit_id, min_units
      - audit: columns: audit_id, name, type, major
    """
    try:
        course_codes = get_course_codes()
        combined_data = []

        for major in os.listdir(AUDIT_DIR):
            major_path = os.path.join(AUDIT_DIR, major)
            if not os.path.isdir(major_path):
                continue

            audit_files = get_audit_files(major_path)
            if not audit_files:
                continue

            logging.info("processing audit files for major: %s", major)

            # process and save core requirements
            core_data = extract_audit_data(audit_files["core"], course_codes)
            core_output_path = os.path.join(major_path, f"{major}_core.xlsx")
            save_to_excel(core_data, core_output_path)

            for d in core_data:
                d.update({"audit_type": 0, "major": major,
                          "audit": d["requirement"].split('---')[0].strip()})
                combined_data.append(d)

            # process and save general education requirements
            gened_data = extract_audit_data(audit_files["gened"], course_codes)
            gened_output_path = os.path.join(major_path, f"{major}_gened.xlsx")
            save_to_excel(gened_data, gened_output_path)

            for d in gened_data:
                d.update({"audit_type": 1, "major": major,
                          "audit": d["requirement"].split('---')[0].strip()})
                combined_data.append(d)

        if combined_data:
            df_audit = pd.DataFrame(combined_data)[["audit",
                                                    "audit_type", "major"]].drop_duplicates()
            df_audit["audit_id"] = df_audit["major"] + "_" + df_audit["audit_type"].astype(str)
            df_audit = df_audit.rename(columns={"audit": "name", "audit_type": "type"})

            df_course = pd.read_excel(COURSE_TABLE_DIR)
            existing_courses = set(df_course["course_code"].astype(str))
            df_countsfor = pd.DataFrame(combined_data)[
                ["requirement", "course"]].rename(columns={"course": "course_code"})
            df_countsfor = df_countsfor[df_countsfor["course_code"].isin(existing_courses)]

            print(f"Total courses before filtering: {len(df_countsfor)}")
            print(f"Total matching courses in df_course: {df_countsfor['course_code'].isin(existing_courses).sum()}")

            df_requirement = pd.DataFrame(combined_data)[["requirement", "major",
                                                          "audit_type"]].drop_duplicates()
            df_requirement = df_requirement.rename(columns={"audit_type": "type"})
            df_requirement = df_requirement.merge(df_audit[["audit_id", "major", "type"]],
                                                  on=["major", "type"], how="left")
            df_requirement = df_requirement[["requirement", "audit_id"]]

            counts_for_output_path = os.path.join(AUDIT_DIR, "CountsFor.xlsx")
            requirement_output_path = os.path.join(AUDIT_DIR, "Requirement.xlsx")
            audit_output_path = os.path.join(AUDIT_DIR, "Audit.xlsx")

            save_to_excel(df_countsfor.to_dict(orient='records'), counts_for_output_path)
            save_to_excel(df_requirement.to_dict(orient='records'), requirement_output_path)
            save_to_excel(df_audit.to_dict(orient='records'), audit_output_path)

            logging.info("audit data processing complete, files saved.")

    except (OSError, KeyError, ValueError) as error:
        logging.error("error occurred during audit processing: %s", error)

if __name__ == "__main__":
    process_all_audits()
