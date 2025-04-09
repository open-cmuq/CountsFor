"""
audit_extractor.py

This module defines the AuditDataExtractor class that extracts course and
requirement details from audit JSON files and outputs Excel files for the database tables.
It inherits common functionality from DataExtractor.
"""

import os
import re
import logging
import pandas as pd
from backend.database.db import SessionLocal
from backend.database.models import Course
import backend.scripts.extract_audit_dataframes as extract_audit_dataframes

# Import the common base class.
from backend.scripts.data_extractor import DataExtractor

# Ensure pandas displays full column width
pd.set_option('display.max_colwidth', None)
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


class AuditDataExtractor(DataExtractor):
    """
    Extracts course and requirement details from audit JSON files.
    Uses extract_audit_dataframes module to fetch pre-processed dataframes.
    """
    def __init__(self, audit_base_path, course_base_path):
        """
        Initializes the extractor with the paths to the audit files,
        course JSON files, and the course table Excel file.
        """
        super().__init__()
        self.audit_base_path = audit_base_path
        self.course_base_path = course_base_path

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

    def get_audit_dataframes(self):
        """
        Fetches all audit dataframes from extract_audit_dataframes module.
        Returns a dictionary of dataframes with keys like 'cs_core', 'cs_gened', etc.
        """
        logging.info("Fetching audit dataframes from extract_audit_dataframes module")
        try:
            dataframes = extract_audit_dataframes.main()
            logging.info(f"Retrieved {len(dataframes)} audit dataframes")

            # Validate and standardize each dataframe
            validated_dataframes = {}
            for df_name, df in dataframes.items():
                validated_df = self.validate_dataframe(df)
                if validated_df is not None:
                    validated_dataframes[df_name] = validated_df

            return validated_dataframes
        except Exception as e:
            logging.error(f"Error fetching audit dataframes: {e}")
            return {}

    def validate_dataframe(self, df):
        """
        Validates and standardizes a dataframe to ensure it has all required columns.
        Adds missing columns with default values if needed.
        """
        required_columns = [
            "Type", "Inclusion/Exclusion", "Course or code", "Requirement"
        ]

        # Check if all required columns exist
        for col in required_columns:
            if col not in df.columns:
                logging.error(f"Required column '{col}' missing from dataframe")
                return None

        # If dataframe passes validation, return it
        return df

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

    def get_results(self) -> dict[str, list[dict]]:
        """
        Extracts audit data from dataframes provided by extract_audit_dataframes module.
        Returns a dictionary with audit, requirement, and countsfor tables.
        """
        logging.info("Starting to extract audit data from dataframes")
        course_codes = self.get_course_codes()
        combined_data = []

        # Get all dataframes from extract_audit_dataframes
        audit_dataframes = self.get_audit_dataframes()

        if not audit_dataframes:
            logging.warning("No audit dataframes found")
            return {
                "audit": [],
                "requirement": [],
                "countsfor": []
            }

        # Define specific requirements to exclude for IS major
        is_excluded_requirements = {
            "BS in Information Systems",
            "Qatar Information Systems - General Education - 2024+",
            "Qatar Information Systems - General Education - 2024+---General Education"
        }

        # Process each dataframe
        for df_name, df in audit_dataframes.items():
            logging.info(f"Processing dataframe: {df_name}")

            # Extract major and audit_type from dataframe name (e.g., 'cs_core', 'ba_gened')
            try:
                major, audit_type_str = df_name.split('_')
                audit_type = 0 if audit_type_str == 'core' else 1  # 0 for core, 1 for gened
            except ValueError:
                logging.error(f"Invalid dataframe name format: {df_name}")
                continue

            # Check if the dataframe has a Min Units column
            has_min_units = "Min Units" in df.columns

            # Process each row in the dataframe
            for _, row in df.iterrows():
                processed_req = self.post_process_requirement(row["Requirement"])

                # Skip excluded requirements for IS major
                if major.lower() == 'is' and processed_req in is_excluded_requirements:
                    logging.info(f"Skipping excluded IS requirement: {processed_req}")
                    continue

                # Get min_units value if available
                min_units = row.get("Min Units") if has_min_units else None

                # Try to get units from the dataframe if available
                if min_units is None and "Units" in df.columns:
                    units_value = row.get("Units")
                    if units_value and not pd.isna(units_value) and str(units_value).isdigit():
                        min_units = int(units_value)

                if row["Inclusion/Exclusion"] == "Inclusion":
                    if row["Type"] == "Code":
                        # If it's a department code, find all courses with that code
                        matching_courses = self.get_courses_from_code(row["Course or code"], course_codes)
                        if matching_courses:
                            for course in matching_courses:
                                combined_data.append({
                                    "requirement": processed_req,
                                    "course": course,
                                    "min_units": min_units,
                                    "audit_type": audit_type,
                                    "major": major,
                                    "audit": processed_req.split('---')[0].strip()
                                })
                        else:
                            # Log if no matching courses found for a department code
                            logging.warning(f"No matching courses found for department code: {row['Course or code']}")
                    else:
                        # Regular course
                        combined_data.append({
                            "requirement": processed_req,
                            "course": row["Course or code"],
                            "min_units": min_units,
                            "audit_type": audit_type,
                            "major": major,
                            "audit": processed_req.split('---')[0].strip()
                        })

        # Create audit table data
        if combined_data:
            # Additional filtering for IS major requirements
            combined_data = [d for d in combined_data if not (d["major"].lower() == "is" and
                                                              d["requirement"] in is_excluded_requirements)]

            # Create audit table
            audit_df = pd.DataFrame(combined_data)[["audit", "audit_type", "major"]].drop_duplicates()
            audit_df["audit_id"] = audit_df["major"] + "_" + audit_df["audit_type"].astype(str)
            audit_df = audit_df.rename(columns={"audit": "name", "audit_type": "type"})
            audit_df = audit_df.drop_duplicates()

            # Get existing courses from database
            session = SessionLocal()
            try:
                existing_courses = set(row[0] for row in session.query(Course.course_code).all())
            finally:
                session.close()

            # Create countsfor table
            counts_df = pd.DataFrame(combined_data)[["requirement", "course"]]
            counts_df = counts_df.rename(columns={"course": "course_code"}).drop_duplicates()

            # Check how many courses aren't in the database
            if not existing_courses:
                logging.warning("No existing courses found in database. Keeping all courses in countsfor table.")
            else:
                # Log how many courses are missing from the database
                missing_courses = set(counts_df["course_code"]) - existing_courses
                if missing_courses:
                    logging.warning(f"Found {len(missing_courses)} courses in audit data that aren't in the database")
                    if len(missing_courses) < 20:  # Only log if there aren't too many
                        logging.warning(f"Missing courses: {sorted(list(missing_courses))}")

                # Optional: Filter to only include courses in database (comment this out to include all courses)
                # counts_df = counts_df[counts_df["course_code"].isin(existing_courses)]

            # Create requirement table
            req_df = pd.DataFrame(combined_data)[["requirement", "major", "audit_type"]].drop_duplicates()
            req_df = req_df.rename(columns={"audit_type": "type"})
            req_df = req_df.merge(
                audit_df[["audit_id", "major", "type"]],
                on=["major", "type"],
                how="left"
            )
            req_df = req_df[["requirement", "audit_id"]]

            # Check for duplicates
            dupes = req_df[req_df.duplicated(subset=["requirement"], keep=False)]
            if not dupes.empty:
                logging.warning("Duplicate requirements across audits found")

            # Prepare results
            results = {
                "audit": audit_df.to_dict(orient="records"),
                "requirement": req_df.to_dict(orient="records"),
                "countsfor": counts_df.to_dict(orient="records")
            }

            # Log summary of results
            logging.info("=== Audit Data Extraction Summary ===")
            for table_name, records in results.items():
                logging.info(f"Table '{table_name}': {len(records)} records")
            logging.info("===================================")

            return results
        else:
            logging.warning("No combined data found for audits.")
            return {
                "audit": [],
                "requirement": [],
                "countsfor": []
            }
