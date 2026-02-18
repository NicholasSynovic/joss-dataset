import re
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field


class NormalIssue(BaseModel):
    """Normalized representation of an issue."""

    model_config = ConfigDict(populate_by_name=True)

    body: str = Field(..., alias="Body")
    closed_at: int = Field(..., alias="Closed At")  # unix seconds; 0 if open
    created_at: int = Field(..., alias="Created At")  # unix seconds
    issue_number: int = Field(..., alias="Issue Number")
    json_str: str = Field(..., alias="JSON")
    labels: list[str] = Field(default_factory=list, alias="Labels")
