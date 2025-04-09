# pylint: disable=all
"""
This script extracts the courses and requirements from the audit JSON files.
It is the exact same code from the course-data-analysis repo.
"""
import sys
import os
from pathlib import Path

# Add parent directory to path to make imports work from any directory
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

# Try to import utils in two ways - either as a module within backend or directly
try:
    import backend.scripts.utils as utils
except ModuleNotFoundError:
    import scripts.utils as utils

import json
import pandas as pd
pd.set_option('display.max_colwidth', None)

def getCoursesFromRange(begin, end, inc_exc, req_chain):
    courses = []
    if begin[:2] != end[:2] or begin[:2] == 'XX':
        # print("[Warning] Not including course range:", begin, end)
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
        # get courses - handle both old and new format
        courses = []
        if 'courses' in constraint['data']:
            courses = constraint['data']['courses']
        elif 'conditional_course_sets' in constraint['data']:
            # New format - courses are in conditional_course_sets array
            for course_set in constraint['data']['conditional_course_sets']:
                if 'courses' in course_set:
                    courses.extend(course_set['courses'])

        # get code ranges
        ranges = []
        if 'code_ranges' in constraint['data']:
            ranges = constraint['data']['code_ranges']
        elif 'conditional_course_sets' in constraint['data']:
            # New format - code_ranges are in conditional_course_sets array
            for course_set in constraint['data']['conditional_course_sets']:
                if 'code_ranges' in course_set:
                    ranges.extend(course_set['code_ranges'])

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
        additional_courses = []
        if 'additional_courses' in constraint['data']:
            additional_courses = constraint['data']['additional_courses']

        return [(d['code'], req_chain, 'Inclusion', 'Code') for d in depts] + [(c, req_chain, 'Inclusion', 'Course') for c in additional_courses]

    elif t == 'notcountcourseset':
        # get exclusions - handle both old and new format
        courses = []
        if 'courses' in constraint['data']:
            courses = constraint['data']['courses']
        elif 'conditional_course_sets' in constraint['data']:
            # New format - courses are in conditional_course_sets array
            for course_set in constraint['data']['conditional_course_sets']:
                if 'courses' in course_set:
                    courses.extend(course_set['courses'])

        # To do: take into account code_ranges and code_patterns
        return [(c, req_chain, 'Exclusion', 'Course') for c in courses]

    else:
        # print("[Warning] Not accounting for constraint:", t)
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

def main():
    # Get the project root directory
    project_root = Path(__file__).resolve().parent.parent.parent

    # Path to the audits-json directory
    base_dir = project_root / "data" / "audit" / "audits-json"

    print(f"Looking for audit files in: {base_dir}")

    # Dictionary to store all dataframes
    all_dataframes = {}

    # Only process specific folders
    target_folders = ['ba', 'bio', 'cs', 'is']

    for folder in target_folders:
        folder_path = base_dir / folder

        # Skip if folder doesn't exist
        if not folder_path.is_dir():
            print(f"Folder {folder} not found, skipping...")
            continue

        # Process each JSON file in the folder
        for json_file in os.listdir(folder_path):
            if not json_file.endswith('.json'):
                continue

            file_path = folder_path / json_file

            # Determine if this is a core or gened file
            file_type = "gened" if json_file == "published.json" else "core"

            # Create dataframe name
            df_name = f"{folder}_{file_type}"

            # Process the audit file
            audit_data = getAudit(str(file_path))
            dataframe = makeDataFrame(audit_data)

            # Store the dataframe
            all_dataframes[df_name] = dataframe
            print(f"Created dataframe: {df_name} with {len(dataframe)} rows")

    return all_dataframes

if __name__ == "__main__":
    dataframes = main()
    # Example: Access specific dataframe
    # print(dataframes["is_core"].head())
