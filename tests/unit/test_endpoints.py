"""
This script contains the test cases for the endpoints.
"""

from fastapi.testclient import TestClient
from backend.app.main import app
client = TestClient(app)

# ---------------------------
# Analytics Endpoints (from analytics router)
# ---------------------------

def test_analytics_course_coverage():
    """
    Test course coverage analytics
    """
    params = {"major": "CS", "semester": "F20"}
    response = client.get("/analytics/course-coverage", params=params)
    assert response.status_code in (200, 404)
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, dict)
        assert "major" in data
        assert "coverage" in data
        assert isinstance(data["coverage"], list)
        if data["coverage"]:

            assert isinstance(data["coverage"][0], dict)
            assert "requirement" in data["coverage"][0]
            assert "num_courses" in data["coverage"][0]
            assert isinstance(data["coverage"][0]["num_courses"], int)

def test_analytics_enrollment_data():
    """
    Test enrollment data analytics
    """
    params = {"course_code": "15122"}
    response = client.get("/analytics/enrollment-data", params=params)
    assert response.status_code in (200, 404)
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, dict)
        assert "enrollment_data" in data
        assert isinstance(data["enrollment_data"], list)
        if data["enrollment_data"]:

            assert isinstance(data["enrollment_data"][0], dict)
            assert "semester" in data["enrollment_data"][0]
            assert "enrollment_count" in data["enrollment_data"][0]
            assert "class_" in data["enrollment_data"][0]
            assert isinstance(data["enrollment_data"][0]["enrollment_count"], int)

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

# ---------------------------
# Departments Endpoint (from departments router)
# ---------------------------

def test_get_departments():
    """
    Test get departments endpoint
    """
    response = client.get("/departments")
    assert response.status_code in (200, 404)
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, dict)
        assert "departments" in data
        assert isinstance(data["departments"], list)
        if data["departments"]:
            dept = data["departments"][0]
            assert isinstance(dept, dict)
            assert "dep_code" in dept
            assert "name" in dept

# ---------------------------
# Requirements Endpoints (from requirements router)
# ---------------------------

def test_get_requirements():
    """
    Test get requirements endpoint
    """
    response = client.get("/requirements")
    assert response.status_code in (200, 404)
    if response.status_code == 200:
        data = response.json()

        assert isinstance(data, dict)
        assert "requirements" in data
        assert isinstance(data["requirements"], list)

        if data["requirements"]:
            req = data["requirements"][0]
            assert isinstance(req, dict)
            assert "requirement" in req
            assert "type" in req
            assert "major" in req
            assert isinstance(req["type"], bool)
