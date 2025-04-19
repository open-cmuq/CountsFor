# pylint: disable=missing-module-docstring, redefined-outer-name
import pytest
from unittest.mock import patch, MagicMock
from backend.services.requirements import RequirementService
from backend.app.schemas import RequirementsResponse, RequirementResponse

# Mock data inspired by requirement.csv and RequirementResponse schema
# Repository is expected to return a list of dicts
MOCK_REQUIREMENTS_DATA = [
    {"requirement": "GenEd---Cultural/Global Understanding---Modern Languages Course", "type": True, "major": "bio"},
    {"requirement": "GenEd---Non-Technical Breadth Electives", "type": False, "major": "bio"},
    {"requirement": "BS in Computer Science---SCS Electives", "type": True, "major": "cs"},
    {"requirement": "BS in Information Systems---Technical Core---Mathematics", "type": True, "major": "is"},
]

@pytest.fixture
def db_session_mock():
    """Provides a mock database session."""
    return MagicMock()

@patch('backend.services.requirements.RequirementRepository')
def test_fetch_all_requirements(mock_requirement_repo, db_session_mock):
    """Test fetching all requirements successfully."""
    # Configure the mock repository method
    mock_repo_instance = mock_requirement_repo.return_value
    mock_repo_instance.get_all_requirements.return_value = MOCK_REQUIREMENTS_DATA

    # Instantiate the service with the mock session
    service = RequirementService(db=db_session_mock)

    # Call the service method
    result = service.fetch_all_requirements()

    # Assertions
    assert isinstance(result, RequirementsResponse)
    assert len(result.requirements) == len(MOCK_REQUIREMENTS_DATA)

    # Check the content of each RequirementResponse object
    for i, expected_req_dict in enumerate(MOCK_REQUIREMENTS_DATA):
        assert isinstance(result.requirements[i], RequirementResponse)
        assert result.requirements[i].requirement == expected_req_dict["requirement"]
        assert result.requirements[i].type == expected_req_dict["type"]
        assert result.requirements[i].major == expected_req_dict["major"]

    # Verify repository methods were called correctly
    mock_requirement_repo.assert_called_once_with(db_session_mock)
    mock_repo_instance.get_all_requirements.assert_called_once()