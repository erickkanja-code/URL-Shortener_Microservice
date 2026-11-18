"""Schemas for user data returned by the API."""

from pydantic import BaseModel, ConfigDict


class OwnerResponse(BaseModel):
    """The owner of a URL, as shown inside URL responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str