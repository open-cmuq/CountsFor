# pylint: disable=missing-module-docstring, redefined-outer-name
import pytest
from unittest.mock import patch, MagicMock
import types # Import types for SimpleNamespace
from backend.services.courses import CourseService
from backend.app.schemas import CourseResponse, CourseListResponse

# Mock data inspired by potential CSV content and CourseResponse schema
MOCK_COURSE_DB_OBJECT = types.SimpleNamespace(
    course_code="15-121",
    name="Introduction to Data Structures",
    dep_code="CS",
    units=10.0,
    description="A first course in data structures.",
    prereqs_text="15-112",
    offered_qatar=True,
    offered_pitts=True,
)
MOCK_OFFERED_SEMESTERS = ["F23", "S24"]
# Updated requirements structure to match Dict[str, List[RequirementResponse-like Dict]]
MOCK_REQUIREMENTS_DICT = {
    "CS": [{"requirement": "CS Core", "type": True, "major": "CS"}]
}

# Mock data for filter tests - Updated requirements structure
MOCK_FILTER_COURSE_1 = {
    "course_code": "15-112",
    "course_name": "Fundamentals of Programming",
    "department": "CS",
    "units": 12.0,
    "description": "Introductory programming course.",
    "prerequisites": "None",
    "offered": ["F23", "S24"],
    "offered_qatar": True,
    "offered_pitts": True,
    "requirements": {
        "CS": [{"requirement": "CS Core", "type": True, "major": "CS"}],
        "IS": [{"requirement": "IS Core", "type": True, "major": "IS"}]
    }
}
MOCK_FILTER_COURSE_2 = {
    "course_code": "66-221",
    "course_name": "Interaction Design Fundamentals",
    "department": "DES",
    "units": 9.0,
    "description": "Design principles.",
    "prerequisites": "None",
    "offered": ["F23"],
    "offered_qatar": True,
    "offered_pitts": False,
    "requirements": {
        "Design": [{"requirement": "Design Minor", "type": False, "major": "Design"}]
    }
}
MOCK_FILTER_COURSE_3 = {
    "course_code": "15-213",
    "course_name": "Introduction to Computer Systems",
    "department": "CS",
    "units": 12.0,
    "description": "Deep dive into computer systems.",
    "prerequisites": "15-122",
    "offered": ["S24"],
    "offered_qatar": False,
    "offered_pitts": True,
    "requirements": {
        "CS": [{"requirement": "CS Core", "type": True, "major": "CS"}]
    }
}

@pytest.fixture
def db_session_mock():
    """Provides a mock database session."""
    return MagicMock()

@patch('backend.services.courses.CourseRepository')
def test_fetch_course_by_code_found(mock_course_repo, db_session_mock):
    """Test fetching an existing course by code."""
    # Configure the mock repository methods
    mock_repo_instance = mock_course_repo.return_value
    # Return a SimpleNamespace or similar object that Pydantic can introspect correctly
    mock_repo_instance.get_course_by_code.return_value = MOCK_COURSE_DB_OBJECT
    mock_repo_instance.get_offered_semesters.return_value = MOCK_OFFERED_SEMESTERS
    # Return the correctly structured dictionary for requirements
    mock_repo_instance.get_course_requirements.return_value = MOCK_REQUIREMENTS_DICT

    # Instantiate the service with the mock session
    service = CourseService(db=db_session_mock)

    # Call the service method
    course_code_to_fetch = "15-121"
    result = service.fetch_course_by_code(course_code_to_fetch)

    # Assertions
    assert result is not None
    assert isinstance(result, CourseResponse)
    # Check attributes from the MOCK_COURSE_DB_OBJECT
    assert result.course_code == MOCK_COURSE_DB_OBJECT.course_code
    assert result.course_name == MOCK_COURSE_DB_OBJECT.name
    assert result.department == MOCK_COURSE_DB_OBJECT.dep_code
    assert result.units == MOCK_COURSE_DB_OBJECT.units
    assert result.description == MOCK_COURSE_DB_OBJECT.description
    assert result.prerequisites == MOCK_COURSE_DB_OBJECT.prereqs_text
    assert result.offered == MOCK_OFFERED_SEMESTERS # From separate mock call
    assert result.offered_qatar == MOCK_COURSE_DB_OBJECT.offered_qatar
    assert result.offered_pitts == MOCK_COURSE_DB_OBJECT.offered_pitts
    # Assert structure and content instead of direct dict comparison
    assert isinstance(result.requirements, dict)
    assert "CS" in result.requirements
    assert isinstance(result.requirements["CS"], list)
    assert len(result.requirements["CS"]) == 1
    assert result.requirements["CS"][0].requirement == MOCK_REQUIREMENTS_DICT["CS"][0]["requirement"]
    assert result.requirements["CS"][0].type == MOCK_REQUIREMENTS_DICT["CS"][0]["type"]
    assert result.requirements["CS"][0].major == MOCK_REQUIREMENTS_DICT["CS"][0]["major"]

    # Verify repository methods were called correctly
    mock_course_repo.assert_called_once_with(db_session_mock)
    mock_repo_instance.get_course_by_code.assert_called_once_with(course_code_to_fetch)
    mock_repo_instance.get_offered_semesters.assert_called_once_with(course_code_to_fetch)
    mock_repo_instance.get_course_requirements.assert_called_once_with(course_code_to_fetch)


