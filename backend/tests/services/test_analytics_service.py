# pylint: disable=missing-module-docstring, redefined-outer-name
import pytest
from unittest.mock import patch, MagicMock
from backend.services.analytics import AnalyticsService
from backend.app.schemas import CourseCoverageResponse, CourseCoverageItem

# Mock data for course coverage (repo returns Dict[str, int])
MOCK_COVERAGE_DATA = {
    "BS in Computer Science---SCS Electives": 5,
    "GenEd---Humanities/Arts Electives": 10,
    "BS in Computer Science---Computer Science": 15,
}

# Mock data for enrollment data (repo returns List[Dict])
MOCK_ENROLLMENT_DATA = [
    {"semester": "F23", "enrollment_count": 50, "class_": 100},
    {"semester": "S24", "enrollment_count": 65, "class_": 150},
    {"semester": "F24", "enrollment_count": 55, "class_": 120},
]

@pytest.fixture
def db_session_mock():
    """Provides a mock database session."""
    return MagicMock()

@patch('backend.services.analytics.AnalyticsRepository')
def test_fetch_course_coverage_without_semester(mock_analytics_repo, db_session_mock):
    """Test fetching course coverage without specifying a semester."""
    # Configure mock
    mock_repo_instance = mock_analytics_repo.return_value
    mock_repo_instance.get_course_coverage.return_value = MOCK_COVERAGE_DATA

    service = AnalyticsService(db=db_session_mock)
    major_to_fetch = "cs"
    result = service.fetch_course_coverage(major=major_to_fetch)

    # Assertions
    assert isinstance(result, CourseCoverageResponse)
    assert result.major == major_to_fetch
    assert result.semester is None
    assert len(result.coverage) == len(MOCK_COVERAGE_DATA)

    # Check coverage items (order might not be guaranteed, so check content)
    result_coverage_dict = {item.requirement: item.num_courses for item in result.coverage}
    assert result_coverage_dict == MOCK_COVERAGE_DATA

    # Verify repo call
    mock_analytics_repo.assert_called_once_with(db_session_mock)
    mock_repo_instance.get_course_coverage.assert_called_once_with(major_to_fetch, None)

@patch('backend.services.analytics.AnalyticsRepository')
def test_fetch_course_coverage_with_semester(mock_analytics_repo, db_session_mock):
    """Test fetching course coverage specifying a semester."""
    # Configure mock
    mock_repo_instance = mock_analytics_repo.return_value
    mock_repo_instance.get_course_coverage.return_value = MOCK_COVERAGE_DATA # Use same mock data for simplicity

    service = AnalyticsService(db=db_session_mock)
    major_to_fetch = "cs"
    semester_to_fetch = "F23"
    result = service.fetch_course_coverage(major=major_to_fetch, semester=semester_to_fetch)

    # Assertions
    assert isinstance(result, CourseCoverageResponse)
    assert result.major == major_to_fetch
    assert result.semester == semester_to_fetch
    assert len(result.coverage) == len(MOCK_COVERAGE_DATA)

    result_coverage_dict = {item.requirement: item.num_courses for item in result.coverage}
    assert result_coverage_dict == MOCK_COVERAGE_DATA

    # Verify repo call
    mock_analytics_repo.assert_called_once_with(db_session_mock)
    mock_repo_instance.get_course_coverage.assert_called_once_with(major_to_fetch, semester_to_fetch)

@patch('backend.services.analytics.AnalyticsRepository')
def test_fetch_enrollment_data(mock_analytics_repo, db_session_mock):
    """Test fetching enrollment data for a course."""
    # Configure mock
    mock_repo_instance = mock_analytics_repo.return_value
    mock_repo_instance.get_enrollment_data.return_value = MOCK_ENROLLMENT_DATA

    service = AnalyticsService(db=db_session_mock)
    course_code_to_fetch = "15-121"
    result = service.fetch_enrollment_data(course_code=course_code_to_fetch)

    # Assertions (Service returns a list of dicts, not a Pydantic model here)
    assert isinstance(result, list)
    assert len(result) == len(MOCK_ENROLLMENT_DATA)

    # Check content of each dict
    for i, expected_enrollment_dict in enumerate(MOCK_ENROLLMENT_DATA):
        assert isinstance(result[i], dict)
        assert result[i]["semester"] == expected_enrollment_dict["semester"]
        assert result[i]["enrollment_count"] == expected_enrollment_dict["enrollment_count"]
        assert result[i]["class_"] == expected_enrollment_dict["class_"]

    # Verify repo call
    mock_analytics_repo.assert_called_once_with(db_session_mock)
    mock_repo_instance.get_enrollment_data.assert_called_once_with(course_code_to_fetch)