import os
import json
import pandas as pd
import utils
import json
import pandas as pd
pd.set_option('display.max_colwidth', None)

# paths
# Define base directories
AUDIT_DIR = "data/audit"
COURSE_DIR = "data/course"  # Folder containing individual course JSON files 

def get_audit_files(folder_path):
    """
    Get the two JSON files in the given folder and determine which is core and which is gen-ed.
    Returns a dictionary with the core and gen-ed file paths.
    """
    json_files = [f for f in os.listdir(folder_path) if f.endswith(".json")]
    if len(json_files) != 2:
        print(f"[Warning] Expected 2 JSON files in {folder_path}, found {len(json_files)}")
        return None

    # Get full file paths with sizes
    file_sizes = {f: os.path.getsize(os.path.join(folder_path, f)) for f in json_files}

    # Sort files by size (largest = core, smallest = gen-ed)
    sorted_files = sorted(file_sizes.items(), key=lambda x: x[1], reverse=True)
    
    return {
        "core": os.path.join(folder_path, sorted_files[0][0]),
        "gened": os.path.join(folder_path, sorted_files[1][0])
    }

def getCoursesFromRange(begin, end, inc_exc, req_chain):
    courses = []
    if begin[:2] != end[:2] or begin[:2] == 'XX':
        print("[Warning] Not including course range:", begin, end)
        return []
    else:
        code = begin[:2]
        begin = int(begin[3:])
        end = int(end[3:])
        # If all are included, use the code instead of individual courses
        if begin == 1 and end == 999:
            courses = [(code, req_chain, inc_exc, 'Code')]
        else:
            for n in range(begin, end+1):
                course_num = code + "-" + str(n).zfill(3)
                courses.append((course_num, req_chain, inc_exc, 'Course'))
            
    return courses

def getCoursesFromConstraint(constraint, req_chain):
    t = constraint['type']
    
    if t == 'xfromcourseset':
        # get courses
        courses = constraint['data']['courses']
        # get code ranges
        ranges = constraint['data']['code_ranges']
        courses_from_range = []
        for range in ranges:
            begin = range[0]
            end = range[1]
            courses_from_range.extend(getCoursesFromRange(begin, end, 'Inclusion', req_chain))
                    
        return [(c, req_chain, 'Inclusion', 'Course') for c in courses] + courses_from_range
    
    elif t == 'xfromdepts':
        # get codes
        depts = constraint['data']['depts']
        # get courses
        courses = constraint['data']['additional_courses']

        return [(d['code'], req_chain, 'Inclusion', 'Code') for d in depts] + [(c, req_chain, 'Inclusion', 'Course') for c in courses]
    
    elif t == 'notcountcourseset':
        # get exclusions
        courses = constraint['data']['courses']
        # To do: take into account code_ranges and code_patterns
        return [(c, req_chain, 'Exclusion', 'Course') for c in courses]
    
    else:
        print("[Warning] Not accounting for constraint:", t)
        return []

def getCourses(data, req_chain):
    if 'choices' in data:
        choices = data['choices']
        req = data['screen_name']
        req = "GenEd" if "General Education" in req else req # This is a hack for the audit comparison below
        new_req_chain = req if req_chain == '' else req_chain + '---' + req
        if len(choices) > 0:
            courses = []
            for c in choices:
                courses.extend(getCourses(c, new_req_chain))
            return courses
        # Courses in the form of constraints
        else:
            constraints = data['constraints']
            courses = []
            for c in constraints:
                courses.extend(getCoursesFromConstraint(c, new_req_chain))
            return courses
    else:
        course_num = data['screen_name']
        return [(course_num, req_chain, 'Inclusion', 'Course')]
        
def getAudit(json_path):
    """
    Extracts the relevant fields from the json file,
    returning a list of courses and the requirement they satisfy.

    A course may be repeated if it satisfies multiple requirements.
    """
    file = open(json_path)
    data = json.load(file)
    major = data['requirement']
    req_major = getCourses(major, '')

    req_programs = []
    if data['uni_req_tree']:
        programs = data['uni_req_tree']['programs'] 
        for p in programs:
            # Excluding degree check and total units requirements because basically all courses count for it, so it is not helpful
            if "Degree Check" not in p['screen_name'] and "Total Units" not in p['screen_name']:
                req_programs.extend(getCourses(p, ''))

    return req_major + req_programs

def makeDataFrame(audit):
    df = pd.DataFrame(audit)

    # Names columns
    df.columns = ['Course or code', 'Requirement', 'Inclusion/Exclusion', 'Type'] # Names columns
    # Adds more information about each couse
    df["Pre-reqs"] = df.apply(lambda row : utils.getPreReqs(row["Course or code"]), axis=1)
    df["Title"] = df.apply(lambda row : utils.getCourseTitle(row["Course or code"]), axis=1)
    df["Units"] = df.apply(lambda row : utils.getCourseUnits(row["Course or code"]), axis=1)
    # Reordering columns
    df = df[["Type", "Inclusion/Exclusion", "Course or code", "Title", "Units", "Pre-reqs", "Requirement"]]
    
    return df

