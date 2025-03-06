from fastapi import APIRouter
import sqlite3

router = APIRouter()

def get_db_connection():
    conn = sqlite3.connect("database/gened_db.sqlite")
    conn.row_factory = sqlite3.Row
    return conn

@router.get("/requirements")
def get_requirements():
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT requirement, requirement AS audit_id FROM Requirement"
    requirements = cursor.execute(query).fetchall()
    conn.close()

    return [
        {"requirement": req["requirement"], "audit_id": req["audit_id"]} for req in requirements
    ]
