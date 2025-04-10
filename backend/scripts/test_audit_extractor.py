#!/usr/bin/env python3
"""
Test script for the refactored AuditDataExtractor class.
This script verifies that the AuditDataExtractor correctly uses the extract_audit_dataframes module.
"""

import os
import sys
import logging
from pathlib import Path

# Add the parent directory to the path to make imports work from any directory
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from backend.scripts.audit_extractor import AuditDataExtractor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def main():
    """
    Main function to test the AuditDataExtractor.
    """
    # Get paths to data directories
    project_root = Path(__file__).resolve().parent.parent.parent
    audit_path = os.path.join(project_root, "data", "audit")
    course_path = os.path.join(project_root, "data", "course")

    logging.info(f"Using audit path: {audit_path}")
    logging.info(f"Using course path: {course_path}")

    # Create an instance of the AuditDataExtractor
    extractor = AuditDataExtractor(audit_path, course_path)

    # Test getting audit dataframes
    dataframes = extractor.get_audit_dataframes()
    if dataframes:
        logging.info(f"Successfully retrieved {len(dataframes)} audit dataframes")
        for df_name, df in dataframes.items():
            logging.info(f"Dataframe '{df_name}' has {len(df)} rows")
    else:
        logging.error("Failed to retrieve audit dataframes")

    # Test getting results
    results = extractor.get_results()
    if results:
        for table_name, records in results.items():
            logging.info(f"Table '{table_name}' has {len(records)} records")
            if records and table_name == "audit":
                logging.info(f"Sample audit record: {records[0]}")
            if records and table_name == "requirement":
                logging.info(f"Sample requirement record: {records[0]}")
            if records and table_name == "countsfor":
                logging.info(f"Sample countsfor record: {records[0]}")
    else:
        logging.error("Failed to get results")

if __name__ == "__main__":
    main()