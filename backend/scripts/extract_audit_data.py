import os
import json
import pandas as pd
import utils
import re

pd.set_option('display.max_colwidth', None)

# paths
AUDIT_DIR = "data/audit"
COURSE_DIR = "data/course"
OUTPUT_EXCEL_FILE = os.path.abspath("data/audit/audit_dataset.xlsx")

# ----------------------------------------
# file and directory helpers
# ----------------------------------------
def get_audit_files(folder_path):
    """
    get the two JSON files in the given folder and determine which is core and which is gen-ed.
    if a file name contains a year (e.g., '2021'), it is classified as the core audit; otherwise it is gen-ed.
    if the check fails, it falls back to the file size method.
    returns a dictionary with the core and gen-ed file paths.
    """
    json_files = [f for f in os.listdir(folder_path) if f.endswith(".json")]
    if len(json_files) != 2:
        print(f"[Warning] Expected 2 JSON files in {folder_path}, found {len(json_files)}")
        return None

    core_file = None
    gened_file = None
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
        core_file = sorted_files[0][0]
        gened_file = sorted_files[1][0]
    
    return {
        "core": os.path.join(folder_path, core_file),
        "gened": os.path.join(folder_path, gened_file)
    }

def get_course_codes():
    """
    retrieves all course codes from COURSE_DIR based on filenames.
    assumes course files are named like '02-201.json'.
    only returns course codes for files where the course JSON indicates success.
    """
    codes = set()
    for filename in os.listdir(COURSE_DIR):
        if filename.endswith(".json"):
            file_path = os.path.join(COURSE_DIR, filename)
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                # skip the file if its content does not indicate success.
                if not data.get("success", True):
                    continue
                codes.add(filename.replace(".json", ""))
            except Exception as e:
                print(f"[Warning] Skipping {filename} due to error: {e}")
                continue
    return codes


def get_courses_from_code(dept_code, course_codes):
    """
    finds all courses that start with the given department code.
    example: If dept_code='02', returns all courses like '02-201', '02-202'.
    """
    return [c for c in course_codes if c.startswith(dept_code)]

# ----------------------------------------
# course extraction functions
# ----------------------------------------
def getCoursesFromRange(begin, end, inc_exc, req_chain, parent_min_units=None):
    """
    Generate course identifiers from a code range, attaching the parent's min_units.
    """
    courses = []
    if begin[:2] != end[:2] or begin[:2] == 'XX':
        print("[Warning] Not including course range:", begin, end)
        return courses

    code = begin[:2]
    begin_num = int(begin[3:])
    end_num = int(end[3:])
    if begin_num == 1 and end_num == 999:
        courses = [(code, req_chain, inc_exc, 'Code', parent_min_units)]
    else:
        for n in range(begin_num, end_num + 1):
            course_num = f"{code}-{str(n).zfill(3)}"
            courses.append((course_num, req_chain, inc_exc, 'Course', parent_min_units))
    return courses

def getCoursesFromConstraint(constraint, req_chain, parent_min_units=None):
    """
    Extract courses based on a given constraint type,
    propagating parent's min_units if available.
    """
    constraint_type = constraint['type']
    
    if constraint_type == 'xfromcourseset':
        courses = constraint['data']['courses']
        ranges = constraint['data']['code_ranges']
        courses_from_range = []
        for r in ranges:
            courses_from_range.extend(getCoursesFromRange(r[0], r[1], 'Inclusion', req_chain, parent_min_units))
        return [(c, req_chain, 'Inclusion', 'Course', parent_min_units) for c in courses] + courses_from_range
    
    elif constraint_type == 'xfromdepts':
        depts = constraint['data']['depts']
        courses = constraint['data']['additional_courses']
        return ([(d['code'], req_chain, 'Inclusion', 'Code', parent_min_units) for d in depts] +
                [(c, req_chain, 'Inclusion', 'Course', parent_min_units) for c in courses])
    
    elif constraint_type == 'notcountcourseset':
        courses = constraint['data']['courses']
        return [(c, req_chain, 'Exclusion', 'Course', parent_min_units) for c in courses]
    
    else:
        print("[Warning] Not accounting for constraint:", constraint_type)
        return []

def getCourses(data, req_chain, parent_min_units=None):
    """
    Recursively extract courses from audit data.
    Propagates a "min_units" property if available.
    """
    current_min_units = data.get("min_units", parent_min_units)
    if 'choices' in data:
        req = data['screen_name']
        req = "GenEd" if "General Education" in req else req  # Hack for audit comparison
        new_req_chain = req if not req_chain else req_chain + '---' + req
        if data['choices']:
            courses = []
            for choice in data['choices']:
                courses.extend(getCourses(choice, new_req_chain, current_min_units))
            return courses
        else:
            courses = []
            for constraint in data['constraints']:
                courses.extend(getCoursesFromConstraint(constraint, new_req_chain, current_min_units))
            return courses
    else:
        return [(data['screen_name'], req_chain, 'Inclusion', 'Course', current_min_units)]


