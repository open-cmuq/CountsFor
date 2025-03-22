"""
Course Data Extractor Module

This module defines the CourseDataExtractor class for extracting course data from JSON files.
It follows design principles such as Single Responsibility, DRY, and Separation of Concerns.
"""

import os
import json
import re
import logging
from typing import Any, Dict, List, Tuple
import pandas as pd

from backend.scripts.data_extractor import DataExtractor

# Configuration & Constants
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
COLUMNS_TO_KEEP = [
    "course_code", "name", "units", "min_units", "max_units",
    "offered_qatar", "offered_pitts", "short_name", "description",
    "dep_code", "prereqs_text",
]

class CourseDataExtractor(DataExtractor):
    """
    Extracts course data from JSON files.
    """
    def __init__(self, folder_path: str, base_dir: str) -> None:
        super().__init__()
        self.folder_path = folder_path
        self.base_dir = base_dir
        self.courses_data: List[Dict[str, Any]] = []
        self.prereq_relationships: List[Dict[str, Any]] = []
        self.offerings_records: List[Dict[str, Any]] = []
        self.course_instructor: List[Dict[str, Any]] = []
        self.instructors_data: Dict[str, Dict[str, Any]] = {}

        # Define output file paths
        self.course_table_file = os.path.join(self.base_dir, "Course.xlsx")
        self.prereqs_table_file = os.path.join(self.base_dir, "Prereqs.xlsx")
        self.offerings_table_file = os.path.join(self.base_dir, "Offering.xlsx")
        self.course_instructor_table_file = os.path.join(self.base_dir, "Course_Instructor.xlsx")
        self.instructor_table_file = os.path.join(self.base_dir, "Instructor.xlsx")

    # ------------------------- Utility Methods -------------------------

    @staticmethod
    def extract_req_relationships(req_data: Any) -> List[str]:
        """
        Recursively extracts course codes from a requirement data structure.
        """
        codes: List[str] = []
        if isinstance(req_data, dict):
            if "req_obj" in req_data:
                codes.extend(CourseDataExtractor.extract_req_relationships(req_data["req_obj"]))
            if "choices" in req_data:
                for choice in req_data["choices"]:
                    codes.extend(CourseDataExtractor.extract_req_relationships(choice))
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
                codes.extend(CourseDataExtractor.extract_req_relationships(item))
        return codes

    @staticmethod
    def get_logic_type(req_obj: Dict[str, Any]) -> str:
        """
        Determines the logic type ("ALL" or "ANY") from the requirement object.
        """
        try:
            constraints = req_obj.get("constraints", [])
            for constraint in constraints:
                if isinstance(constraint, dict) and constraint.get("type") in ("anyxof", "allxof"):
                    is_and = constraint.get("data", {}).get("is_and", False)
                    return "ALL" if is_and else "ANY"
        except (AttributeError, TypeError) as error:
            logging.error("Error determining logic type: %s", error)
        return "ANY"


    @staticmethod
    def parse_req_obj(course_code: str, req_obj: Dict[str, Any],
                      group_id_counter: int) -> Tuple[int, List[Dict[str, Any]]]:
        """
        Parses a top-level requirement object and returns updated group_id and rows.
        """
        rows: List[Dict[str, Any]] = []
        top_level_logic = CourseDataExtractor.get_logic_type(req_obj)
        top_choices = req_obj.get("choices", [])

        if not top_choices:
            prereq_codes = CourseDataExtractor.extract_req_relationships(req_obj)
            for code in prereq_codes:
                rows.append({
                    "course_code": course_code,
                    "prerequisite": code,
                    "logic_type": top_level_logic,
                    "group_id": group_id_counter
                })
            group_id_counter += 1
            return group_id_counter, rows

        for choice in top_choices:
            group_logic = (CourseDataExtractor.get_logic_type(choice)
                           if choice.get("constraints") else top_level_logic)
            codes_in_choice = CourseDataExtractor.extract_req_relationships(choice)
            for code in set(codes_in_choice):
                rows.append({
                    "course_code": course_code,
                    "prerequisite": code,
                    "logic_type": group_logic,
                    "group_id": group_id_counter
                })
            group_id_counter += 1

        return group_id_counter, rows

    # ------------------------- Data Extraction Methods -------------------------

    def extract_course_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extracts basic course information from the JSON data.
        """
        code = data.get("code")
        name = data.get("name")
        if not code or not name:
            raise ValueError("Missing course code or name")
        dep_code_str = code.split("-")[0]
        dep_code = int(dep_code_str) if dep_code_str.isdigit() and len(dep_code_str) == 2 else None
        is_undergraduate = any(s.get("name") == "undergraduate" for s in data.get("student_sets",
                                                                                  []))
        offered_qatar = 1 in data.get("offered_in_campuses", [])
        offered_pitts = 2 in data.get("offered_in_campuses", [])

        # Handle the case when "units" is None.
        units_value = data.get("units", 0)
        try:
            # If units_value is None, default to 0
            units = int(units_value) if units_value is not None else 0
        except ValueError:
            logging.warning("Invalid unit value for course %s, defaulting to 0", code)
            units = 0

        if dep_code is None or not is_undergraduate or not (offered_qatar or offered_pitts):
            raise ValueError("Course does not meet criteria")
        prereqs_text = data.get("prereqs", {}).get("text", "") if isinstance(data.get("prereqs"),
                                                                             dict) else ""
        return {
            "course_code": code,
            "name": name,
            "units": units,
            "min_units": int(data.get("min_units", 0)),
            "max_units": int(data.get("max_units", 0)),
            "offered_qatar": offered_qatar,
            "offered_pitts": offered_pitts,
            "short_name": data.get("short_name"),
            "description": data.get("long_desc"),
            "dep_code": dep_code,
            "prereqs_text": prereqs_text,
        }


    def extract_prereqs(self, data: Dict[str, Any], code: str) -> None:
        """
        Extracts prerequisites from the course JSON data.
        """
        prereqs_data = data.get("prereqs")
        group_id_counter = 1
        if prereqs_data:
            if isinstance(prereqs_data, dict) and "req_obj" in prereqs_data:
                req_obj = prereqs_data.get("req_obj")
                if req_obj:
                    group_id_counter, new_rows = CourseDataExtractor.parse_req_obj(code,
                                                                                   req_obj,
                                                                                   group_id_counter)
                    self.prereq_relationships.extend(new_rows)
                else:
                    codes = set(CourseDataExtractor.extract_req_relationships(prereqs_data))
                    for ccode in codes:
                        self.prereq_relationships.append({
                            "course_code": code,
                            "prerequisite": ccode,
                            "logic_type": "ANY",
                            "group_id": group_id_counter
                        })
                    group_id_counter += 1

    def extract_offerings(self, data: Dict[str, Any], code: str) -> None:
        """
        Extracts course offerings from the JSON data.
        """
        try:
            for offering in data.get("offerings", []):
                campus_id = offering.get("campus_id")
                for sem in offering.get("semesters", []):
                    semester_num = sem.get("semester")
                    year = sem.get("year")
                    if semester_num and year:
                        sem_map = {1: "F", 2: "S", 3: "M"}
                        sem_letter = sem_map.get(semester_num, "X")
                        sem_str = f"{sem_letter}{str(year)[-2:]}"
                        self.offerings_records.append({
                            "offering_id": f"{code}_{sem_str}_{campus_id}",
                            "course_code": code,
                            "semester": sem_str,
                            "campus_id": campus_id
                        })
        except (AttributeError, TypeError) as error:
            logging.error("Error extracting offerings for course %s: %s", code, error)


    def extract_instructors(self, data: Dict[str, Any], code: str) -> None:
        """
        Extracts instructor data from the course JSON data.
        """
        try:
            for instructor in data.get("instructors", []):
                andrew_id = instructor.get("username")
                first_name = instructor.get("first_name")
                last_name = instructor.get("last_name")
                if andrew_id and first_name and last_name:
                    self.course_instructor.append({
                        "course_code": code,
                        "andrew_id": andrew_id
                    })
                    if andrew_id not in self.instructors_data:
                        self.instructors_data[andrew_id] = {
                            "andrew_id": andrew_id,
                            "first_name": first_name,
                            "last_name": last_name
                        }
        except (AttributeError, TypeError) as error:
            logging.error("Error extracting instructors for course %s: %s", code, error)

    def process_course_file(self, file_path: str) -> None:
        """
        Processes a single course JSON file.
        Catches specific exceptions expected from file operations and JSON parsing.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
        except FileNotFoundError as fnf_error:
            logging.warning("File not found %s: %s", os.path.basename(file_path), fnf_error)
            return
        except json.JSONDecodeError as json_error:
            logging.warning("JSON decoding error in file %s: %s",
                            os.path.basename(file_path), json_error)
            return

        if not data.get("success", True):
            return

        try:
            course_info = self.extract_course_info(data)
        except ValueError as ve:
            logging.warning("Error extracting course info from %s: %s",
                            os.path.basename(file_path), ve)
            return

        self.courses_data.append(course_info)
        self.extract_prereqs(data, course_info["course_code"])
        self.extract_offerings(data, course_info["course_code"])
        self.extract_instructors(data, course_info["course_code"])


    def process_all_courses(self) -> None:
        if not os.path.exists(self.folder_path):
            logging.error("Folder not found: %s", self.folder_path)
            return
        # Recursively walk through the folder structure
        for root, dirs, files in os.walk(self.folder_path):
            logging.info("Scanning directory: %s", root)
            for filename in files:
                if filename.endswith(".json"):
                    file_path = os.path.join(root, filename)
                    logging.info("Processing file: %s", file_path)
                    self.process_course_file(file_path)



    def save_results(self) -> None:
        """
        Saves all extracted data to Excel files.
        """
        instructors_list = list(self.instructors_data.values())
        self.save_to_excel(self.courses_data, self.course_table_file)
        self.save_to_excel(self.prereq_relationships, self.prereqs_table_file)
        self.save_to_excel(self.offerings_records, self.offerings_table_file)
        self.save_to_excel(self.course_instructor, self.course_instructor_table_file)
        self.save_to_excel(instructors_list, self.instructor_table_file)

    # ------------------------- DataFrame Processing -------------------------

    @staticmethod
    def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
        """
        Handles missing values in the DataFrame.
        """
        try:
            if "units" in df.columns:
                df["units"] = df["units"].fillna(9).astype(int)
            if "min_units" in df.columns:
                df["min_units"] = df["min_units"].fillna(
                    df["units"].apply(lambda x: 9 if pd.isna(x) else x)).astype(int)
            if "max_units" in df.columns:
                df["max_units"] = df["max_units"].fillna(
                    df["units"].apply(lambda x: 9 if pd.isna(x) else x)).astype(int)
            if "short_name" in df.columns and "name" in df.columns:
                df["short_name"] = df["short_name"].fillna(df["name"])
            if "dep_code" in df.columns:
                df["dep_code"] = df["dep_code"].fillna(-1).astype(int)
            if "offered_qatar" in df.columns:
                df["offered_qatar"] = df["offered_qatar"].fillna(False).astype(bool)
            if "offered_pitts" in df.columns:
                df["offered_pitts"] = df["offered_pitts"].fillna(False).astype(bool)
        except (KeyError, ValueError, TypeError) as error:
            logging.error("Error handling missing values: %s", error)
        return df

    @staticmethod
    def save_to_excel_static(data: List[Dict[str, Any]],
                             output_file: str, columns: List[str] = None) -> None:
        """
        Saves data to an Excel file using specified columns.
        """
        try:
            if not data:
                logging.warning("No data to save for %s", output_file)
                return
            df = pd.DataFrame(data)
            if columns:
                df = df[columns]
                df = CourseDataExtractor.handle_missing_values(df)
            df.to_excel(output_file, index=False)
            logging.info("Data successfully saved to %s", output_file)
        except (KeyError, ValueError, TypeError) as error:
            logging.error("Error saving to %s: %s", output_file, error)

    def get_results(self) -> dict[str, list[dict]]:
        return {
            "course": self.courses_data,
            "prereqs": self.prereq_relationships,
            "offering": self.offerings_records,
            "course_instructor": self.course_instructor,
            "instructor": list(self.instructors_data.values()),
        }



def process_courses(course_base_path: str) -> Dict[str, str]:
    """
    Convenience function to process course data.
    """

    folder_path = os.path.join(course_base_path, "courses")
    extractor = CourseDataExtractor(folder_path=folder_path, base_dir=course_base_path)
    extractor.process_all_courses()
    extractor.save_results()
    return {
        "course_file": extractor.course_table_file,
        "prereqs_file": extractor.prereqs_table_file,
        "offerings_file": extractor.offerings_table_file,
        "course_instructor_file": extractor.course_instructor_table_file,
        "instructor_file": extractor.instructor_table_file,
    }