@patch('backend.services.courses.CourseRepository')
def test_fetch_course_by_code_not_found(mock_course_repo, db_session_mock):
    """Test fetching a non-existent course by code."""
    # Configure the mock repository method to return None
    mock_repo_instance = mock_course_repo.return_value
    mock_repo_instance.get_course_by_code.return_value = None

    # Instantiate the service with the mock session
    service = CourseService(db=db_session_mock)

    # Call the service method
    course_code_to_fetch = "99-999"
    result = service.fetch_course_by_code(course_code_to_fetch)

    # Assertions
    assert result is None

    # Verify repository methods were called correctly
    mock_course_repo.assert_called_once_with(db_session_mock)
    mock_repo_instance.get_course_by_code.assert_called_once_with(course_code_to_fetch)
    # Ensure other methods were not called if the course wasn't found
    mock_repo_instance.get_offered_semesters.assert_not_called()
    mock_repo_instance.get_course_requirements.assert_not_called()

@patch('backend.services.courses.CourseRepository')
def test_fetch_all_semesters(mock_course_repo, db_session_mock):
    """Test fetching all available semesters."""
    mock_semesters = ["F22", "S23", "F23", "S24"]
    mock_repo_instance = mock_course_repo.return_value
    mock_repo_instance.get_all_semesters.return_value = mock_semesters

    service = CourseService(db=db_session_mock)
    result = service.fetch_all_semesters()

    assert result == mock_semesters
    mock_course_repo.assert_called_once_with(db_session_mock)
    mock_repo_instance.get_all_semesters.assert_called_once()


@patch('backend.services.courses.CourseRepository')
def test_fetch_courses_by_filters_no_filters(mock_course_repo, db_session_mock):
    """Test fetching courses with no filters, checking sorting."""
    # Note the order: 66-221, 15-112, 15-213 (unsorted by code)
    mock_courses_from_repo = [
        MOCK_FILTER_COURSE_2, # 66221
        MOCK_FILTER_COURSE_1, # 15112
        MOCK_FILTER_COURSE_3, # 15213
    ]
    mock_repo_instance = mock_course_repo.return_value
    mock_repo_instance.get_courses_by_filters.return_value = mock_courses_from_repo

    service = CourseService(db=db_session_mock)
    result = service.fetch_courses_by_filters()

    assert isinstance(result, CourseListResponse)
    assert len(result.courses) == 3
    # Check sorting: 15-112, 15-213, 66-221
    assert result.courses[0].course_code == "15-112"
    assert result.courses[1].course_code == "15-213"
    assert result.courses[2].course_code == "66-221"
    # Check one course content detail
    assert result.courses[0].course_name == MOCK_FILTER_COURSE_1["course_name"]
    # Assert structure and content instead of direct dict comparison
    reqs = result.courses[0].requirements
    expected_reqs = MOCK_FILTER_COURSE_1["requirements"]
    assert isinstance(reqs, dict)
    assert "CS" in reqs
    assert "IS" in reqs
    assert isinstance(reqs["CS"], list)
    assert len(reqs["CS"]) == 1
    assert reqs["CS"][0].requirement == expected_reqs["CS"][0]["requirement"]
    assert reqs["CS"][0].type == expected_reqs["CS"][0]["type"]
    assert reqs["CS"][0].major == expected_reqs["CS"][0]["major"]
    assert isinstance(reqs["IS"], list)
    assert len(reqs["IS"]) == 1
    assert reqs["IS"][0].requirement == expected_reqs["IS"][0]["requirement"]
    assert reqs["IS"][0].type == expected_reqs["IS"][0]["type"]
    assert reqs["IS"][0].major == expected_reqs["IS"][0]["major"]

    mock_course_repo.assert_called_once_with(db_session_mock)
    # Check that filters were called with default None values
    mock_repo_instance.get_courses_by_filters.assert_called_once_with(
        department=None,
        search_query=None,
        semester=None,
        has_prereqs=None,
        cs_requirement=None,
        is_requirement=None,
        ba_requirement=None,
        bs_requirement=None,
        offered_qatar=None,
        offered_pitts=None
    )


