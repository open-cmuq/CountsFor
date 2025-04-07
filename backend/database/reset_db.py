"""
Script to reset the database by dropping all tables and recreating them.
Use this script to reinitialize the database with empty tables for testing data uploads.
"""

import os
import sys
from backend.database.db import reset_db

# Add parent directory to Python path to allow imports
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(parent_dir)

if __name__ == "__main__":
    print("Starting database reset...")
    reset_db()
    print("Database has been reinitialized with empty tables.")
    print("You can now use the data upload interface to test uploading data.")
