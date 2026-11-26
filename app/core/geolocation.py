"""IP geolocation: turning a visitor's IP address into a city and country.

Uses the free ip-api.com service, which needs no API key. Its free plan
allows 45 requests per minute, only works over plain HTTP, and is meant for
non-commercial use; a production deployment would use a paid HTTPS plan or
a local database such as MaxMind GeoLite2.

A lookup must never break a redirect: any failure (timeout, network error,
rate limit, unexpected response) returns an unknown location instead.
"""

import ipaddress
from typing import NamedTuple

import httpx

GEOLOCATION_URL = "http://ip-api.com/json/{ip}"
GEOLOCATION_TIMEOUT_SECONDS = 2


class Location(NamedTuple):
    """Where an IP address is. Either field is None when unknown."""

    city: str | None
    country: str | None


UNKNOWN_LOCATION = Location(city=None, country=None)


def lookup_location(ip_address: str) -> Location:
    """Return the city and country of a public IP address.

    Private, local and invalid addresses are not looked up, since they
    belong to no country. Any failure returns UNKNOWN_LOCATION.
    """
    try:
        ip = ipaddress.ip_address(ip_address)
    except ValueError:
        return UNKNOWN_LOCATION

    if not ip.is_global:
        return UNKNOWN_LOCATION

    try:
        response = httpx.get(
            GEOLOCATION_URL.format(ip=ip_address),
            params={"fields": "status,country,city"},
            timeout=GEOLOCATION_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
    except (httpx.HTTPError, ValueError):
        return UNKNOWN_LOCATION

    if data.get("status") != "success":
        return UNKNOWN_LOCATION

    return Location(city=data.get("city") or None, country=data.get("country") or None)