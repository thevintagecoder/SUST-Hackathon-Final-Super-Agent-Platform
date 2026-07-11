"""Request and response schemas for Agents."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AgentCreate(BaseModel):
    """Data accepted when creating a simulated Agent."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

    code: str = Field(
        min_length=3,
        max_length=50,
        pattern=r"^[A-Z0-9-]+$",
    )
    name: str = Field(
        min_length=2,
        max_length=100,
    )
    area: str = Field(
        min_length=2,
        max_length=100,
    )


class AgentResponse(BaseModel):
    """Data returned after reading an Agent ORM object."""

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    code: str
    name: str
    area: str
    is_active: bool
    created_at: datetime