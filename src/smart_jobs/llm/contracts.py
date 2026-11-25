from typing import Protocol

from pydantic import BaseModel, Field


class ExtractedRequirements(BaseModel):
    required: list[str] = Field(default_factory=list)
    desirable: list[str] = Field(default_factory=list)
    unknown: list[str] = Field(default_factory=list)


class LLMAdapter(Protocol):
    def extract_requirements(self, description: str) -> ExtractedRequirements:
        """Extract a structured requirement schema without changing rules."""
        ...
