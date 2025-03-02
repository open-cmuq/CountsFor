"""
this script tests database/db.py
"""
import os
import unittest
from sqlalchemy import inspect
import database.db as db

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

class TestDBInitialization(unittest.TestCase):
    """
    Test the database initialization.
    """
    @classmethod
    def setUpClass(cls):
        db.init_db()
        cls.inspector = inspect(db.engine)

    def test_tables_created(self):
        """
        Test that the tables are created successfully.
        """
        expected_tables = [
            "course", "prereqs", "offering", "instructor",
            "course_instructor", "countsfor", "requirement",
            "audit", "enrollment"
        ]
        created_tables = self.inspector.get_table_names()
        for table in expected_tables:
            self.assertIn(table, created_tables, f"Table {table} should be created.")

if __name__ == "__main__":
    unittest.main()
