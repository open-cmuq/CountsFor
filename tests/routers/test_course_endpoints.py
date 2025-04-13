# pylint: disable=missing-module-docstring
"""
This script contains the test cases for the courses endpoints.
"""

from fastapi.testclient import TestClient
from backend.app.main import app
client = TestClient(app)

# ---------------------------
# Courses Endpoints (from courses router)
# ---------------------------

def test_search_courses():
    """
    Test course search endpoint
    """
    params = {
        "department": "CS",
        "semester": "F20",
    }
    response = client.get("/courses/search", params=params)
    # Expect 200 if matching courses found, 404 otherwise
    assert response.status_code in (200, 404), f"Search failed ({response.status_code}): {response.text[:100]}"
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, dict)
        assert "courses" in data
        assert isinstance(data["courses"], list)
        if data["courses"]:
            course = data["courses"][0]
            assert isinstance(course, dict)

            assert "course_code" in course
            assert "course_name" in course
            assert "department" in course
            assert "units" in course
            assert "description" in course
            assert "prerequisites" in course
            assert "offered" in course
            assert isinstance(course["offered"], list)
            assert "offered_qatar" in course
            assert "offered_pitts" in course
            assert "requirements" in course
            assert isinstance(course["requirements"], dict)
            if "department" in params:
                assert course.get("department") == params["department"]

def test_get_all_semesters():
    """
    Test get all semesters endpoint
    """
    response = client.get("/courses/semesters")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "semesters" in data
    assert isinstance(data["semesters"], list)
    if data["semesters"]:
        assert isinstance(data["semesters"][0], str)

def test_get_course_by_code():
    """
    Test get course by code endpoint
    """
    course_code_to_test = "15122"
    response = client.get(f"/courses/{course_code_to_test}")
    assert response.status_code in (200, 404)
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, dict)
        assert "course_code" in data
        assert "course_name" in data
        assert "department" in data
        assert "units" in data
        assert "description" in data
        assert "prerequisites" in data
        assert "offered" in data
        assert isinstance(data["offered"], list)
        assert "offered_qatar" in data
        assert "offered_pitts" in data
        assert "requirements" in data
        assert isinstance(data["requirements"], dict)
        assert data["course_code"] == course_code_to_test
