"""
audit_extractor.py

This module defines the AuditDataExtractor class that extracts course and
requirement details from audit JSON files and outputs Excel files for the database tables.
It inherits common functionality from DataExtractor.
"""

import re
import logging
import os
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple

import pandas as pd
from backend.database.db import SessionLocal
from backend.database.models import Course

# Import the common base class.
from backend.scripts.data_extractor import DataExtractor

# Ensure pandas displays full column width
pd.set_option('display.max_colwidth', None)
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


class AuditDataExtractor(DataExtractor):
    """
    Extracts course and requirement details from audit JSON files.
    Processes JSON files directly instead of relying on extract_audit_dataframes module.
    """
    def __init__(self, audit_base_path):
        """
        Initializes the extractor with the path to the audit files.
        """
        super().__init__()
        self.audit_base_path = Path(audit_base_path) # Use Path object

    # --- Integrated Helper Functions from extract_audit_dataframes.py ---

    @staticmethod
    def _getCoursesFromRange(begin, end, inc_exc, req_chain) -> List[Tuple[str, str, str, str]]:
        courses = []
        if begin[:2] != end[:2] or begin[:2] == 'XX':
            logging.warning("[Warning] Not including course range: %s %s", begin, end)
            return []
        else:
            code = begin[:2]
            try:
                begin_num = int(begin[3:])
                end_num = int(end[3:])
                # If all are included, use the code instead of individual courses
                if begin_num == 1 and end_num == 999:
                    courses = [(code, req_chain, inc_exc, 'Code')]
                else:
                    for n in range(begin_num, end_num+1):
                        course_num = f"{code}-{str(n).zfill(3)}"
                        courses.append((course_num, req_chain, inc_exc, 'Course'))
            except (ValueError, IndexError):
                 logging.warning("Invalid course range format: %s-%s", begin, end)
                 return []

        return courses

    @staticmethod
    def _getCoursesFromConstraint(constraint, req_chain) -> List[Tuple[str, str, str, str]]:
        t = constraint.get('type')
        data = constraint.get('data', {})

        if t == 'xfromcourseset':
            courses = []
            if 'courses' in data:
                courses = data['courses']
            elif 'conditional_course_sets' in data:
                for course_set in data['conditional_course_sets']:
                    if 'courses' in course_set:
                        courses.extend(course_set['courses'])

            ranges = []
            if 'code_ranges' in data:
                ranges = data['code_ranges']
            elif 'conditional_course_sets' in data:
                for course_set in data['conditional_course_sets']:
                    if 'code_ranges' in course_set:
                        ranges.extend(course_set['code_ranges'])

            courses_from_range = []
            for r in ranges:
                if len(r) == 2:
                     courses_from_range.extend(AuditDataExtractor._getCoursesFromRange(r[0], r[1], 'Inclusion', req_chain))

            return [(c, req_chain, 'Inclusion', 'Course') for c in courses] + courses_from_range

        elif t == 'xfromdepts':
            depts = data.get('depts', [])
            additional_courses = data.get('additional_courses', [])
            return [(d.get('code'), req_chain, 'Inclusion', 'Code') for d in depts if d.get('code')] + \
                   [(c, req_chain, 'Inclusion', 'Course') for c in additional_courses]

        elif t == 'notcountcourseset':
            courses = []
            if 'courses' in data:
                courses = data['courses']
            elif 'conditional_course_sets' in data:
                for course_set in data['conditional_course_sets']:
                    if 'courses' in course_set:
                        courses.extend(course_set['courses'])
            # TODO: take into account code_ranges and code_patterns for exclusions
            return [(c, req_chain, 'Exclusion', 'Course') for c in courses]

        else:
            logging.warning("Not accounting for constraint type: %s", t)
            return []

    @staticmethod
    def _getCourses(data, req_chain) -> List[Tuple[str, str, str, str]]:
        courses_list = []
        if isinstance(data, dict):
            req = data.get('screen_name', 'Unknown Requirement')
            req = "GenEd" if "General Education" in req else req # Hack for audit comparison
            new_req_chain = req if not req_chain else f"{req_chain}---{req}"

            if 'choices' in data:
                choices = data['choices']
                if choices: # Recursive case
                    for c in choices:
                        courses_list.extend(AuditDataExtractor._getCourses(c, new_req_chain))
                elif 'constraints' in data: # Constraints case
                    constraints = data['constraints']
                    for c in constraints:
                        courses_list.extend(AuditDataExtractor._getCoursesFromConstraint(c, new_req_chain))
                # else: Base case? Maybe a requirement with no choices/constraints?
            elif 'type' in data: # If it's a constraint itself at this level
                 courses_list.extend(AuditDataExtractor._getCoursesFromConstraint(data, new_req_chain))
            elif 'screen_name' in data: # Base case: a single course identified by screen_name
                 course_num = data['screen_name']
                 # Basic validation for course code format XX-XXX
                 if re.match(r"^\d{2}-\d{3}$", course_num):
                     courses_list.append((course_num, new_req_chain, 'Inclusion', 'Course'))
                 else:
                      logging.warning("Skipping non-course screen_name as course: %s", course_num)


        elif isinstance(data, list): # Handle lists of items (e.g., in uni_req_tree)
             for item in data:
                 courses_list.extend(AuditDataExtractor._getCourses(item, req_chain)) # Pass original req_chain

        return courses_list


    @staticmethod
    def _getAuditData(data: Dict[str, Any], source_name: str = "Unknown") -> List[Tuple[str, str, str, str]]:
        """
        Extracts the relevant fields from the loaded audit data dictionary.
        Returns a list of (course_or_code, requirement_chain, inclusion/exclusion, type).
        `source_name` is used for logging.
        """
        req_major_list = []
        if 'requirement' in data:
            major_req_data = data['requirement']
            req_major_list = AuditDataExtractor._getCourses(major_req_data, '')
        else:
            logging.warning("No top-level 'requirement' key found in audit data from %s", source_name)

        req_programs_list = []
        uni_req_tree = data.get('uni_req_tree')
        if uni_req_tree and isinstance(uni_req_tree, dict) and 'programs' in uni_req_tree:
            programs = uni_req_tree['programs']
            # Ensure programs is a list before iterating
            if isinstance(programs, list):
                for p in programs:
                    # Check if p is a dict and has screen_name before processing
                    if p and isinstance(p, dict):
                        screen_name = p.get('screen_name', '')
                        # Excluding degree check and total units requirements
                        if screen_name and "Degree Check" not in screen_name and \
                           "Total Units" not in screen_name:
                            req_programs_list.extend(AuditDataExtractor._getCourses(p, ''))
                        # else: logging.debug("Skipping program node (excluded type or missing name): %s", screen_name)
                    # else: logging.warning("Skipping invalid program item in audit data from %s: %s", source_name, p)
            # else: logging.warning("'programs' key does not contain a list in audit data from %s", source_name)
        # else: logging.debug("No 'uni_req_tree.programs' found in audit data from %s", source_name)

        # logging.info("Extracted %d major reqs and %d program reqs from %s",
        #             len(req_major_list), len(req_programs_list), source_name)
        return req_major_list + req_programs_list

    # --- End of Integrated Helper Functions ---

    def get_processed_audit_data(self) -> Dict[str, List[Tuple[str, str, str, str]]]:
        """
        Walks the audit directory structure, reads JSON files, extracts raw audit data.
        Returns a dictionary mapping an identifier (e.g., 'cs_core') to a list of tuples:
        (course_or_code, requirement_chain, inclusion/exclusion, type)
        """
        logging.info("Processing audit files in: %s", self.audit_base_path)
        processed_data = {}
        target_folders = {'ba', 'bio', 'cs', 'is'} # Use a set for efficiency

        if not self.audit_base_path.exists():
            logging.error("Audit base directory not found: %s", self.audit_base_path)
            return {}

        files_processed_count = 0
        scan_path = self.audit_base_path # Start scanning from the base path

        # Check for intermediate directory structure: data/audit/<intermediate>/<major>
        subdirs = [d for d in self.audit_base_path.iterdir() if d.is_dir()]
        if subdirs:
            # If subdirectories exist, assume the first one is the intermediate holder
            intermediate_dir = subdirs[0]
            logging.info("Found intermediate directory: %s. Scanning inside for major folders.", intermediate_dir.name)
            scan_path = intermediate_dir # Change scan path to the intermediate dir
            # Check if major folders exist inside the intermediate directory
            folders_to_scan = [d for d in scan_path.iterdir() if d.is_dir() and d.name in target_folders]
            if not folders_to_scan:
                 logging.warning("Did not find expected major folders (%s) inside %s.",
                                 ", ".join(target_folders), scan_path)
                 # Optionally, could still check for JSONs directly in intermediate_dir here
                 # json_files_intermediate = list(scan_path.glob('*.json'))
                 # ... processing logic ...
                 # For now, we strictly expect major folders inside the intermediate dir
                 return {}
        else:
            # No intermediate directory, check for major folders directly in audit_base_path
            logging.info("No intermediate directory found. Scanning %s directly for major folders or JSON files.", self.audit_base_path)
            folders_to_scan = [d for d in scan_path.iterdir() if d.is_dir() and d.name in target_folders]

        # --- Process based on findings --- #

        if folders_to_scan: # Found major folders (either directly or in intermediate)
            logging.info("Found major folders to process: %s (scanning from %s)",
                         [f.name for f in folders_to_scan], scan_path)
            for folder_path in folders_to_scan:
                major = folder_path.name
                json_files = list(folder_path.glob('*.json'))
                if not json_files:
                    logging.warning("No JSON files found in %s, skipping...", folder_path)
                    continue

                for json_file in json_files:
                    file_type = "gened" if json_file.name == "published.json" else "core"
                    df_name = f"{major}_{file_type}"
                    logging.info("Processing audit file: %s as %s", json_file.name, df_name)
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            audit_json_data = json.load(f)
                        audit_tuples = self._getAuditData(audit_json_data, source_name=json_file.name)
                        if audit_tuples:
                            processed_data[df_name] = audit_tuples
                            files_processed_count += 1
                    except FileNotFoundError:
                        logging.error("Audit file disappeared?: %s", json_file)
                    except json.JSONDecodeError:
                        logging.error("Error decoding JSON in audit file: %s", json_file)
                    except Exception as e:
                        logging.exception("Unexpected error processing audit file %s: %s", json_file.name, e)
        else:
            # No major folders found, check for JSON files directly in the scan_path
            # (This handles the case where majors aren't in folders OR the original fallback)
            logging.warning("No major folders found in %s. Looking for JSON files directly.", scan_path)
            json_files_direct = list(scan_path.glob('*.json'))
            if not json_files_direct:
                logging.error("No target major folders or JSON files found in scan path: %s.", scan_path)
                return {}

            for json_file in json_files_direct:
                major = "unknown"
                file_name_lower = json_file.stem.lower()
                for tf in target_folders:
                    if tf in file_name_lower:
                        major = tf
                        break
                file_type = "gened" if "gen" in file_name_lower or "published" in file_name_lower else "core"
                df_name = f"{major}_{file_type}"
                logging.info("Processing direct JSON file: %s as %s", json_file.name, df_name)
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        audit_json_data = json.load(f)
                    audit_tuples = self._getAuditData(audit_json_data, source_name=json_file.name)
                    if audit_tuples:
                        processed_data[df_name] = audit_tuples
                        files_processed_count += 1
                except FileNotFoundError:
                    logging.error("Audit file disappeared?: %s", json_file)
                except json.JSONDecodeError:
                    logging.error("Error decoding JSON in audit file: %s", json_file)
                except Exception as e:
                    logging.exception("Unexpected error processing direct audit file %s: %s", json_file.name, e)

        logging.info("Retrieved raw audit data for %d identifiers from %d files",
                     len(processed_data), files_processed_count)
        return processed_data

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

    def get_courses_from_code(self, dept_code, course_codes):
        """
        Finds all courses that start with the given department code.
        Example: if dept_code='02', returns all courses like '02-201', '02-202'.
        """
        return [c for c in course_codes if c.startswith(dept_code)]

    def get_results(self, db_course_codes: set) -> dict[str, list[dict]]:
        """
        Extracts audit data by processing JSON files directly.
        Requires a set of existing database course codes to be passed in for validation.
        Returns a dictionary with audit, requirement, and countsfor tables.
        """
        logging.info("Starting audit data extraction and transformation...")
        # course_codes are now passed in
        if not db_course_codes:
             logging.warning("Received empty set of database course codes. Countsfor table might be inaccurate.")

        combined_data = []

        # Get processed audit data (dict mapping id -> list of tuples)
        processed_audit_data = self.get_processed_audit_data() # Reads files

        if not processed_audit_data:
            logging.warning("No raw audit data found or processed.")
            return {"audit": [], "requirement": [], "countsfor": []}

        # Define specific requirements to exclude for IS major
        is_excluded_requirements = {
            "BS in Information Systems",
            "Qatar Information Systems - General Education - 2024+",
            "Qatar Information Systems - General Education - 2024+---General Education"
        }

        # Process each identifier (e.g., 'cs_core') and its list of tuples
        for identifier, audit_tuples in processed_audit_data.items():
            logging.info("Processing identifier: %s (%d tuples)", identifier, len(audit_tuples))

            try:
                major, audit_type_str = identifier.split('_')
                audit_type = 0 if audit_type_str == 'core' else 1  # 0 for core, 1 for gened
            except ValueError:
                logging.error("Invalid identifier format: %s. Skipping.", identifier)
                continue

            # Process each tuple in the list
            # Tuple format: (course_or_code, req_chain, inclusion/exclusion, type_str)
            for course_or_code, req_chain, inc_exc, type_str in audit_tuples:
                if not course_or_code or not req_chain: # Basic validation
                    logging.warning("Skipping tuple with missing course/code or requirement chain: %s",
                                    (course_or_code, req_chain, inc_exc, type_str))
                    continue

                processed_req = self.post_process_requirement(req_chain)

                # Skip excluded requirements for IS major
                if major.lower() == 'is' and processed_req in is_excluded_requirements:
                    logging.debug("Skipping excluded IS requirement: %s", processed_req)
                    continue

                if inc_exc == "Inclusion":
                    audit_name = processed_req.split('---')[0].strip() # Extract top-level audit name
                    if type_str == "Code":
                        # If it's a department code, find all courses with that code FROM THE PASSED IN SET
                        matching_courses = self.get_courses_from_code(course_or_code, db_course_codes)
                        if matching_courses:
                            for course in matching_courses:
                                combined_data.append({
                                    "requirement": processed_req,
                                    "course": course,
                                    "audit_type": audit_type,
                                    "major": major,
                                    "audit": audit_name
                                })
                        # else: No need to log here if dept code simply has no matching courses in DB
                    elif type_str == "Course":
                        # Regular course - check if it exists in the passed in set
                        if course_or_code in db_course_codes:
                            combined_data.append({
                                "requirement": processed_req,
                                "course": course_or_code,
                                "audit_type": audit_type,
                                "major": major,
                                "audit": audit_name
                            })
                        # else: logging.debug("Course %s from audit '%s' not in db_course_codes. Not adding to countsfor.", course_or_code, processed_req)
                # else: Handle "Exclusion" if needed

        # --- Create final tables ---
        if combined_data:
            # Additional filtering for IS major requirements (redundant check, but safe)
            combined_data = [d for d in combined_data if not (d["major"].lower() == "is" and
                                                              d["requirement"] in
                                                              is_excluded_requirements)]
            if not combined_data:
                 logging.warning("No combined data remaining after filtering.")
                 return {"audit": [], "requirement": [], "countsfor": []}

            # Create audit table
            audit_df = pd.DataFrame(combined_data)[["audit", "audit_type", "major"]].drop_duplicates()
            audit_df.dropna(subset=["major", "audit_type"], inplace=True)
            audit_df["audit_id"] = audit_df["major"].astype(str) + "_" + audit_df["audit_type"].astype(str)
            audit_df = audit_df.rename(columns={"audit": "name", "audit_type": "type"})
            audit_df = audit_df.drop_duplicates(subset=["audit_id"])

            # Create countsfor table
            counts_df = pd.DataFrame(combined_data)[["requirement", "course"]].drop_duplicates()
            counts_df = counts_df.rename(columns={"course": "course_code"})

            # Create requirement table
            req_df = pd.DataFrame(combined_data)[["requirement", "major", "audit_type"]].drop_duplicates()
            req_df.dropna(subset=["requirement", "major", "audit_type"], inplace=True)
            req_df = req_df.rename(columns={"audit_type": "type"})
            req_df = req_df.merge(
                audit_df[["audit_id", "major", "type"]],
                on=["major", "type"],
                how="inner"
            )
            req_df = req_df[["requirement", "audit_id"]].drop_duplicates()

            dupes = req_df[req_df.duplicated(subset=["requirement"], keep=False)]
            if not dupes.empty:
                logging.warning("Duplicate requirements found mapping to potentially different audits: %s", dupes['requirement'].unique())

            results = {
                "audit": audit_df.to_dict(orient="records"),
                "requirement": req_df.to_dict(orient="records"),
                "countsfor": counts_df.to_dict(orient="records")
            }

            logging.info("=== Audit Data Extraction Summary ===")
            for table_name, records in results.items():
                logging.info("Table '%s': %d records", table_name, len(records))
            logging.info("===================================")

            return results
        else:
            logging.warning("No combined data generated from audit processing.")
            return {"audit": [], "requirement": [], "countsfor": []}
