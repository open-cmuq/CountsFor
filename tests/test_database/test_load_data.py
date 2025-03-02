"""
this script tests database/load_data.py
"""

import os
import unittest
import tempfile
import pandas as pd
import database.db as db
import database.load_data as load_data
from database.models import (
    Instructor,
    Course,
    Audit,
    Requirement,
    CountsFor,
    Offering,
    Prereqs,
    CourseInstructor,
    Enrollment
)

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

class TestLoadDataPerTable(unittest.TestCase):
    """
    Test the loading of data for each table.
    """
    @classmethod
    def setUpClass(cls):
        db.init_db()

    def create_temp_excel(self, df):
        """helper to create a temporary Excel file from a DataFrame."""
        tmp = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
        tmp.close()
        df.to_excel(tmp.name, index=False)
        return tmp.name

    def test_load_instructor(self):
        """
        test loading of data into the Instructor table.
        """
        df = pd.DataFrame({
            "andrew_id": ["dphelps"],
            "first_name": ["Daniel"],
            "last_name": ["Phelps"]
        })
        file_path = self.create_temp_excel(df)
        try:
            load_data.load_excel_data(file_paths=[("instructor", file_path)])
            session = db.SessionLocal()
            instructor = session.query(Instructor).filter_by(andrew_id="dphelps").first()
            self.assertIsNotNone(instructor, "Instructor record should be inserted.")
            self.assertEqual(instructor.first_name, "Daniel")
        finally:
            os.remove(file_path)
            session.close()

    def test_load_course(self):
        """
        test loading of data into the Course table.
        """
        df = pd.DataFrame({
            "course_code": ["67-380"],
            "name": ["Information Systems Security"],
            "units": [9],
            "min_units": [9],
            "max_units": [9],
            "offered_qatar": [False],
            "offered_pitts": [True],
            "short_name": ["INFORMATION SYS SEC"],
            "description": ["Basic course"],
            "dep_code": ["67"],
            "prereqs_text": [""]
        })
        file_path = self.create_temp_excel(df)
        try:
            load_data.load_excel_data(file_paths=[("course", file_path)])
            session = db.SessionLocal()
            course = session.query(Course).filter_by(course_code="67-380").first()
            self.assertIsNotNone(course, "Course record should be inserted.")
            self.assertEqual(course.name, "Information Systems Security")
        finally:
            os.remove(file_path)
            session.close()

    def test_load_audit(self):
        """
        test loading of data into the Audit table.
        """
        df = pd.DataFrame({
            "audit_id": ["is_0"],
            "name": ["BS in Information Systems"],
            "type": [False],
            "major": ["is"]
        })
        file_path = self.create_temp_excel(df)
        try:
            load_data.load_excel_data(file_paths=[("audit", file_path)])
            session = db.SessionLocal()
            audit = session.query(Audit).filter_by(audit_id="is_0").first()
            self.assertIsNotNone(audit, "Audit record should be inserted.")
            self.assertEqual(audit.name, "BS in Information Systems")
        finally:
            os.remove(file_path)
            session.close()

    def test_load_requirement(self):
        """
        test loading of data into the Requirement table.
        """
        # Requirement depends on Audit load audit first.
        audit_df = pd.DataFrame({
            "audit_id": ["cs_1"],
            "name": ["GenEd"],
            "type": [True],
            "major": ["cs"]
        })
        req_df = pd.DataFrame({
            "requirement": ["GenEd---First Year Writing"],
            "audit_id": ["cs_1"]
        })
        audit_file = self.create_temp_excel(audit_df)
        req_file = self.create_temp_excel(req_df)
        try:
            load_data.load_excel_data(file_paths=[("audit", audit_file), ("requirement", req_file)])
            session = db.SessionLocal()
            req = session.query(Requirement).filter_by(requirement="GenEd---First Year Writing").first()
            self.assertIsNotNone(req, "Requirement record should be inserted.")
            self.assertEqual(req.audit_id, "cs_1")
        finally:
            os.remove(audit_file)
            os.remove(req_file)
            session.close()

    def test_load_countsfor(self):
        """
        test loading of data into the CountsFor table.
        """
        # CountsFor depends on Course and Requirement (and Requirement depends on Audit).
        audit_df = pd.DataFrame({
            "audit_id": ["ba_0"],
            "name": ["BS in Business Administration"],
            "type": [False],
            "major": ["ba"]
        })
        req_df = pd.DataFrame({
            "requirement": ["Business Foundations---Mathematics---Calculus"],
            "audit_id": ["ba_0"]
        })
        course_df = pd.DataFrame({
            "course_code": ["21-112"],
            "name": ["Calculus II"],
            "units": [10],
            "min_units": [10],
            "max_units": [10],
            "offered_qatar": [True],
            "offered_pitts": [True],
            "short_name": ["INTEGRAL CALCULUS"],
            "description": ["Basic math course"],
            "dep_code": ["21"],
            "prereqs_text": [""]
        })
        countsfor_df = pd.DataFrame({
            "course_code": ["21-112"],
            "requirement": ["Business Foundations---Mathematics---Calculus"]
        })
        audit_file = self.create_temp_excel(audit_df)
        req_file = self.create_temp_excel(req_df)
        course_file = self.create_temp_excel(course_df)
        countsfor_file = self.create_temp_excel(countsfor_df)
        try:
            load_data.load_excel_data(file_paths=[
                ("audit", audit_file),
                ("requirement", req_file),
                ("course", course_file),
                ("countsfor", countsfor_file)
            ])
            session = db.SessionLocal()
            cf = session.query(CountsFor).filter_by(
                course_code="21-112",
                requirement="Business Foundations---Mathematics---Calculus").first()
            self.assertIsNotNone(cf, "CountsFor record should be inserted.")
        finally:
            for f in [audit_file, req_file, course_file, countsfor_file]:
                os.remove(f)
            session.close()

    def test_load_offering(self):
        """
        test loading of data into the Offering table.
        """
        # Offering depends on Course.
        course_df = pd.DataFrame({
            "course_code": ["21-112"],
            "name": ["Calculus II"],
            "units": [10],
            "min_units": [10],
            "max_units": [10],
            "offered_qatar": [True],
            "offered_pitts": [True],
            "short_name": ["INTEGRAL CALCULUS"],
            "description": ["Basic math course"],
            "dep_code": ["21"],
            "prereqs_text": [""]
        })
        offering_df = pd.DataFrame({
            "offering_id": ["21-112_M21_2"],
            "semester": ["M21"],
            "course_code": ["21-112"],
            "campus_id": [2]
        })
        course_file = self.create_temp_excel(course_df)
        offering_file = self.create_temp_excel(offering_df)
        try:
            load_data.load_excel_data(file_paths=[
                ("course", course_file),
                ("offering", offering_file)
            ])
            session = db.SessionLocal()
            offering = session.query(Offering).filter_by(offering_id="21-112_M21_2").first()
            self.assertIsNotNone(offering, "Offering record should be inserted.")
            self.assertEqual(offering.semester, "M21")
        finally:
            os.remove(course_file)
            os.remove(offering_file)
            session.close()

    def test_load_prereqs(self):
        """
        test loading of data into the Prereqs table.
        """
        # Prereqs depends on Course.
        course_df = pd.DataFrame({
            "course_code": ["21-112"],
            "name": ["Calculus II"],
            "units": [10],
            "min_units": [10],
            "max_units": [10],
            "offered_qatar": [True],
            "offered_pitts": [True],
            "short_name": ["INTEGRAL CALCULUS"],
            "description": ["Basic math course"],
            "dep_code": ["21"],
            "prereqs_text": [""]
        })
        prereqs_df = pd.DataFrame({
            "course_code": ["21-112"],
            "prerequisite": ["21-111"],
            "group_id": [1],
            "logic_type": ["ALL"]
        })
        course_file = self.create_temp_excel(course_df)
        prereqs_file = self.create_temp_excel(prereqs_df)
        try:
            load_data.load_excel_data(file_paths=[
                ("course", course_file),
                ("prereqs", prereqs_file)
            ])
            session = db.SessionLocal()
            prereq = session.query(Prereqs).filter_by(course_code="21-112", prerequisite="21-111").first()
            self.assertIsNotNone(prereq, "Prereqs record should be inserted.")
            self.assertEqual(prereq.logic_type, "ALL")
        finally:
            os.remove(course_file)
            os.remove(prereqs_file)
            session.close()

    def test_load_course_instructor(self):
        """
        test loading of data into the CourseInstructor table.
        """
        # CourseInstructor depends on Instructor and Course.
        instructor_df = pd.DataFrame({
            "andrew_id": ["aweston2"],
            "first_name": ["Anthony Ross"],
            "last_name": ["Weston"]
        })
        course_df = pd.DataFrame({
            "course_code": ["21-112"],
            "name": ["Calculus II"],
            "units": [10],
            "min_units": [10],
            "max_units": [10],
            "offered_qatar": [True],
            "offered_pitts": [True],
            "short_name": ["INTEGRAL CALCULUS"],
            "description": ["Basic math course"],
            "dep_code": ["21"],
            "prereqs_text": [""]
        })
        ci_df = pd.DataFrame({
            "andrew_id": ["21-112"],
            "course_code": ["PHYS101"]
        })
        instr_file = self.create_temp_excel(instructor_df)
        course_file = self.create_temp_excel(course_df)
        ci_file = self.create_temp_excel(ci_df)
        try:
            load_data.load_excel_data(file_paths=[
                ("instructor", instr_file),
                ("course", course_file),
                ("course_instructor", ci_file)
            ])
            session = db.SessionLocal()
            ci = session.query(CourseInstructor).filter_by(andrew_id="aweston2",
                                                           course_code="21-112").first()
            self.assertIsNotNone(ci, "CourseInstructor record should be inserted.")
        finally:
            for f in [instr_file, course_file, ci_file]:
                os.remove(f)
            session.close()

    def test_load_enrollment(self):
        """
        test loading of data into the Enrollment table.
        """
        # Enrollment depends on Offering, which in turn depends on Course.
        course_df = pd.DataFrame({
            "course_code": ["21-112"],
            "name": ["Calculus II"],
            "units": [10],
            "min_units": [10],
            "max_units": [10],
            "offered_qatar": [True],
            "offered_pitts": [True],
            "short_name": ["INTEGRAL CALCULUS"],
            "description": ["Basic math course"],
            "dep_code": ["21"],
            "prereqs_text": [""]
        })
        offering_df = pd.DataFrame({
            "offering_id": ["21-122_M20_2"],
            "semester": ["Fall2025"],
            "course_code": ["21-112"],
            "campus_id": [3]
        })
        enrollment_df = pd.DataFrame({
            "enrollment_id": ["enrCHEM1"],
            "class_": [201],
            "enrollment_count": [25],
            "department": ["CHEM"],
            "section": ["2"],
            "offering_id": ["offCHEM1"]
        })
        course_file = self.create_temp_excel(course_df)
        offering_file = self.create_temp_excel(offering_df)
        enrollment_file = self.create_temp_excel(enrollment_df)
        try:
            load_data.load_excel_data(file_paths=[
                ("course", course_file),
                ("offering", offering_file),
                ("enrollment", enrollment_file)
            ])
            session = db.SessionLocal()
            enrollment = session.query(Enrollment).filter_by(enrollment_id="enrCHEM1").first()
            self.assertIsNotNone(enrollment, "Enrollment record should be inserted.")
            self.assertEqual(enrollment.class_, 201)
            self.assertEqual(enrollment.enrollment_count, 25)
            self.assertEqual(enrollment.section, "2")
        finally:
            for f in [course_file, offering_file, enrollment_file]:
                os.remove(f)
            session.close()

if __name__ == "__main__":
    unittest.main()