def mergeAudits(major, gened):
    audit_major = makeDataFrame(getAudit(major))
    audit_gened = makeDataFrame(getAudit(gened))

    # To avoid type mismatch when merging
    audit_major = audit_major.astype(object)
    audit_gened = audit_gened.astype(object)

    all = pd.merge(audit_major, audit_gened, how='outer')
    return all



def get_course_codes():
    """
    Retrieves all course codes from the COURSE_DIR based on filenames.
    Assumes course files are named like '02-201.json'.
    """
    course_codes = set()
    for file in os.listdir(COURSE_DIR):
        if file.endswith(".json"):
            course_codes.add(file.replace(".json", ""))  # Extract course code from filename
    return course_codes

def get_courses_from_code(dept_code, course_codes):
    """
    Finds all courses that start with the given department code.
    Example: If dept_code='02', it returns all courses like '02-201', '02-202'.
    """
    return [c for c in course_codes if c.startswith(dept_code)]


def extract_min_units(data, parent_chain=""):
    """
    Recursively extracts hierarchical requirement names and min_units.
    Stops at the level before individual courses.
    """
    extracted_units = {}

    # Get current requirement name
    req_name = data.get("screen_name", "Unknown Requirement")
    full_chain = f"{parent_chain} - {req_name}" if parent_chain else req_name

    # Extract the min_units if it exists
    min_units = data.get("min_units", 0)
    extracted_units[full_chain] = min_units  # Store this requirement's min_units

    # Check if there are further sub-requirements
    if "choices" in data and isinstance(data["choices"], list):
        for sub_req in data["choices"]:
            extracted_units.update(extract_min_units(sub_req, full_chain))  # Recursively extract

    return extracted_units



def extract_audit_data(json_path, course_codes):
    """
    Extracts course and requirement details from an audit JSON file.
    """
    with open(json_path, "r") as file:
        data = json.load(file)

    # Extract requirements and courses
    audit_data = getAudit(json_path)  # Uses the original getAudit function
    df = makeDataFrame(audit_data)  # Uses the provided makeDataFrame function

    # Extract minimum units for each requirement
    # min_units_dict = extract_min_units(data)

    cleaned_data = []
    for _, row in df.iterrows():
        course_code = row["Course or code"]
        requirement = row["Requirement"]
        inclusion_exclusion = row["Inclusion/Exclusion"]
        type_ = row["Type"]

        # Get min_units for this requirement (fallback to 0 if missing)
        # requirement_min_units = min_units_dict.get(requirement, 0)

        # Only include rows where Inclusion/Exclusion is "Inclusion"
        if inclusion_exclusion == "Inclusion":
            if type_ == "Code":
                # If the type is "Code", find all matching courses
                matching_courses = get_courses_from_code(course_code, course_codes)
                for match in matching_courses:
                    cleaned_data.append({
                        "requirement": requirement,
                        # "requirement_min_units": requirement_min_units,
                        "course": match,
                    })
            else:
                # Directly store course-based rows
                cleaned_data.append({
                    "requirement": requirement,
                    # "requirement_min_units": requirement_min_units,
                    "course": course_code,
                })

    return cleaned_data


def save_to_excel(data, output_path):
    """
    Saves extracted and cleaned data to an Excel file.
    """
    df = pd.DataFrame(data)
    df.to_excel(output_path, index=False)
    print(f"✅ Data saved to {output_path}")

def process_all_audits():
    """
    Processes all audit JSON files in each major folder and saves them as Excel files.
    """
    course_codes = get_course_codes()  # Get all available course codes from COURSE_DIR

    for major in os.listdir(AUDIT_DIR):
        major_path = os.path.join(AUDIT_DIR, major)
        
        if not os.path.isdir(major_path):
            continue  # Skip non-folder entries

        audit_files = get_audit_files(major_path)
        if not audit_files:
            continue

        # Extract and save core requirements
        core_data = extract_audit_data(audit_files["core"], course_codes)
        core_output_path = os.path.join(major_path, f"{major}_core.xlsx")
        save_to_excel(core_data, core_output_path)

        # Extract and save general education requirements
        gened_data = extract_audit_data(audit_files["gened"], course_codes)
        gened_output_path = os.path.join(major_path, f"{major}_gened.xlsx")
        save_to_excel(gened_data, gened_output_path)

if __name__ == "__main__":
    process_all_audits()
