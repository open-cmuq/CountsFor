"""
audit_extractor.py

This module defines the AuditDataExtractor class that extracts course and
requirement details from audit JSON files and outputs Excel files for the database tables.
It inherits common functionality from DataExtractor.
"""

import os
import re
import json
import logging
import pandas as pd
import backend.scripts.utils as utils

# Import the common base class.
from backend.scripts.data_extractor import DataExtractor

# Ensure pandas displays full column width
pd.set_option('display.max_colwidth', None)
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


class AuditDataExtractor(DataExtractor):
    """
    Extracts course and requirement details from audit JSON files.
    """
    def __init__(self, audit_base_path, course_base_path, course_table_path):
        """
        Initializes the extractor with the paths to the audit files,
        course JSON files, and the course table Excel file.
        """
        super().__init__()
        self.audit_base_path = audit_base_path
        self.course_base_path = course_base_path
        self.course_table_path = course_table_path

    def get_audit_files(self, folder_path):
        """
        Returns a dictionary with paths for the two audit JSON files in a folder,
        determining which file is core and which is general education.
        """
        try:
            json_files = [f for f in os.listdir(folder_path) if f.endswith(".json")]
            if len(json_files) != 2:
                logging.warning("Expected 2 JSON files in %s, found %d", folder_path,
                                len(json_files))
                return None
        except OSError as error:
            logging.error("Failed to list files in %s: %s", folder_path, error)
            return None

        core_file, gened_file = None, None
        try:
            for f in json_files:
                if re.search(r"(19|20)\d{2}", f):
                    core_file = f
                else:
                    gened_file = f
            if not core_file or not gened_file:
                file_sizes = {f: os.path.getsize(os.path.join(folder_path, f)) for f in json_files}
                sorted_files = sorted(file_sizes.items(), key=lambda x: x[1], reverse=True)
                core_file, gened_file = sorted_files[0][0], sorted_files[1][0]
        except OSError as error:
            logging.error("Failed to determine file sizes in %s: %s", folder_path, error)
            return None

        return {
            "core": os.path.join(folder_path, core_file),
            "gened": os.path.join(folder_path, gened_file)
        }

    def get_course_codes(self, course_dir):
        """
        Retrieves all course codes from the given course directory.
        Assumes course files are named like '02-201.json'.
        """
        codes = set()
        try:
            for filename in os.listdir(course_dir):
                if filename.endswith(".json"):
                    file_path = os.path.join(course_dir, filename)
                    try:
                        with open(file_path, "r", encoding="utf-8") as file:
                            data = json.load(file)
                        if not data.get("success", True):
                            continue
                        codes.add(filename.replace(".json", ""))
                    except (OSError, json.JSONDecodeError) as error:
                        logging.warning("Skipping %s due to error: %s", filename, error)
        except OSError as error:
            logging.error("Failed to list files in %s: %s", course_dir, error)
        return codes

    def get_courses_from_range(self, begin, end, req_chain, parent_min_units=None):
        """
        Generates course identifiers from a given range.
        Returns tuples: (Course or code, Requirement, Inclusion/Exclusion, Type, Min Units)
        """
        courses = []
        try:
            if begin[:2] != end[:2] or begin[:2] == 'XX':
                logging.warning("Not including course range: %s to %s", begin, end)
                return courses

            code = begin[:2]
            begin_num = int(begin[3:])
            end_num = int(end[3:])

            if begin_num == 1 and end_num == 999:
                courses = [(code, req_chain, 'Inclusion', 'Code', parent_min_units)]
            else:
                for n in range(begin_num, end_num + 1):
                    course_num = f"{code}-{str(n).zfill(3)}"
                    courses.append((course_num, req_chain, 'Inclusion', 'Course', parent_min_units))
        except (ValueError, IndexError) as error:
            logging.error("Invalid course range format: %s to %s, error: %s", begin, end, error)
        return courses

    def get_courses_from_constraint(self, constraint, req_chain,
                                    course_codes, parent_min_units=None):
        """
        Extracts courses (or codes) from a constraint.
        Returns tuples: (Course or code, Requirement, Inclusion/Exclusion, Type, Min Units)
        """
        course_codes = self.get_course_codes(self.course_base_path)
        courses = []
        min_units = parent_min_units
        try:
            constraint_type = constraint.get("type", "")
            constraint_data = constraint.get("data", {})

            if constraint_type == "course":
                course_info = constraint_data.get("course", {})
                if course_info:
                    course_code = course_info.get("code", "Unknown Course")
                    units = course_info.get("units", min_units)
                    extracted_course = (course_code, req_chain, "Inclusion", "Course", units)
                    courses.append(extracted_course)
                else:
                    logging.error("Missing expected course information in constraint")
            elif constraint_type == "xfromcourseset":
                course_sets = constraint_data.get("conditional_course_sets", [])
                for cs in course_sets:
                    if "courses" in cs:
                        for course in cs["courses"]:
                            extracted_course = (course, req_chain, "Inclusion", "Course", min_units)
                            courses.append(extracted_course)
                    else:
                        logging.error("Missing expected key in constraint: 'courses'")
            elif constraint_type == "xfromdepts":
                depts = constraint_data.get("depts", [])
                for dept in depts:
                    dept_code = dept.get("code", "")
                    if dept_code:
                        possible_courses = [f"{dept_code}-{str(i).zfill(3)}" for i
                                            in range(1, 1000)]
                        valid_courses = [c for c in possible_courses if c in course_codes]
                        for course in valid_courses:
                            extracted_course = (course, req_chain, "Inclusion", "Course", min_units)
                            courses.append(extracted_course)
                    else:
                        logging.warning("Skipping department with missing code")
                code_ranges = constraint_data.get("code_ranges", [])
                for range_pair in code_ranges:
                    if len(range_pair) == 2:
                        begin, end = range_pair
                        range_courses = self.get_courses_from_range(begin, end,
                                                                    req_chain, min_units)
                        for course_tuple in range_courses:
                            course_code = course_tuple[0]
                            if course_code in course_codes:
                                courses.append(course_tuple)
                    else:
                        logging.error("Invalid code range format in constraint: %s", range_pair)
            elif constraint_type in ["anyxof", "minxunits", "notcountcourseset"]:
                logging.info("Skipping non-course constraint: %s", constraint_type)
            else:
                logging.warning("Unknown constraint type: %s", constraint_type)
        except (KeyError, ValueError, IndexError) as e:
            logging.error("Exception while processing constraint: %s", str(e))
        return courses

    def get_courses(self, data, req_chain, course_codes, parent_min_units=None):
        """
        Recursively extracts courses from audit data.
        Returns tuples: (Course or code, Requirement, Inclusion/Exclusion, Type, Min Units)
        """
        try:
            current_min_units = data.get("min_units", parent_min_units)
            req = data.get('screen_name', '')
            req = "GenEd" if "General Education" in req else req
            new_req_chain = req if not req_chain else f"{req_chain}---{req}"

            courses = []
            if 'choices' in data and data['choices']:
                for choice in data['choices']:
                    courses.extend(self.get_courses(choice, new_req_chain,
                                                    course_codes, current_min_units))

            for constraint in data.get('constraints', []):
                courses.extend(self.get_courses_from_constraint(constraint, new_req_chain,
                                                                course_codes, current_min_units))

            if not courses:
                courses = [(data.get('screen_name', 'Unknown'), req_chain, 'Inclusion',
                            'Course', current_min_units)]
            return courses
        except KeyError as error:
            logging.error("Missing expected key in audit data: %s", error)
            return []

    def get_courses_from_code(self, code, course_codes):
        """
        Given a department code, returns the list of full course codes from course_codes that
        start with that code.
        """
        return [c for c in course_codes if c.startswith(code)]

    def get_audit(self, json_path, course_codes):
        """
        Extracts relevant fields from the audit JSON file,
        returning a list of course tuples and the requirements they satisfy.
        """
        try:
            with open(json_path, "r", encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, json.JSONDecodeError) as error:
            logging.error("Failed to read or parse JSON file %s: %s", json_path, error)
            return []

        try:
            req_major = self.get_courses(data['requirement'], '', course_codes)
            req_programs = []
            if data.get('uni_req_tree'):
                for program in data['uni_req_tree'].get('programs', []):
                    if ("Degree Check" not in program['screen_name'] and
                        "Total Units" not in program['screen_name']):
                        req_programs.extend(self.get_courses(program, '', course_codes))
            return req_major + req_programs
        except KeyError as error:
            logging.error("Missing expected key in audit data: %s", error)
            return []

    def extract_audit_data(self, json_path, course_codes):
        """
        Extracts course and requirement details from an audit JSON file.
        Returns standardized dictionaries with keys: requirement, course, min_units.
        """
        try:
            audit_data = self.get_audit(json_path, course_codes)
            df = self.make_data_frame(audit_data)
            cleaned_data = []

            for _, row in df.iterrows():
                processed_req = self.post_process_requirement(row["Requirement"])
                if row["Inclusion/Exclusion"] == "Inclusion":
                    if row["Type"] == "Code":
                        for match in self.get_courses_from_code(row["Course or code"],
                                                                course_codes):
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
        except KeyError as error:
            logging.error("Missing expected key in audit data: %s", error)
            return []

    def post_process_requirement(self, req):
        """
        Cleans and standardizes the requirement string.
        This version replicates the original behavior by:
        1. Splitting the requirement on '---'
        2. Handling specific cases for Business Administration and Information Systems
        3. Always filtering out tokens that match a course code pattern or contain 'choose'/'select'
        """
        try:
            parts = req.split('---')
            number_words = {"one", "two", "three", "four", "five", "six",
                            "seven", "eight", "nine", "ten"}
            new_req = req

            # Case 1: BS in Business Administration with a "select" token in parts[1]
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
                    new_req = "---".join([part0, cleaned_part1, part2, part3,
                                          processed_part4, part5])
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

            # Case 2: BS in Information Systems---Concentration
            elif req.startswith("BS in Information Systems---Concentration") and len(parts) == 5:
                (part0, part1, part2, part4) = (parts[0].strip(), parts[1].strip(),
                parts[2].strip(), parts[4].strip())
                if part4.startswith(part2):
                    part4 = part4[len(part2):].strip()
                    part4 = part4[1:].strip() if part4.startswith('-') else part4
                new_req = "---".join([part0, part1, part2, part4])

            # Always apply final filtering (Case 3) to remove tokens that look like course codes
            # or contain 'choose'/'select'
            course_code_pattern = r'\b(?:\d{5}|\d{2}-\d{3}|[a-zA-Z]{2}-\d{3})\b'
            final_parts = []
            for part in new_req.split('---'):
                stripped = part.strip()
                if not (re.search(course_code_pattern, stripped) or
                        re.search(r'\bchoose\b', stripped, flags=re.IGNORECASE) or
                        re.search(r'\bselect\b', stripped, flags=re.IGNORECASE)):
                    final_parts.append(stripped)
            new_req = "---".join(final_parts)
            return new_req

        except (IndexError, AttributeError, TypeError) as error:
            logging.error("Error processing requirement string: %s", error)
            return req


    def make_data_frame(self, audit):
        """
        Converts the list of audit tuples into a standardized DataFrame.
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
            logging.error("Missing expected column in audit data: %s", error)
            return pd.DataFrame()

    def process_all_audits(self):
        """
        Processes all audit JSON files in subdirectories of audit_base_path.
        Outputs multiple Excel files and returns a dictionary of output file paths.
        """
        try:
            course_codes = self.get_course_codes(os.path.join(self.course_base_path, "courses"))
            combined_data = []

            for major in os.listdir(self.audit_base_path):
                major_path = os.path.join(self.audit_base_path, major)
                if not os.path.isdir(major_path):
                    continue

                audit_files = self.get_audit_files(major_path)
                if not audit_files:
                    continue

                logging.info("Processing audit files for major: %s", major)

                # Process and save core requirements
                core_data = self.extract_audit_data(audit_files["core"], course_codes)
                core_output_path = os.path.join(major_path, f"{major}_core.xlsx")
                self.save_to_excel(core_data, core_output_path)
                for d in core_data:
                    d.update({"audit_type": 0, "major": major,
                              "audit": d["requirement"].split('---')[0].strip()})
                    combined_data.append(d)

                # Process and save general education requirements
                gened_data = self.extract_audit_data(audit_files["gened"], course_codes)
                gened_output_path = os.path.join(major_path, f"{major}_gened.xlsx")
                self.save_to_excel(gened_data, gened_output_path)
                for d in gened_data:
                    d.update({"audit_type": 1, "major": major,
                              "audit": d["requirement"].split('---')[0].strip()})
                    combined_data.append(d)

            if combined_data:
                df_audit = pd.DataFrame(combined_data)[["audit", "audit_type",
                                                        "major"]].drop_duplicates()
                df_audit["audit_id"] = df_audit["major"] + "_" + df_audit["audit_type"].astype(str)
                df_audit = df_audit.rename(columns={"audit": "name", "audit_type": "type"})

                df_course = pd.read_excel(self.course_table_path)
                existing_courses = set(df_course["course_code"].astype(str))
                df_countsfor = pd.DataFrame(combined_data)[
                    ["requirement","course"]].rename(columns={"course": "course_code"})
                df_countsfor = df_countsfor[
                    df_countsfor["course_code"].isin(existing_courses)].drop_duplicates()

                df_requirement = pd.DataFrame(combined_data)[
                    ["requirement", "major", "audit_type"]].drop_duplicates()
                df_requirement = df_requirement.rename(columns={"audit_type": "type"})
                df_requirement = df_requirement.merge(df_audit[["audit_id", "major", "type"]],
                                                       on=["major", "type"], how="left")
                df_requirement = df_requirement[["requirement", "audit_id"]]

                counts_for_output_path = os.path.join(self.audit_base_path, "CountsFor.xlsx")
                requirement_output_path = os.path.join(self.audit_base_path, "Requirement.xlsx")
                audit_output_path = os.path.join(self.audit_base_path, "Audit.xlsx")

                self.save_to_excel(df_countsfor.to_dict(orient='records'), counts_for_output_path)
                self.save_to_excel(df_requirement.to_dict(orient='records'),
                                   requirement_output_path)
                self.save_to_excel(df_audit.to_dict(orient='records'), audit_output_path)

                logging.info("Audit data processing complete, files saved.")
                return {
                    "counts_for": counts_for_output_path,
                    "requirement": requirement_output_path,
                    "audit": audit_output_path
                }
        except (OSError, KeyError, ValueError) as error:
            logging.error("Error occurred during audit processing: %s", error)
            return None


if __name__ == "__main__":
    # Adjust these paths as needed for your environment.
    AUDIT_BASE = "data/audit"
    COURSE_BASE = "data/course/courses"
    COURSE_TABLE = "data/course/Course.xlsx"

    extractor = AuditDataExtractor(AUDIT_BASE, COURSE_BASE, COURSE_TABLE)
    extractor.process_all_audits()
