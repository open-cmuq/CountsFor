# Backend Tests

This directory contains automated tests for the backend application components.

## Running Tests

Tests are typically run using `pytest` from the project root directory.

Example:
```bash
# Run all tests in the backend/tests directory
python -m pytest backend/tests

# Run tests in a specific file
python -m pytest backend/tests/unit/test_data_extractors.py

# Run a specific test function
python -m pytest backend/tests/unit/test_data_extractors.py::test_format_course_code
```

## Test Structure

Tests are currently organized into:

*   `integration/`: Tests involving interactions between multiple components or with external factors (like file system operations). Example: `test_file_preparation.py`.
*   `unit/`: Tests focused on isolating and verifying individual functions or classes. Example: `test_data_extractors.py`.

## Data Extractor Tests (`unit/test_data_extractors.py`)

### Purpose: Regression Testing

The primary goal of the tests for `AuditDataExtractor`, `CourseDataExtractor`, and `EnrollmentDataExtractor` is **regression testing**. They verify that the current code correctly processes a known set of input data formats and produces the expected output.

*   **Test Data:** Input data (e.g., sample JSON files) is stored in `backend/tests/unit/test_data/`.
*   **Expected Output:** The tests often compare the extractor's output against reference data derived from the CSV files located in `data/csv_exports/`.
*   **Granular Tests:** In addition to testing the main `get_results` method, specific unit tests exist for certain internal helper methods (e.g., `AuditDataExtractor.post_process_requirement`, `AuditDataExtractor._getCoursesFromRange`, `AuditDataExtractor._getCoursesFromConstraint`, `EnrollmentDataExtractor.format_course_code`) to verify their logic in isolation.

### Handling New Data Formats

These tests **do not automatically validate** the extractors against completely new or unforeseen data structures in future uploaded files. They test the code's behavior against the formats it *was designed for* at the time the tests were written or last updated.

If new data (e.g., new audit JSONs) causes issues:

1.  **Identify:** Use the extractor's failure or incorrect output with the new data, combined with the passing status of these tests, to pinpoint that the issue lies in handling the *new format*, not a regression in handling old formats.
2.  **Update Test Data:** Add the new file(s) or representative examples to the relevant subdirectory within `backend/tests/unit/test_data/`.
3.  **Define Expectations:** Determine the correct output for this new data (you might need to manually inspect the new data and potentially update the reference CSVs or test assertions).
4.  **Adapt Code:** Modify the relevant extractor code (`backend/scripts/*.py`) to handle the new format/structure/data points correctly.
5.  **Test:** Rerun the tests. The newly added test cases (or modified existing ones) should now pass, confirming the code handles both old and new formats.

This process ensures the extractors remain robust and adaptable as data sources evolve, while the regression tests safeguard existing functionality.