@patch('backend.services.courses.CourseRepository')
def test_fetch_courses_by_filters_with_filters(mock_course_repo, db_session_mock):
    """Test fetching courses with specific filters."""
    # Simulate repo returning only CS courses when filtered
    mock_courses_from_repo = [MOCK_FILTER_COURSE_1, MOCK_FILTER_COURSE_3]
    mock_repo_instance = mock_course_repo.return_value
    mock_repo_instance.get_courses_by_filters.return_value = mock_courses_from_repo

    service = CourseService(db=db_session_mock)
    filters = {
        "department": "CS",
        "semester": "F23",
        "has_prereqs": False, # Example filter
        "offered_qatar": True
    }
    result = service.fetch_courses_by_filters(**filters)

    assert isinstance(result, CourseListResponse)
    assert len(result.courses) == 2
    # Check sorting: 15-112, 15-213
    assert result.courses[0].course_code == "15-112"
    assert result.courses[1].course_code == "15-213"

    mock_course_repo.assert_called_once_with(db_session_mock)
    # Check that filters were passed correctly
    mock_repo_instance.get_courses_by_filters.assert_called_once_with(
        department="CS",
        search_query=None, # default
        semester="F23",
        has_prereqs=False,
        cs_requirement=None, # default
        is_requirement=None, # default
        ba_requirement=None, # default
        bs_requirement=None, # default
        offered_qatar=True,
        offered_pitts=None # default
    )

@patch('backend.services.courses.CourseRepository')
def test_fetch_courses_by_filters_prereqs_search_pitts(mock_course_repo, db_session_mock):
    """Test filters: has_prereqs=True, search_query, offered_pitts=True."""
    # Simulate repo returning course 3 when filtered
    mock_courses_from_repo = [MOCK_FILTER_COURSE_3]
    mock_repo_instance = mock_course_repo.return_value
    mock_repo_instance.get_courses_by_filters.return_value = mock_courses_from_repo

    service = CourseService(db=db_session_mock)
    filters = {
        "has_prereqs": True,
        "search_query": "Systems",
        "offered_pitts": True
    }
    result = service.fetch_courses_by_filters(**filters)

    assert isinstance(result, CourseListResponse)
    assert len(result.courses) == 1
    assert result.courses[0].course_code == "15-213"

    mock_course_repo.assert_called_once_with(db_session_mock)
    # Check that filters were passed correctly
    mock_repo_instance.get_courses_by_filters.assert_called_once_with(
        department=None,
        search_query="Systems",
        semester=None,
        has_prereqs=True,
        cs_requirement=None,
        is_requirement=None,
        ba_requirement=None,
        bs_requirement=None,
        offered_qatar=None,
        offered_pitts=True
    )

@patch('backend.services.courses.CourseRepository')
def test_fetch_courses_by_filters_major_requirements(mock_course_repo, db_session_mock):
    """Test filters: cs_requirement, is_requirement, ba_requirement, bs_requirement."""
    # Simulate repo returning course 1 when filtered by requirements
    mock_courses_from_repo = [MOCK_FILTER_COURSE_1]
    mock_repo_instance = mock_course_repo.return_value
    mock_repo_instance.get_courses_by_filters.return_value = mock_courses_from_repo

    service = CourseService(db=db_session_mock)
    # Using realistic-looking requirement strings
    filters = {
        "cs_requirement": "BS in Computer Science---SCS Electives",
        "is_requirement": "BS in Information Systems---Technical Core---Computer Science Requirement",
        "ba_requirement": "BS in Business Administration---Business Core",
        "bs_requirement": "BS in Biological Sciences---Chemistry---Modern Chemistry I"
    }
    result = service.fetch_courses_by_filters(**filters)

    assert isinstance(result, CourseListResponse)
    assert len(result.courses) == 1
    assert result.courses[0].course_code == "15-112" # Assuming repo mock returns this

    mock_course_repo.assert_called_once_with(db_session_mock)
    # Check that filters were passed correctly
    mock_repo_instance.get_courses_by_filters.assert_called_once_with(
        department=None,
        search_query=None,
        semester=None,
        has_prereqs=None,
        cs_requirement="BS in Computer Science---SCS Electives",
        is_requirement="BS in Information Systems---Technical Core---Computer Science Requirement",
        ba_requirement="BS in Business Administration---Business Core",
        bs_requirement="BS in Biological Sciences---Chemistry---Modern Chemistry I",
        offered_qatar=None,
        offered_pitts=None
    )

@patch('backend.services.courses.CourseRepository')
def test_fetch_courses_by_filters_qatar_false(mock_course_repo, db_session_mock):
    """Test filter: offered_qatar=False."""
    # Simulate repo returning course 3 (offered_qatar=False)
    mock_courses_from_repo = [MOCK_FILTER_COURSE_3]
    mock_repo_instance = mock_course_repo.return_value
    mock_repo_instance.get_courses_by_filters.return_value = mock_courses_from_repo

    service = CourseService(db=db_session_mock)
    filters = {
        "offered_qatar": False
    }
    result = service.fetch_courses_by_filters(**filters)

    assert isinstance(result, CourseListResponse)
    assert len(result.courses) == 1
    assert result.courses[0].course_code == "15-213"

    mock_course_repo.assert_called_once_with(db_session_mock)
    # Check that filters were passed correctly
    mock_repo_instance.get_courses_by_filters.assert_called_once_with(
        department=None,
        search_query=None,
        semester=None,
        has_prereqs=None,
        cs_requirement=None,
        is_requirement=None,
        ba_requirement=None,
        bs_requirement=None,
        offered_qatar=False,
        offered_pitts=None
    )

