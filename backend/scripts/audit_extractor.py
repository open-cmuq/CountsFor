"""
audit_extractor.py

This module defines the AuditDataExtractor class that extracts course and
requirement details from audit JSON files and outputs Excel files for the database tables.
It inherits common functionality from DataExtractor.
"""

import re
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple

import pandas as pd
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
    # pylint: disable=invalid-name
    def _getCoursesFromRange(begin, end, inc_exc, req_chain
                             ) -> List[Tuple[str, str, str, str]]:
        """
        Extracts courses from a range of course numbers.
        """
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
    # pylint: disable=invalid-name
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
                    courses_from_range.extend(AuditDataExtractor._getCoursesFromRange(r[0], r[1],
                                                                                      'Inclusion',
                                                                                      req_chain))

            return [(c, req_chain, 'Inclusion', 'Course') for c in courses] + courses_from_range

        elif t == 'xfromdepts':
            depts = data.get('depts', [])
            additional_courses = data.get('additional_courses', [])
            return [(d.get('code'), req_chain, 'Inclusion', 'Code') \
                    for d in depts if d.get('code')] + \
                   [(c, req_chain, 'Inclusion', 'Course') for c in additional_courses]

        elif t == 'notcountcourseset':
            courses = []
            if 'courses' in data:
                courses = data['courses']
            elif 'conditional_course_sets' in data:
                for course_set in data['conditional_course_sets']:
                    if 'courses' in course_set:
                        courses.extend(course_set['courses'])
            return [(c, req_chain, 'Exclusion', 'Course') for c in courses]

        else:
            logging.warning("Not accounting for constraint type: %s", t)
            return []

    @staticmethod
    # pylint: disable=invalid-name
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
                        courses_list.extend(AuditDataExtractor._getCoursesFromConstraint(c,
                        new_req_chain))
                # else: Base case? Maybe a requirement with no choices/constraints?
            elif 'type' in data: # If it's a constraint itself at this level
                courses_list.extend(AuditDataExtractor._getCoursesFromConstraint(data,
                                    new_req_chain))
            elif 'screen_name' in data: # Base case: a single course identified by screen_name
                course_num = data['screen_name']
                # Basic validation for course code format XX-XXX
                if re.match(r"^\d{2}-\d{3}$", course_num):
                    courses_list.append((course_num, new_req_chain, 'Inclusion', 'Course'))
                else:
                    logging.warning("Skipping non-course screen_name as course: %s", course_num)


        elif isinstance(data, list): # Handle lists of items (e.g., in uni_req_tree)
            for item in data:
                courses_list.extend(AuditDataExtractor._getCourses(item, req_chain))

        return courses_list


    @staticmethod
    # pylint: disable=invalid-name
    def _getAuditData(data: Dict[str, Any],
                    source_name: str = "Unknown") -> List[Tuple[str, str, str, str]]:
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
            logging.warning("No top-level 'requirement' key found in audit data from %s",
                            source_name)

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
        target_folders = {'ba', 'bio', 'cs', 'is'}
        subdirs = [d for d in self.audit_base_path.iterdir() if d.is_dir()]
        subdirs_names = {d.name for d in subdirs}

        folders_to_scan = []

        # Check if the base path itself contains the major folders
        if target_folders.issubset(subdirs_names) or any(m in subdirs_names
                                                         for m in target_folders):
            logging.info("Found major folders directly under %s. Processing these.",
                         self.audit_base_path)
            folders_to_scan = [d for d in subdirs if d.name in target_folders]
            # scan_path remains self.audit_base_path
        # If not, check if there's exactly ONE subdirectory,
        # and assume THAT contains the major folders
        elif len(subdirs) == 1:
            potential_intermediate_dir = subdirs[0]
            logging.info("Found single subdirectory '%s'. Checking inside for major folders.",
                         potential_intermediate_dir.name)
            scan_path = potential_intermediate_dir # Update scan path
            major_subdirs_inside = [d for d in scan_path.iterdir()
                                    if d.is_dir() and d.name in target_folders]
            if major_subdirs_inside:
                logging.info("Found major folders inside '%s'. Processing these.",
                             potential_intermediate_dir.name)
                folders_to_scan = major_subdirs_inside
            else:
                logging.warning("Single subdirectory '%s' did not contain expected major folders.",
                                potential_intermediate_dir.name)
        # If multiple subdirs but none match the expected structure, log warning
        elif len(subdirs) > 1:
            logging.warning("Multiple subdirectories found in %s,\
                             but none directly contain the expected major\
                             folders (%s).", self.audit_base_path, ', '.join(target_folders))
            # Decide how to handle this - currently will lead to empty folders_to_scan
        else:
            logging.warning("No subdirectories found in %s.", self.audit_base_path)
            # This also leads to empty folders_to_scan

        files_processed_count = 0
        scan_path = self.audit_base_path # Ensure scan_path is initialized

        # --- Process based on findings --- #

        if folders_to_scan: # Found major folders (either directly or in intermediate)
            logging.info("Processing major folders found: %s", [f.name for f in folders_to_scan])
            for folder_path in folders_to_scan:
                major = folder_path.name
                # Log the actual folder being processed
                logging.info("Processing audit files in folder: %s", folder_path)
                json_files = list(folder_path.glob('*.json'))
                if not json_files:
                    logging.warning("No JSON files found in %s, skipping...", folder_path)
                    continue

                for json_file in json_files:
                    file_type = "gened" if json_file.name == "published.json" else "core"
                    df_name = f"{major}_{file_type}" # Keep f-string for variable assignment
                    logging.info("Processing audit file: %s as %s", json_file.name, df_name)
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            audit_json_data = json.load(f)
                        audit_tuples = self._getAuditData(audit_json_data,
                                                          source_name=json_file.name)
                        if audit_tuples:
                            processed_data[df_name] = audit_tuples
                            files_processed_count += 1
                    except FileNotFoundError:
                        logging.error("Audit file disappeared?: %s", json_file)
                    except json.JSONDecodeError:
                        logging.error("Error decoding JSON in audit file: %s", json_file)
                    except Exception as e: # pylint: disable=broad-exception-caught
                        logging.exception("Unexpected error processing audit file %s: %s",
                                           json_file.name, e)
        else:
            # No major folders found, check for JSON files directly in the scan_path
            # (This handles the case where majors aren't in folders OR the original fallback)
            logging.warning("No major folders found in %s. Looking for JSON files directly.",
                            scan_path)
            json_files_direct = list(scan_path.glob('*.json'))
            if not json_files_direct:
                logging.error("No target major folders or JSON files found in scan path: %s.",
                              scan_path)
                return {}

            for json_file in json_files_direct:
                major = "unknown"
                file_name_lower = json_file.stem.lower()
                for tf in target_folders:
                    if tf in file_name_lower:
                        major = tf
                        break
                if "gen" in file_name_lower or "published" in file_name_lower:
                    file_type = "gened"
                else:
                    file_type = "core"

                df_name = f"{major}_{file_type}" # Keep f-string for variable assignment
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
                except Exception as e: # pylint: disable=broad-exception-caught
                    logging.exception("Unexpected error processing direct audit file %s: %s",
                                      json_file.name, e)

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
        Handles course exclusions correctly.
        Returns a dictionary with audit, requirement, and countsfor tables.
        """
        logging.info("Starting audit data extraction and transformation...")
        if not db_course_codes:
            logging.warning("Received empty set of database course codes. \
                            Countsfor table might be inaccurate.")

        # Get processed audit data (dict mapping id -> list of tuples)
        processed_audit_data = self.get_processed_audit_data() # Reads files

        if not processed_audit_data:
            logging.warning("No raw audit data found or processed.")
            return {"audit": [], "requirement": [], "countsfor": []}

        # Define specific requirements to exclude entirely for IS major (e.g., degree checks)
        is_excluded_requirements = {
            "BS in Information Systems",
            "Qatar Information Systems - General Education - 2024+",
            "Qatar Information Systems - General Education - 2024+---General Education"
        }

        all_rows = []
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
                    logging.warning("Skipping tuple with missing course/code \
                                    or requirement chain: %s",
                                    (course_or_code, req_chain, inc_exc, type_str))
                    continue

                processed_req = self.post_process_requirement(req_chain)

                # Skip processing entirely for certain IS requirements
                if major.lower() == 'is' and processed_req in is_excluded_requirements:
                    logging.debug("Skipping completely excluded IS requirement entry: %s",
                                  processed_req)
                    continue

                audit_name = processed_req.split('---')[0].strip() # Extract top-level audit name

                all_rows.append({
                    "major": major,
                    "audit_type": audit_type,
                    "audit_name": audit_name,
                    "requirement": processed_req,
                    "course_or_code": course_or_code,
                    "type_str": type_str,
                    "inc_exc": inc_exc
                })

        if not all_rows:
            logging.warning("No raw rows generated from audit data.")
            return {"audit": [], "requirement": [], "countsfor": []}

        # Create a DataFrame from all rows
        combined_df = pd.DataFrame(all_rows)

        # --- Expand 'Code' entries into individual courses ---
        logging.info("Expanding department code entries...")
        expanded_entries = []
        codes_df = combined_df[combined_df['type_str'] == 'Code']
        courses_df = combined_df[combined_df['type_str'] == 'Course']

        for _, row in codes_df.iterrows():
            # Pass the full set of DB codes for lookup
            matching_courses = self.get_courses_from_code(row['course_or_code'], db_course_codes)
            if matching_courses:
                for course in matching_courses:
                    new_entry = row.to_dict()
                    new_entry['course'] = course # Add the specific course code
                    # Clean up temporary fields
                    del new_entry['course_or_code']
                    del new_entry['type_str']
                    expanded_entries.append(new_entry)
            # else: logging.debug("No courses found in DB for dept code %s", row['course_or_code'])

        # Add existing course rows, renaming columns for consistency
        courses_df['course'] = courses_df['course_or_code']
        courses_df = courses_df.drop(columns=['course_or_code', 'type_str'])
        expanded_entries.extend(courses_df.to_dict(orient='records'))

        if not expanded_entries:
            logging.warning("No valid course entries after expanding codes.")
            return {"audit": [], "requirement": [], "countsfor": []}

        # Create DataFrame from fully expanded entries and remove duplicates
        final_expanded_df = pd.DataFrame(expanded_entries).drop_duplicates()
        logging.info("Total expanded entries (before exclusion): %d", len(final_expanded_df))

        # --- Identify exclusions ---
        # An exclusion applies to a course within a specific major/audit_type context
        exclusions_df = final_expanded_df[final_expanded_df['inc_exc'] == 'Exclusion']
        # Create a set of tuples (major, audit_type, course) for quick lookup
        exclusion_set = set(exclusions_df[['major', 'audit_type',
                                           'course']].itertuples(index=False, name=None))
        logging.info("Identified %d unique exclusion rules (major, type, course).",
                     len(exclusion_set))

        # --- Filter inclusions ---
        inclusions_df = final_expanded_df[final_expanded_df['inc_exc'] == 'Inclusion'].copy()
        logging.info("Initial inclusion entries: %d", len(inclusions_df))

        # Define a function to check if an inclusion row should be removed due to an exclusion
        def is_excluded(row):
            return (row['major'], row['audit_type'], row['course']) in exclusion_set

        # Apply the filter using boolean indexing (more efficient than apply)
        excluded_mask = inclusions_df.apply(is_excluded, axis=1)
        filtered_inclusions_df = inclusions_df[~excluded_mask]
        logging.info("Inclusion entries after filtering exclusions: %d",
                     len(filtered_inclusions_df))

        # --- Create final tables from filtered_inclusions_df ---
        if filtered_inclusions_df.empty:
            logging.warning("No inclusion data remaining after filtering exclusions.")
            return {"audit": [], "requirement": [], "countsfor": []}

        # Create countsfor table (Requirement <-> Course mapping)
        counts_df = filtered_inclusions_df[["requirement", "course"]].drop_duplicates()
        counts_df = counts_df.rename(columns={"course": "course_code"})

        # Create audit table (Unique Audits based on remaining data)
        # Ensures only audits with actual counting courses are included
        audit_df = filtered_inclusions_df[["audit_name", "audit_type",
                                           "major"]].drop_duplicates()
        audit_df.dropna(subset=["major", "audit_type"], inplace=True)
        audit_df["audit_id"] = audit_df["major"].astype(str) + "_" + audit_df["audit_type"
                                                                              ].astype(str)
        audit_df = audit_df.rename(columns={"audit_name": "name", "audit_type": "type"})
        audit_df = audit_df.drop_duplicates(subset=["audit_id"]) # Ensure unique audit_id

        # Create requirement table (Unique Requirements linked to Audits)
        # Ensures only requirements with actual counting courses are included
        req_df_raw = filtered_inclusions_df[["requirement", "major",
                                              "audit_type"]].drop_duplicates()
        req_df_raw.dropna(subset=["requirement", "major", "audit_type"], inplace=True) # Safe check
        req_df_raw = req_df_raw.rename(columns={"audit_type": "type"})

        # Merge with audit_df to get audit_id, ensuring requirements belong to a valid final audit
        req_df = req_df_raw.merge(
            audit_df[["audit_id", "major", "type"]],
            on=["major", "type"],
            how="inner" # Only keep requirements belonging to an audit in audit_df
        )
        # Select final columns and ensure uniqueness
        req_df = req_df[["requirement", "audit_id"]].drop_duplicates()

        dupes = req_df[req_df.duplicated(subset=["requirement"], keep=False)]
        if not dupes.empty:
            logging.warning("Duplicate requirements found mapping to potentially\
                             different audits (after exclusion filtering\
                            ): %s", dupes['requirement'].unique())

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
