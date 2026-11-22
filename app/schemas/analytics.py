"""Schemas for the analytics endpoint."""

from datetime import date

from pydantic import BaseModel


class DailyClicks(BaseModel):
    """The number of clicks on one day."""

    day: date
    total_clicks: int


class CountryClicks(BaseModel):
    """The number of clicks from one country. `country` is None when unknown."""

    country: str | None
    total_clicks: int


class AnalyticsResponse(BaseModel):
    """Detailed analytics for one URL: a time series and a breakdown by country."""

    short_code: str
    total_clicks: int
    clicks_per_day: list[DailyClicks]
    clicks_per_country: list[CountryClicks]