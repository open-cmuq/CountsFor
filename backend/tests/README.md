# Backend Tests

This directory (`backend/tests/`) contains automated tests, primarily focusing on the backend application components.

## Running Tests

Tests are run using `pytest` from the **project root directory** (`CountsFor/`).

**Run all backend tests:**

```bash
# Ensure you are in the project root directory
python -m pytest backend/tests
```

**Run tests in a specific backend test directory:**

```bash
# Example: Run only database tests
python -m pytest backend/tests/database
```

**Run tests in a specific backend test file:**

```bash
python -m pytest backend/tests/database/test_data_extractors.py
```

**Run a specific test function:**

```bash
python -m pytest backend/tests/database/test_data_extractors.py::test_some_extractor_method
```

## Test Structure

Tests within this directory are organized by the backend layer they target:

*   **`database/`**: Contains tests related to data extraction, file handling, and potentially direct database interactions or model validation. Includes:
    *   `test_data_extractors.py`: Verifies the logic of the data extractors in `backend/scripts/` (Audit, Course, Enrollment). See detailed section below.
    *   `test_file_preparation.py`: Tests utility functions related to file handling and preparation, likely used during data uploads.
    *   `test_data/`: Contains sample input files used by the data extractor tests.
*   **`routers/`**: Contains integration tests for the FastAPI API endpoints defined in `backend/app/routers/`. These tests typically use a test client to send requests to the API and assert the responses.
*   **`services/`**: Contains unit or integration tests for the business logic components located in `backend/services/`. These tests verify the logic within the service layer, often mocking repository interactions.

## Data Extractor Tests (`database/test_data_extractors.py`)

### Purpose: Regression Testing

The primary goal of the tests for `AuditDataExtractor`, `CourseDataExtractor`, and `EnrollmentDataExtractor` is **regression testing**. They verify that the current code correctly processes a known set of input data formats and produces the expected output.

*   **Test Data:** Input data (e.g., sample JSON files) is stored within this directory at `database/test_data/`.
*   **Expected Output:** The tests often compare the extractor's output against reference data derived from the CSV files located in the project root `data/csv_exports/` directory.
*   **Granular Tests:** In addition to testing the main `get_results` method, specific unit tests exist for certain internal helper methods (e.g., `AuditDataExtractor.post_process_requirement`, `AuditDataExtractor._getCoursesFromRange`, `AuditDataExtractor._getCoursesFromConstraint`, `EnrollmentDataExtractor.format_course_code`) to verify their logic in isolation.

### Handling New Data Formats

These tests **do not automatically validate** the extractors against completely new or unforeseen data structures in future uploaded files. They test the code's behavior against the formats it *was designed for* at the time the tests were written or last updated.

If new data (e.g., new audit JSONs) causes issues:

1.  **Identify:** Use the extractor's failure or incorrect output with the new data, combined with the passing status of these tests, to pinpoint that the issue lies in handling the *new format*, not a regression in handling old formats.
2.  **Update Test Data:** Add the new file(s) or representative examples to the relevant subdirectory within `database/test_data/`.
3.  **Define Expectations:** Determine the correct output for this new data (you might need to manually inspect the new data and potentially update the reference CSVs or test assertions).
4.  **Adapt Code:** Modify the relevant extractor code (`backend/scripts/*.py`) to handle the new format/structure/data points correctly.
5.  **Test:** Rerun the tests. The newly added test cases (or modified existing ones) should now pass, confirming the code handles both old and new formats.

This process ensures the extractors remain robust and adaptable as data sources evolve, while the regression tests safeguard existing functionality.