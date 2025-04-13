"""
This script implements the data access layer for courses.
"""

from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from backend.database.models import Course, CountsFor, Requirement, Offering, Audit
import logging

class CourseRepository:
    """encapsulates all database operations for the 'Course' entity."""

    def __init__(self, db: Session):
        self.db = db

    def get_course_by_code(self, course_code: str):
        """fetch course details by course code (raw data only)."""
        return self.db.query(Course).filter(Course.course_code == course_code).first()

    def get_offered_semesters(self, course_code: str):
        """fetch semesters in which a course is offered."""
        offered_semesters = (
            self.db.query(Offering.semester)
            .filter(Offering.course_code == course_code)
            .all()
        )
        return [semester[0] for semester in offered_semesters]

    def get_course_requirements(self, course_code: str):
        """fetch requirements per major for a course."""
        requirements = {"CS": [], "IS": [], "BA": [], "BS": []}
        requirements_query = (
            self.db.query(CountsFor.requirement, Requirement.audit_id, Audit.type)
            .join(Requirement, CountsFor.requirement == Requirement.requirement)
            .join(Audit, Requirement.audit_id == Audit.audit_id)
            .filter(CountsFor.course_code == course_code)
            .all()
        )

        for req, audit_id, req_bool in requirements_query:
            if audit_id.startswith("cs"):
                requirements["CS"].append({
                    "requirement": req,
                    "type": bool(req_bool),
                    "major": "CS"
                })
            elif audit_id.startswith("is"):
                requirements["IS"].append({
                    "requirement": req,
                    "type": bool(req_bool),
                    "major": "IS"
                })
            elif audit_id.startswith("ba"):
                requirements["BA"].append({
                    "requirement": req,
                    "type": bool(req_bool),
                    "major": "BA"
                })
            elif audit_id.startswith("bio"):
                requirements["BS"].append({
                    "requirement": req,
                    "type": bool(req_bool),
                    "major": "BS"
                })

        return requirements

    def get_all_semesters(self):
        """fetch a distinct list of all semesters from the Offerings table."""
        semesters = self.db.query(Offering.semester).distinct().all()
        # Each row is a tuple (semester,), so extract the first element.
        return [semester[0] for semester in semesters]

    def get_courses_by_filters(self,
                            department: Optional[str] = None,
                            search_query: Optional[str] = None,
                            semester: Optional[str] = None,
                            has_prereqs: Optional[bool] = None,
                            cs_requirement: Optional[str] = None,
                            is_requirement: Optional[str] = None,
                            ba_requirement: Optional[str] = None,
                            bs_requirement: Optional[str] = None,
                            offered_qatar: Optional[bool] = None,
                            offered_pitts: Optional[bool] = None):
        """Fetch courses matching any combination of provided filters."""
        query = self.db.query(Course)

        # Filter by department.
        if department:
            query = query.filter(Course.dep_code == department)

        # Filter by search query on course code.
        if search_query:
            query = query.filter(Course.course_code.ilike(f"%{search_query}%"))

        # Filter by prerequisites.
        if has_prereqs is not None:
            if has_prereqs:
                query = query.filter(
                    Course.prereqs_text.isnot(None),
                    Course.prereqs_text != "",
                    Course.prereqs_text != "None"
                )
            else:
                query = query.filter(
                    (Course.prereqs_text.is_(None)) | (Course.prereqs_text == "")
                      | (Course.prereqs_text == "None")
                )

        # --- Defer Requirement Filtering to Python ---
        # The complex logic for handling AND within majors and OR between them
        # is better handled after fetching candidates.

        # --- Location and Semester Filtering ---
        # This part requires joining with Offering table
        needs_offering_join = semester or (offered_qatar is not None) or (offered_pitts is not None)
        if needs_offering_join:
            # Base subquery on Offerings
            offering_subquery = self.db.query(Offering.course_code).distinct()

            # Filter by semester if provided
            if semester:
                semester_list = [s.strip() for s in semester.split(",") if s.strip()]
                if semester_list:
                    offering_subquery = offering_subquery.filter(Offering.semester.in_(semester_list))

            # Filter by location
            location_conditions = []
            if offered_qatar is True:
                location_conditions.append(Offering.campus_id == 2)
            if offered_pitts is True:
                location_conditions.append(Offering.campus_id == 1)

            # Apply location filters if any were specified
            if location_conditions:
                 # If specific locations are requested, apply OR logic between them
                if offered_qatar is True and offered_pitts is True:
                     # If both are True, we might need courses offered in EITHER location
                     # depending on exact requirements, but the current filter finds courses
                     # listed in offerings for the specified semesters at either campus.
                     # Let's assume user wants courses available in *at least one* of the specified locations+semesters
                     offering_subquery = offering_subquery.filter(or_(*location_conditions))
                elif offered_qatar is True:
                    offering_subquery = offering_subquery.filter(location_conditions[0])
                elif offered_pitts is True:
                    offering_subquery = offering_subquery.filter(location_conditions[0])
            elif offered_qatar is False or offered_pitts is False:
                 # Handle cases where user explicitly wants courses *not* in a location.
                 # This requires a more complex subquery or anti-join, potentially excluding
                 # courses based on campus_id. Let's stick to positive filtering for now.
                 # If offered_qatar is False, filter out courses linked to campus_id 2?
                 # If offered_pitts is False, filter out courses linked to campus_id 1?
                 # This needs clarification, current logic handles only True cases.
                 # For simplicity, we only filter *for* locations specified as True.
                 # If only False is provided (e.g., qatar=False, pitts=None), this block isn't hit.
                 pass


            # Apply the subquery filter to the main query
            query = query.filter(Course.course_code.in_(offering_subquery.scalar_subquery()))


        # Execute the query to get candidate courses
        try:
            candidate_courses = query.distinct().all()
            logging.info(f"Initial filter query returned {len(candidate_courses)} candidate courses.")
        except Exception as e:
            logging.error(f"Error executing initial course filter query: {e}")
            return [] # Return empty list on query error

        # --- Python-based Requirement Filtering ---
        required_cs_set = set(r.strip() for r in cs_requirement.strip().split(',') if r.strip()) if cs_requirement else set()
        required_is_set = set(r.strip() for r in is_requirement.strip().split(',') if r.strip()) if is_requirement else set()
        required_ba_set = set(r.strip() for r in ba_requirement.strip().split(',') if r.strip()) if ba_requirement else set()
        required_bs_set = set(r.strip() for r in bs_requirement.strip().split(',') if r.strip()) if bs_requirement else set()

        any_req_filter_active = bool(required_cs_set or required_is_set or required_ba_set or required_bs_set)

        if not any_req_filter_active:
            # If no requirement filters are active, all candidates pass
            filtered_courses = candidate_courses
        else:
            filtered_courses = []
            logging.info(f"Applying Python requirement filters: CS={required_cs_set}, IS={required_is_set}, BA={required_ba_set}, BS={required_bs_set}")
            for course in candidate_courses:
                requirements_dict = self.get_course_requirements(course.course_code)

                actual_cs = set(r['requirement'] for r in requirements_dict.get('CS', []))
                actual_is = set(r['requirement'] for r in requirements_dict.get('IS', []))
                actual_ba = set(r['requirement'] for r in requirements_dict.get('BA', []))
                actual_bs = set(r['requirement'] for r in requirements_dict.get('BS', []))

                # Check if ALL specified requirements for EACH major are met
                cs_match = not required_cs_set or required_cs_set.issubset(actual_cs)
                is_match = not required_is_set or required_is_set.issubset(actual_is)
                ba_match = not required_ba_set or required_ba_set.issubset(actual_ba)
                bs_match = not required_bs_set or required_bs_set.issubset(actual_bs)

                # The course must satisfy the requirements for all majors for which requirements were specified
                if cs_match and is_match and ba_match and bs_match:
                    filtered_courses.append(course)
                    # logging.info(f"Course {course.course_code} MATCHED filters.") # Verbose logging if needed
                # else:
                    # logging.info(f"Course {course.course_code} REJECTED by filters. CS:{cs_match}, IS:{is_match}, BA:{ba_match}, BS:{bs_match}") # Verbose logging


        # Format the final list of courses
        result = []
        logging.info(f"Processing {len(filtered_courses)} filtered courses to add details...")
        for course in filtered_courses:
            try:
                # Fetch details needed for the response object
                offered_semesters = self.get_offered_semesters(course.course_code)
                # Fetch requirements again to ensure the final response object has the full, correct structure
                requirements = self.get_course_requirements(course.course_code)
                # Log the fetched requirements for debugging
                # logging.debug(f"Course: {course.course_code}, Requirements for response: {requirements}")

                result.append({
                    "course_code": course.course_code,
                    "course_name": course.name,
                    "department": course.dep_code,
                    "units": course.units,
                    "description": course.description,
                    "prerequisites": course.prereqs_text or "None",
                    "offered_qatar": course.offered_qatar,
                    "offered_pitts": course.offered_pitts,
                    "offered": offered_semesters,
                    "requirements": requirements, # Ensure this is the structured dict
                })
            except Exception as e:
                 logging.error(f"Error processing details for course {course.course_code}: {e}")
                 continue

        logging.info(f"Finished processing filters. Returning {len(result)} courses with details.")
        return result
