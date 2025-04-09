# Audit Extractor Refactoring

This document describes the refactoring of the `audit_extractor.py` module to use the new `extract_audit_dataframes` module for extracting course and requirement data from audit JSON files.

## Overview

The `AuditDataExtractor` class has been refactored to use the `extract_audit_dataframes` module instead of directly handling file discovery and audit processing. The new implementation:

1. Uses dataframes returned by `extract_audit_dataframes.main()`
2. Validates and standardizes these dataframes
3. Processes them to generate three tables:
   - `audit`: Information about audit types (core/gened) for each major
   - `requirement`: Links requirements to their parent audits
   - `countsfor`: Maps courses to the requirements they satisfy

## Key Methods

### `get_audit_dataframes()`
- Fetches all audit dataframes from the `extract_audit_dataframes` module
- Validates and standardizes each dataframe
- Returns a dictionary of validated dataframes with keys like 'cs_core', 'cs_gened', etc.

### `validate_dataframe(df)`
- Validates that a dataframe has all required columns
- Returns the validated dataframe or None if validation fails

### `post_process_requirement(req)`
- Cleans and standardizes requirement strings
- Removes trailing course codes, arrows, and other artifacts

### `get_results()`
- Processes dataframes to extract data for the database tables
- Creates audit, requirement, and countsfor tables
- Returns a dictionary with the three tables as lists of dictionaries

### `get_course_codes()`
- Retrieves all course codes from the database
- Used to match department codes to actual courses

## How to Use

```python
from backend.scripts.audit_extractor import AuditDataExtractor

# Initialize the extractor with paths to audit and course data
extractor = AuditDataExtractor(
    audit_base_path="/path/to/audit/files",
    course_base_path="/path/to/course/files"
)

# Get the extracted data
results = extractor.get_results()

# Access the individual tables
audit_table = results["audit"]
requirement_table = results["requirement"]
countsfor_table = results["countsfor"]
```

## Testing

A test script is provided in `backend/scripts/test_audit_extractor.py` to verify the functionality of the refactored code. Run it with:

```bash
python backend/scripts/test_audit_extractor.py
```

The test script will:
1. Create an instance of the `AuditDataExtractor`
2. Test fetching audit dataframes
3. Test extracting results and display summary information

## Notes

- The refactored code handles cases where courses in the audit data don't exist in the database by logging warnings and keeping all courses in the countsfor table.
- Special handling is implemented for IS major requirements to exclude certain specific requirements.
- The code assumes that dataframe names follow the pattern 'major_type' (e.g., 'cs_core', 'ba_gened').