def getAudit(json_path):
    """
    Extracts relevant fields from the audit JSON file,
    returning a list of courses and the requirements they satisfy.
    """
    with open(json_path, "r") as file:
        data = json.load(file)
    req_major = getCourses(data['requirement'], '')
    req_programs = []
    if data.get('uni_req_tree'):
        for program in data['uni_req_tree'].get('programs', []):
            if "Degree Check" not in program['screen_name'] and "Total Units" not in program['screen_name']:
                req_programs.extend(getCourses(program, ''))
    return req_major + req_programs

# ----------------------------------------
# requirement post-processing
# ----------------------------------------
def post_process_requirement(req):
    """
    Post process the requirement string.
    
    Handles two cases:
    
    1. For requirements starting with "BS in Business Administration" and containing a selection instruction 
       in the second part:
       
       a. For a five-part string like:
          "BS in Business Administration---Concentration - select 1 concentration from the list below---Operations Management---Operations Management Concentration---Two Area Electives"
          it becomes:
          "BS in Business Administration---Concentration---Operations Management---Area Electives"
          
       b. For a six-part string like:
          "BS in Business Administration---Concentration - select 1 concentration from the list below---Operations Management---Operations Management Concentration---Two Area Electives---70-462 Uncertainty and Risk Modeling  OR 70-453 Business Technology for Consulting"
          it becomes:
          "BS in Business Administration---Concentration---Operations Management---Operations Management Concentration---Area Electives---70-462 Uncertainty and Risk Modeling  OR 70-453 Business Technology for Consulting"
          
       In both cases, the cleaning steps are:
         - In the second part, remove everything from (and including) a space before "select" onward.
         - Remove any number words (e.g., "one", "two", etc.) from the cleaned second part.
         - In the part that lists area electives (fifth part in the six-part case or last part in the five-part case),
           remove the first word if it is a number word.
    
    2. For requirements starting with "BS in Information Systems---Concentration" and formatted as:
       "BS in Information Systems---Concentration---Data Science---Data Science Concentration---Data Science Technical Core"
       it becomes:
       "BS in Information Systems---Concentration---Data Science---Technical Core"

    3. General rule: After the above processing, if any section (substring between '---')
       contains a course code or the words "choose" and "select" (case-insensitive), that section is removed completely.
       Course codes can be in one of these forms: 
         • 5 consecutive digits (e.g., "67101")
         • 2 digits, a hyphen, and 3 digits (e.g., "67-101")
         • 2 letters, a hyphen, and 3 digits (e.g., "xx-213")
       This removal applies even if the section has additional text.
    """

    course_code_regex = r'^(?:\d{5}|\d{2}-\d{3}|[a-zA-Z]{2}-\d{3})$'
    
    parts = req.split('---')
    number_words = {"one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"}
    new_req = req 

    # case 1
    if req.startswith("BS in Business Administration") and "select" in parts[1].lower():
        if len(parts) == 6:
            part0 = parts[0].strip()
            cleaned_part1 = re.sub(r'\s*-\s*select.*', '', parts[1], flags=re.IGNORECASE).strip()
            tokens = cleaned_part1.split()
            tokens = [t for t in tokens if t.lower() not in number_words]
            cleaned_part1 = " ".join(tokens)
            
            part2 = parts[2].strip()
            part3 = parts[3].strip()

            tokens_p4 = parts[4].split()
            if tokens_p4 and tokens_p4[0].lower() in number_words:
                processed_part4 = " ".join(tokens_p4[1:]).strip()
            else:
                processed_part4 = parts[4].strip()
            part5 = parts[5].strip()
            new_req = "---".join([part0, cleaned_part1, part2, part3, processed_part4, part5])
        elif len(parts) == 5:
            part0 = parts[0].strip()
            cleaned_part1 = re.sub(r'\s*-\s*select.*', '', parts[1], flags=re.IGNORECASE).strip()
            tokens = cleaned_part1.split()
            tokens = [t for t in tokens if t.lower() not in number_words]
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
        part0 = parts[0].strip()
        part1 = parts[1].strip()
        part2 = parts[2].strip()
        part4 = parts[4].strip()
    
        if part4.startswith(part2):
            part4 = part4[len(part2):].strip()
            if part4.startswith('-'):
                part4 = part4[1:].strip()
        new_req = "---".join([part0, part1, part2, part4])
    
    # case 3 
    course_code_pattern = r'\b(?:\d{5}|\d{2}-\d{3}|[a-zA-Z]{2}-\d{3})\b'
    final_parts = []
    for part in new_req.split('---'):
        stripped = part.strip()
        if re.search(course_code_pattern, stripped) or re.search(r'\bchoose\b', stripped, flags=re.IGNORECASE) \
        or re.search(r'\bselect\b', stripped, flags=re.IGNORECASE):
            continue
        final_parts.append(stripped)
    return "---".join(final_parts)

