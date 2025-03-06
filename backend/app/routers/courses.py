from fastapi import APIRouter, Query, HTTPException
import sqlite3
from typing import Optional

router = APIRouter()

def get_db_connection():
    conn = sqlite3.connect("database/gened_db.sqlite")
    conn.row_factory = sqlite3.Row
    return conn

@router.get("/courses/{course_code}")
def get_course(course_code: str):
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT c.course_code AS course_code, c.name AS course_name, c.dep_code AS department,
               c.units, c.offered_qatar, c.offered_pitts, c.description
        FROM Course c WHERE c.course_code = ?
    """
    course = cursor.execute(query, (course_code,)).fetchone()

    if not course:
        conn.close()
        raise HTTPException(status_code=404, detail="Course not found")

    # Get requirements
    requirements_query = """
        SELECT r.requirement, cf.requirement as audit_id
        FROM CountsFor cf
        JOIN Requirement r ON cf.requirement = r.requirement
        WHERE cf.course_code = ?
    """
    requirements = cursor.execute(requirements_query, (course_code,)).fetchall()

    conn.close()

    return {
        "course_code": course["course_code"],
        "course_name": course["course_name"],
        "department": course["department"],
        "units": course["units"],
        "offered_qatar": bool(course["offered_qatar"]),
        "offered_pitts": bool(course["offered_pitts"]),
        "description": course["description"],
        "requirements": {req["audit_id"]: req["requirement"] for req in requirements}
    }

@router.get("/courses")
def get_courses(
    department: Optional[str] = None,
    cs_requirement: Optional[str] = None,
    is_requirement: Optional[str] = None,
    ba_requirement: Optional[str] = None,
    bs_requirement: Optional[str] = None,
):
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT course_code, name FROM Course"
    conditions = []
    params = []

    if department:
        conditions.append("dep_code = ?")
        params.append(department)

    requirements = {
        "CS": cs_requirement,
        "IS": is_requirement,
        "BA": ba_requirement,
        "BS": bs_requirement
    }

    req_conditions = []
    req_params = []
    for major, req in requirements.items():
        if req:
            req_conditions.append("cf.requirement = ?")
            req_params.append(req)

    if req_conditions:
        query += " JOIN CountsFor cf ON Course.course_code = cf.course_code"
        conditions.extend(req_conditions)
        params.extend(req_params)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    courses = cursor.execute(query, params).fetchall()
    conn.close()

    return [
        {
            "course_code": course["course_code"],
            "course_name": course["name"]
        } for course in courses
    ]
