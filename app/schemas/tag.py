"""Schemas for tag data returned by the API."""

from pydantic import BaseModel, ConfigDict


class TagResponse(BaseModel):
    """A tag, as shown inside URL responses."""

    model_config = ConfigDict(from_attributes=True)

    name: str