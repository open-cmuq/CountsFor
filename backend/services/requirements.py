from typing import Optional
from sqlalchemy.orm import Session
from backend.repository.requirements import RequirementRepository
from backend.app.schemas import RequirementResponse, RequirementsResponse

class RequirementService:
    """encapsulates business logic for handling requirements."""

    def __init__(self, db: Session):
        self.requirement_repo = RequirementRepository(db)

    def fetch_requirement(self, requirement_name: str) -> Optional[RequirementResponse]:
        """fetch and return a single requirement with type and major."""
        requirement = self.requirement_repo.get_requirement(requirement_name)
        if not requirement:
            return None

        return RequirementResponse(
            requirement=requirement["requirement"],
            type=requirement["type"],
            major=requirement["major"]
        )

    def fetch_all_requirements(self) -> RequirementsResponse:
        """fetch and structure all requirements."""
        requirements = self.requirement_repo.get_all_requirements()

        structured_requirements = [
            RequirementResponse(
                requirement=req["requirement"],
                type=req["type"],
                major=req["major"]
            )
            for req in requirements
        ]

        return RequirementsResponse(requirements=structured_requirements)