# ----------------------------------------
# dataFrame and excel output
# ----------------------------------------
def makeDataFrame(audit):
    """
    Convert audit list into a structured DataFrame with additional course info,
    including the new "Min Units" field.
    """
    df = pd.DataFrame(audit, columns=['Course or code', 'Requirement', 'Inclusion/Exclusion', 'Type', 'Min Units'])
    df["Pre-reqs"] = df["Course or code"].apply(utils.getPreReqs)
    df["Title"] = df["Course or code"].apply(utils.getCourseTitle)
    df["Units"] = df["Course or code"].apply(utils.getCourseUnits)
    return df[["Type", "Inclusion/Exclusion", "Course or code", "Title", "Units", "Pre-reqs", "Requirement", "Min Units"]]

def extract_audit_data(json_path, course_codes):
    """
    Extracts course and requirement details (including min_units) from an audit JSON file.
    """
    audit_data = getAudit(json_path)
    df = makeDataFrame(audit_data)
    
    cleaned_data = []
    for _, row in df.iterrows():
        # Use post_process_requirement to clean the requirement string
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
    return cleaned_data

def save_to_excel(data, output_path):
    """
    saves extracted and cleaned data to an Excel file.
    """
    pd.DataFrame(data).to_excel(output_path, index=False)
    print(f"✅ Data saved to {output_path}")

def process_all_audits():
    """
    Processes all audit JSON files in each major folder and saves three Excel files:
      - CountsFor: columns: requirement, course_code
      - Requirement: columns: requirement, audit_name, min_units
      - Audit: columns: name, type, major
    """
    course_codes = get_course_codes()
    combined_data = []  
    for major in os.listdir(AUDIT_DIR):
        major_path = os.path.join(AUDIT_DIR, major)
        if not os.path.isdir(major_path):
            continue

        audit_files = get_audit_files(major_path)
        if not audit_files:
            continue

        print(audit_files)
        # process and save core requirements
        core_data = extract_audit_data(audit_files["core"], course_codes)
        core_output_path = os.path.join(major_path, f"{major}_core.xlsx")
        save_to_excel(core_data, core_output_path)
        
        # append core data to combined_data with audit_type=0 (for core)
        for d in core_data:
            d["audit_type"] = 0  # core -> 0
            d["major"] = major
            d["audit"] = d["requirement"].split('---')[0].strip()
            combined_data.append(d)

        # process and save general education requirements
        gened_data = extract_audit_data(audit_files["gened"], course_codes)
        gened_output_path = os.path.join(major_path, f"{major}_gened.xlsx")
        save_to_excel(gened_data, gened_output_path)
        
        # append gen-ed data to combined_data with audit_type=1 (for gened)
        for d in gened_data:
            d["audit_type"] = 1  # gened -> 1
            d["major"] = major
            d["audit"] = d["requirement"].split('---')[0].strip()
            combined_data.append(d)

    if combined_data:
        # Create CountsFor table: requirement and course_code (rename "course" to "course_code")
        df_countsfor = pd.DataFrame(combined_data)[["requirement", "course"]].rename(columns={"course": "course_code"})
        
        # Create Requirement table: requirement, audit_name (from "audit"), and min_units
        df_requirement = pd.DataFrame(combined_data)[["requirement", "audit", "min_units"]].rename(columns={"audit": "audit_name"})
        
        # Create Audit table: name (from "audit"), type (from "audit_type"), and major.
        df_audit = pd.DataFrame(combined_data)[["audit", "audit_type", "major"]].rename(columns={"audit": "name", "audit_type": "type"})
        df_audit = df_audit.drop_duplicates()
        
        counts_for_output_path = os.path.join(AUDIT_DIR, "CountsFor.xlsx")
        requirement_output_path = os.path.join(AUDIT_DIR, "Requirement.xlsx")
        audit_output_path = os.path.join(AUDIT_DIR, "Audit.xlsx")
        
        df_countsfor.to_excel(counts_for_output_path, index=False)
        df_requirement.to_excel(requirement_output_path, index=False)
        df_audit.to_excel(audit_output_path, index=False)
        
        print(f"✅ CountsFor data saved to {counts_for_output_path}")
        print(f"✅ Requirement data saved to {requirement_output_path}")
        print(f"✅ Audit data saved to {audit_output_path}")


if __name__ == "__main__":
    process_all_audits()
