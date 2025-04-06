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
from backend.database.db import SessionLocal
from backend.database.models import Course
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
    def __init__(self, audit_base_path, course_base_path):
        """
        Initializes the extractor with the paths to the audit files,
        course JSON files, and the course table Excel file.
        """
        super().__init__()
        self.audit_base_path = audit_base_path
        self.course_base_path = course_base_path

    def get_audit_files(self, folder_path):
        """
        Returns a dictionary with paths for audit JSON files in a folder or its subfolders.
        More flexible implementation that doesn't require specific folder structure.
        """
        json_files = []

        # Walk through the directory tree to find all JSON files
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.endswith(".json") and not file.startswith("."):
                    json_files.append(os.path.join(root, file))

        if not json_files:
            logging.warning("No JSON files found in %s or its subdirectories", folder_path)
            return None

        # If only one JSON file found, use it for both core and gened
        if len(json_files) == 1:
            logging.info("Only one JSON file found in %s, using it for both core and gened", folder_path)
            return {
                "core": json_files[0],
                "gened": json_files[0]
            }

        # Check for core vs. gened words in filenames
        core_candidates = []
        gened_candidates = []

        for f in json_files:
            filename = os.path.basename(f).lower()
            if 'gened' in filename or 'general' in filename or 'gen_ed' in filename or 'gen-ed' in filename:
                gened_candidates.append(f)
            elif 'core' in filename or 'major' in filename or 'program' in filename:
                core_candidates.append(f)

        # If we have clear core and gened candidates
        if core_candidates and gened_candidates:
            return {
                "core": core_candidates[0],
                "gened": gened_candidates[0]
            }

        # Try to determine by looking at content (approximate)
        try:
            file_sizes = {f: os.path.getsize(f) for f in json_files}
            sorted_files = sorted(file_sizes.items(), key=lambda x: x[1], reverse=True)

            # Larger file is usually the major/core file
            if len(sorted_files) >= 2:
                # Attempt to open and check content
                core_file = sorted_files[0][0]
                gened_file = sorted_files[1][0]

                # Verify by content - look for General Education in the smaller file
                try:
                    with open(gened_file, 'r') as f:
                        content = f.read().lower()
                        if 'general education' in content or 'gened' in content:
                            # Correctly identified
                            pass
                        else:
                            # Reverse if not found - the larger file might be gened
                            with open(core_file, 'r') as f2:
                                content2 = f2.read().lower()
                                if 'general education' in content2 or 'gened' in content2:
                                    core_file, gened_file = gened_file, core_file
                except:
                    # If we can't read the file, just go with size heuristic
                    pass

                return {
                    "core": core_file,
                    "gened": gened_file
                }
            else:
                # Fallback to using the same file for both
                return {
                    "core": sorted_files[0][0],
                    "gened": sorted_files[0][0]
                }
        except OSError as error:
            logging.error("Failed to determine file sizes in %s: %s", folder_path, error)
            return None

    def get_course_codes(self):
        """
        Retrieves all course codes directly from the database.
        """
        codes = set()
        session = SessionLocal()
        try:
            result = session.query(Course.course_code).all()
            codes = {row[0] for row in result}
        except Exception as e:
            logging.error("Failed to retrieve course codes from database: %s", e)
            raise e
        finally:
            session.close()
        return codes


    def get_courses_from_range(self, begin, end, req_chain, parent_min_units=None):
        """
        Generates course identifiers from a given range.
        Returns tuples: (Course or code, Requirement, Inclusion/Exclusion, Type, Min Units)
        """
        courses = []
        try:
            # Special handling for wildcard ranges like XX-001 to XX-999
            if begin.startswith('XX-') or end.startswith('XX-'):
                logging.info("Processing wildcard range: %s to %s", begin, end)
                # This is a wildcard range that applies to any department code
                # We'll just add the range as a special type
                range_description = f"{begin} to {end}"
                courses.append((range_description, req_chain, 'Inclusion', 'Range',
                                 parent_min_units))
                return courses

            # Normal department-specific range
            if begin[:2] != end[:2]:
                logging.warning("Course range spans different departments: %s to %s", begin, end)
                return courses

            code = begin[:2]

            # If the range is the full range of a department (e.g., 03-001 to 03-999)
            if begin.endswith('-001') and end.endswith('-999'):
                # Add the entire department code
                courses.append((code, req_chain, 'Inclusion', 'Code', parent_min_units))
                return courses

            # Handle specific numeric ranges
            try:
                begin_num = int(begin[3:])
                end_num = int(end[3:])

                if end_num - begin_num > 100:
                    # If range is too large, just add the range as a description
                    range_description = f"{begin} to {end}"
                    courses.append((range_description, req_chain, 'Inclusion', 'Range',
                                     parent_min_units))
                else:
                    # Otherwise, enumerate each course in the range
                    for n in range(begin_num, end_num + 1):
                        course_num = f"{code}-{str(n).zfill(3)}"
                        courses.append((course_num, req_chain, 'Inclusion', 'Course',
                                         parent_min_units))
            except ValueError:
                logging.error("Invalid course numbers in range: %s to %s", begin, end)

        except (ValueError, IndexError) as error:
            logging.error("Invalid course range format: %s to %s, error: %s", begin, end, error)

        return courses

    def get_courses_from_constraint(self, constraint, req_chain,
                                    course_codes, parent_min_units=None):
        """
        Extracts courses (or codes) from a constraint.
        Returns tuples: (Course or code, Requirement, Inclusion/Exclusion, Type, Min Units)
        """
        course_codes = self.get_course_codes()
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
                # Process course sets that define ranges of courses
                course_sets = constraint_data.get("conditional_course_sets", [])
                for cs in course_sets:
                    # Process explicit courses list
                    if "courses" in cs and cs["courses"]:
                        for course in cs["courses"]:
                            extracted_course = (course, req_chain, "Inclusion", "Course", min_units)
                            courses.append(extracted_course)

                    # Process code ranges (like 03-001 to 03-999)
                    if "code_ranges" in cs and cs["code_ranges"]:
                        for range_pair in cs["code_ranges"]:
                            if len(range_pair) == 2:
                                begin, end = range_pair
                                range_courses = self.get_courses_from_range(begin, end,
                                                                          req_chain, min_units)
                                courses.extend(range_courses)

                    # Process code patterns (like 70-***)
                    if "code_patterns" in cs and cs["code_patterns"]:
                        for pattern in cs["code_patterns"]:
                            # Convert pattern to regex
                            pattern_regex = pattern.replace("*", ".")
                            for code in course_codes:
                                if re.match(pattern_regex, code):
                                    extracted_course = (code, req_chain, "Inclusion", "Course",
                                                        min_units)
                                    courses.append(extracted_course)

            elif constraint_type == "notcountcourseset":
                # Process exclusion courses - we'll add them with "Exclusion" type
                if "courses" in constraint_data and constraint_data["courses"]:
                    for course in constraint_data["courses"]:
                        extracted_course = (course, req_chain, "Exclusion", "Course", min_units)
                        courses.append(extracted_course)

                # Process excluded patterns
                if "code_patterns" in constraint_data and constraint_data["code_patterns"]:
                    for pattern in constraint_data["code_patterns"]:
                        pattern_regex = pattern.replace("*", ".")
                        # For patterns, we'll just add the pattern itself with a special type
                        extracted_pattern = (pattern, req_chain, "Exclusion", "Pattern", min_units)
                        courses.append(extracted_pattern)

            elif constraint_type in ["anyxof", "minxunits", "xwithgrades", "dc"]:
                # These constraint types don't directly specify courses, they're rules for counting
                # We'll add them as special entries for completeness
                constraint_text = constraint.get("type_string", "")
                if constraint_text:
                    extracted_rule = (constraint_text, req_chain, "Rule", constraint_type,
                                      min_units)
                    courses.append(extracted_rule)

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
            # req = "GenEd" if "General Education" in req else req
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
            # Get requirements from the main requirement tree
            req_major = self.get_courses(data['requirement'], '', course_codes)
            req_programs = []

            # Check if this is the BA GenEd format (published.json)
            if (data.get('program', {}).get('name', '').startswith("EY") and
                "Business Administration" in data.get('program', {}).get('name', '')
                and "Core Requirements" in data.get('program', {}).get('name', '')):
                # This is the BA GenEd format - handle main requirements
                logging.info("Processing BA GenEd format for file: %s", json_path)
                main_req_name = data.get('program', {}).get('name', '')

                for choice in data['requirement'].get('choices', []):
                    req_name = f"{main_req_name}---{choice.get('screen_name', '')}"
                    for constraint in choice.get('constraints', []):
                        courses = self.get_courses_from_constraint(constraint, req_name,
                                                                   course_codes)
                        req_programs.extend(courses)

                    for subchoice in choice.get('choices', []):
                        sub_req_name = f"{req_name}---{subchoice.get('screen_name', '')}"
                        for constraint in subchoice.get('constraints', []):
                            courses = self.get_courses_from_constraint(constraint,
                                                                       sub_req_name,
                                                                       course_codes)
                            req_programs.extend(courses)

                        for course_item in subchoice.get('choices', []):
                            screen_name = course_item.get('screen_name', '')
                            course_req_name = f"{sub_req_name}---{screen_name}"
                            for constraint in course_item.get('constraints', []):
                                courses = self.get_courses_from_constraint(constraint,
                                                                           course_req_name,
                                                                           course_codes)
                                req_programs.extend(courses)

            elif data.get('uni_req_tree'):
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
        Removes any course codes from the end of the requirement string.
        """
        # Remove any trailing course code (format: XX-XXX) from the requirement
        req = re.sub(r'\s*→\s*\d{2}-\d{3}\s*$', '', req)
        req = re.sub(r'\s*->\s*\d{2}-\d{3}\s*$', '', req)
        req = re.sub(r'\s*--\s*\d{2}-\d{3}\s*$', '', req)
        req = re.sub(r'\s*\d{2}-\d{3}\s*$', '', req)

        # Remove any other trailing arrow indicators
        req = re.sub(r'\s*→\s*$', '', req)
        req = re.sub(r'\s*->\s*$', '', req)

        # Remove any trailing dashes or hyphens
        req = re.sub(r'\s*[-–—]\s*$', '', req)

        # Trim any trailing whitespace, dashes, or separators
        req = req.rstrip(' -–—→\t\n')

        return req.strip()

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
            course_codes = self.get_course_codes()
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
                df_audit = pd.DataFrame(combined_data)[["audit",
                                                        "audit_type", "major"]].drop_duplicates()
                df_audit["audit_id"] = df_audit["major"] + "_" + df_audit["audit_type"].astype(str)
                df_audit = df_audit.rename(columns={"audit": "name", "audit_type": "type"})

                # ✅ Get course codes from DB instead of Excel
                session = SessionLocal()
                try:
                    existing_courses = set(row[0] for row in
                                        session.query(Course.course_code).all())
                finally:
                    session.close()

                df_countsfor = pd.DataFrame(combined_data)[["requirement", "course"]]
                df_countsfor = df_countsfor.rename(columns={"course":
                                                            "course_code"}).drop_duplicates()
                df_countsfor = df_countsfor[df_countsfor["course_code"].isin(existing_courses)]

                df_requirement = pd.DataFrame(combined_data)[
                    ["requirement", "major", "audit_type"]
                ].drop_duplicates()
                df_requirement = df_requirement.rename(columns={"audit_type": "type"})
                df_requirement = df_requirement.merge(
                    df_audit[["audit_id", "major", "type"]],
                    on=["major", "type"], how="left"
                )
                df_requirement = df_requirement[["requirement", "audit_id"]]

                # No longer save Excel files — just return the data
                return {
                    "audit": df_audit.to_dict(orient="records"),
                    "requirement": df_requirement.to_dict(orient="records"),
                    "countsfor": df_countsfor.to_dict(orient="records")
                }
        except (OSError, KeyError, ValueError) as error:
            logging.error("Error occurred during audit processing: %s", error)
            return None

    def get_results(self) -> dict[str, list[dict]]:
        """
        Extracts audit data from JSON files and returns a dictionary of results.
        More flexible implementation that doesn't require specific subfolder structure.
        Only processes the four main majors: BA, CS, IS, and BIO.
        """
        course_codes = self.get_course_codes()
        combined_data = []
        processed_dirs = set()
        processed_files = 0

        # Define the allowed majors (only these will be processed)
        ALLOWED_MAJORS = {'ba', 'cs', 'is', 'bio'}

        # Define specific requirements to exclude for IS major
        IS_EXCLUDED_REQUIREMENTS = {
            "BS in Information Systems",
            "Qatar Information Systems - General Education - 2024+",
            "Qatar Information Systems - General Education - 2024+---General Education"
        }

        # First pass: collect all JSON files in the directory tree
        all_json_files = []
        for root, _, files in os.walk(self.audit_base_path):
            for file in files:
                if file.endswith('.json') and not file.startswith('.'):
                    json_path = os.path.join(root, file)
                    parent_dir = os.path.basename(os.path.dirname(json_path))

                    # Normalize parent_dir name to lowercase for comparison
                    normalized_dir = parent_dir.lower()

                    # Only include files from allowed major directories
                    if normalized_dir in ALLOWED_MAJORS:
                        all_json_files.append((parent_dir, json_path))
                    else:
                        logging.info("Skipping non-main major directory: %s", parent_dir)

        # If no JSON files found, return empty results
        if not all_json_files:
            logging.warning("No JSON files found for main majors in audit directory: %s", self.audit_base_path)
            return {
                "audit": [],
                "requirement": [],
                "countsfor": []
            }

        # Process files by parent directory to group related files
        for parent_dir, files_in_dir in self._group_files_by_parent_dir(all_json_files):
            # Skip already processed directories
            if parent_dir in processed_dirs:
                continue

            processed_dirs.add(parent_dir)

            # Use parent directory name as major name
            major = parent_dir

            logging.info("Processing audit data for major: %s", major)

            try:
                # Get core and gened files for this directory
                audit_files = self.get_audit_files(os.path.dirname(files_in_dir[0]))

                if not audit_files:
                    continue

                # Extract core data with type 0 (core/major requirements)
                core_data = self.extract_audit_data(audit_files["core"], course_codes)
                for d in core_data:
                    # Skip excluded requirements for IS major
                    if major.lower() == 'is' and d["requirement"] in IS_EXCLUDED_REQUIREMENTS:
                        logging.info(f"Skipping excluded IS requirement: {d['requirement']}")
                        continue

                    d.update({
                        "audit_type": 0,  # 0 = core/major requirements
                        "major": major,
                        "audit": d["requirement"].split('---')[0].strip()
                    })
                    combined_data.append(d)

                # Extract gened data with type 1 (gened requirements)
                gened_data = self.extract_audit_data(audit_files["gened"], course_codes)
                for d in gened_data:
                    # Skip excluded requirements for IS major
                    if major.lower() == 'is' and d["requirement"] in IS_EXCLUDED_REQUIREMENTS:
                        logging.info(f"Skipping excluded IS requirement: {d['requirement']}")
                        continue

                    d.update({
                        "audit_type": 1,  # 1 = gened requirements
                        "major": major,
                        "audit": d["requirement"].split('---')[0].strip()
                    })
                    combined_data.append(d)

                processed_files += 2

            except Exception as e:
                logging.error("Error processing files in %s: %s", parent_dir, e)
                # Fall back to the old approach for this directory
                if len(files_in_dir) == 1:
                    # If only one file, use it for both core and gened
                    json_path = files_in_dir[0]
                    audit_data = self.extract_audit_data(json_path, course_codes)

                    # Add as core data
                    for d in audit_data:
                        # Skip excluded requirements for IS major
                        if major.lower() == 'is' and d["requirement"] in IS_EXCLUDED_REQUIREMENTS:
                            logging.info(f"Skipping excluded IS requirement: {d['requirement']}")
                            continue

                        d.update({
                            "audit_type": 0,
                            "major": major,
                            "audit": d["requirement"].split('---')[0].strip()
                        })
                        combined_data.append(d)

                    # Also add as gened data
                    for d in audit_data:
                        # Skip excluded requirements for IS major
                        if major.lower() == 'is' and d["requirement"] in IS_EXCLUDED_REQUIREMENTS:
                            logging.info(f"Skipping excluded IS requirement: {d['requirement']}")
                            continue

                        d.update({
                            "audit_type": 1,
                            "major": major,
                            "audit": d["requirement"].split('---')[0].strip()
                        })
                        combined_data.append(d)

                    processed_files += 1
                elif len(files_in_dir) >= 2:
                    # With multiple files, determine largest (core) and second largest (gened)
                    file_sizes = {f: os.path.getsize(f) for f in files_in_dir}
                    sorted_files = sorted(file_sizes.items(), key=lambda x: x[1], reverse=True)

                    core_file = sorted_files[0][0]
                    gened_file = sorted_files[1][0]

                    # Extract core data
                    core_data = self.extract_audit_data(core_file, course_codes)
                    for d in core_data:
                        # Skip excluded requirements for IS major
                        if major.lower() == 'is' and d["requirement"] in IS_EXCLUDED_REQUIREMENTS:
                            logging.info(f"Skipping excluded IS requirement: {d['requirement']}")
                            continue

                        d.update({
                            "audit_type": 0,
                            "major": major,
                            "audit": d["requirement"].split('---')[0].strip()
                        })
                        combined_data.append(d)

                    # Extract gened data
                    gened_data = self.extract_audit_data(gened_file, course_codes)
                    for d in gened_data:
                        # Skip excluded requirements for IS major
                        if major.lower() == 'is' and d["requirement"] in IS_EXCLUDED_REQUIREMENTS:
                            logging.info(f"Skipping excluded IS requirement: {d['requirement']}")
                            continue

                        d.update({
                            "audit_type": 1,
                            "major": major,
                            "audit": d["requirement"].split('---')[0].strip()
                        })
                        combined_data.append(d)

                    processed_files += 2

        # When creating the audit DataFrame, also filter out requirements at this level
        logging.info("Processed %d audit JSON files from %d directories",
                    processed_files, len(processed_dirs))

        # Ensure the DataFrame is created with the correct columns
        if combined_data:
            # Add additional filtering for combined data to make sure we exclude the specified requirements
            combined_data = [d for d in combined_data if not (d["major"].lower() == "is" and
                                                              d["requirement"] in IS_EXCLUDED_REQUIREMENTS)]

            # Create audit table data (filter to only include valid columns)
            audit_df = pd.DataFrame(combined_data)
            if not all(col in audit_df.columns for col in ["audit", "audit_type", "major"]):
                logging.error("Expected columns are missing in the combined data.")
                raise ValueError("Missing expected columns in the audit data.")

            audit_df["audit_id"] = audit_df["major"] + "_" + audit_df["audit_type"].astype(str)
            audit_df = audit_df[["audit_id", "major", "audit", "audit_type"]]
            audit_df = audit_df.rename(columns={"audit": "name", "audit_type": "type"})
            audit_df = audit_df.drop_duplicates()

            # Create countsfor table data
            counts_df = pd.DataFrame(combined_data)[["requirement", "course"]]
            counts_df = counts_df.rename(columns={"course": "course_code"}).drop_duplicates()

            # Create requirement table data
            req_df = pd.DataFrame(combined_data)[["requirement", "major", "audit_type"]].drop_duplicates()
            req_df = req_df.rename(columns={"audit_type": "type"})
            req_df = req_df.merge(
                audit_df[["audit_id", "major", "type"]],
                on=["major", "type"],
                how="left"
            )
            req_df = req_df[["requirement", "audit_id"]]

            dupes = req_df[req_df.duplicated(subset=["requirement"], keep=False)]
            if not dupes.empty:
                logging.warning("Duplicate requirements across audits found")

            return {
                "audit": audit_df.to_dict(orient="records"),
                "requirement": req_df.to_dict(orient="records"),
                "countsfor": counts_df.to_dict(orient="records")
            }
        else:
            logging.warning("No combined data found for audits.")
            return {
                "audit": [],
                "requirement": [],
                "countsfor": []
            }

    def _group_files_by_parent_dir(self, files):
        """
        Group files by their parent directory.
        Returns a list of tuples (parent_dir, [file_paths]).
        """
        result = {}
        for parent_dir, file_path in files:
            if parent_dir not in result:
                result[parent_dir] = []
            result[parent_dir].append(file_path)
        return result.items()
