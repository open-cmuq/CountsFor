"""
this script implements the data access layer for requirements.
"""

from sqlalchemy.orm import Session
from backend.database.models import Requirement, Audit

class RequirementRepository:
    """Encapsulates all database operations for requirements."""

    def __init__(self, db: Session):
        self.db = db

    def get_all_requirements(self):
        """Fetch all requirements with their corresponding type and major."""
        requirements = (
            self.db.query(Requirement.requirement, Audit.type, Audit.major)
            .join(Audit, Requirement.audit_id == Audit.audit_id)
            .all()
        )

        return [
            {
                "requirement": requirement,
                "type": bool(audit_type),  # Ensure `type` remains a boolean
                "major": major
            }
            for requirement, audit_type, major in requirements
        ]

    def search_requirements(self, query: str):
        """Search for requirements by a keyword."""
        query = f"%{query}%"
        requirements = (
            self.db.query(Requirement.requirement, Audit.type, Audit.major)
            .join(Audit, Requirement.audit_id == Audit.audit_id)
            .filter(Requirement.requirement.ilike(query))
            .all()
        )

        return [
            {
                "requirement": requirement,
                "type": bool(audit_type),
                "major": major
            }
            for requirement, audit_type, major in requirements
        ]
