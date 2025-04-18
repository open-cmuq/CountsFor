# pylint: disable=missing-module-docstring, redefined-outer-name
import pytest
from unittest.mock import patch, MagicMock
from backend.services.departments import DepartmentService
from backend.app.schemas import DepartmentListResponse, DepartmentResponse

# Mock data inspired by department.csv
MOCK_DEPARTMENTS_DATA = [
    ("15", "Computer Science"),
    ("70", "Business Administration"),
    ("67", "Information Systems Program"),
    ("03", "Biological Sciences"),
]

@pytest.fixture
def db_session_mock():
    """Provides a mock database session."""
    return MagicMock()

@patch('backend.services.departments.DepartmentRepository')
def test_fetch_all_departments(mock_department_repo, db_session_mock):
    """Test fetching all departments successfully."""
    # Configure the mock repository method
    mock_repo_instance = mock_department_repo.return_value
    mock_repo_instance.get_all_departments.return_value = MOCK_DEPARTMENTS_DATA

    # Instantiate the service with the mock session
    service = DepartmentService(db=db_session_mock)

    # Call the service method
    result = service.fetch_all_departments()

    # Assertions
    assert isinstance(result, DepartmentListResponse)
    assert len(result.departments) == len(MOCK_DEPARTMENTS_DATA)

    # Check the content of each DepartmentResponse object
    for i, expected_dept in enumerate(MOCK_DEPARTMENTS_DATA):
        assert isinstance(result.departments[i], DepartmentResponse)
        assert result.departments[i].dep_code == expected_dept[0]
        assert result.departments[i].name == expected_dept[1]

    # Verify repository methods were called correctly
    mock_department_repo.assert_called_once_with(db_session_mock)
    mock_repo_instance.get_all_departments.assert_called_once()