"""Tests for IP geolocation.

These tests never contact ip-api.com: `httpx.get` is replaced with a fake,
so they are fast, work offline, and do not depend on a third-party service.
"""

import httpx
import pytest

from app.core import geolocation
from app.core.geolocation import UNKNOWN_LOCATION, Location, lookup_location

PUBLIC_IP = "8.8.8.8"


def fake_response(json_body, status_code=200):
    """Return a function that stands in for httpx.get and answers with this response."""

    def fake_get(url, **kwargs):
        return httpx.Response(status_code, json=json_body, request=httpx.Request("GET", url))

    return fake_get


def test_lookup_returns_city_and_country(monkeypatch):
    monkeypatch.setattr(
        geolocation.httpx,
        "get",
        fake_response({"status": "success", "country": "Rwanda", "city": "Kigali"}),
    )

    assert lookup_location(PUBLIC_IP) == Location(city="Kigali", country="Rwanda")


def test_lookup_asks_the_service_about_the_right_ip(monkeypatch):
    requested_urls = []

    def recording_get(url, **kwargs):
        requested_urls.append(url)
        return httpx.Response(
            200, json={"status": "success", "country": "Rwanda", "city": "Kigali"},
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(geolocation.httpx, "get", recording_get)

    lookup_location(PUBLIC_IP)

    assert requested_urls == [f"http://ip-api.com/json/{PUBLIC_IP}"]


@pytest.mark.parametrize(
    "ip_address",
    ["127.0.0.1", "192.168.1.10", "10.0.0.5", "172.18.0.1", "::1", "0.0.0.0", "not-an-ip"],
)
def test_lookup_skips_addresses_that_have_no_location(monkeypatch, ip_address):
    def fail_if_called(url, **kwargs):
        raise AssertionError("the geolocation service should not be called")

    monkeypatch.setattr(geolocation.httpx, "get", fail_if_called)

    assert lookup_location(ip_address) == UNKNOWN_LOCATION


def test_lookup_returns_unknown_when_the_service_reports_failure(monkeypatch):
    monkeypatch.setattr(
        geolocation.httpx, "get", fake_response({"status": "fail", "message": "reserved range"})
    )

    assert lookup_location(PUBLIC_IP) == UNKNOWN_LOCATION


def test_lookup_returns_unknown_when_rate_limited(monkeypatch):
    monkeypatch.setattr(geolocation.httpx, "get", fake_response({}, status_code=429))

    assert lookup_location(PUBLIC_IP) == UNKNOWN_LOCATION


def test_lookup_returns_unknown_when_the_service_is_unreachable(monkeypatch):
    def unreachable(url, **kwargs):
        raise httpx.ConnectError("cannot connect")

    monkeypatch.setattr(geolocation.httpx, "get", unreachable)

    assert lookup_location(PUBLIC_IP) == UNKNOWN_LOCATION


def test_lookup_returns_unknown_when_the_service_times_out(monkeypatch):
    def too_slow(url, **kwargs):
        raise httpx.ReadTimeout("took too long")

    monkeypatch.setattr(geolocation.httpx, "get", too_slow)

    assert lookup_location(PUBLIC_IP) == UNKNOWN_LOCATION


def test_lookup_returns_unknown_for_a_response_that_is_not_json(monkeypatch):
    def not_json(url, **kwargs):
        return httpx.Response(200, text="<html>oops</html>", request=httpx.Request("GET", url))

    monkeypatch.setattr(geolocation.httpx, "get", not_json)

    assert lookup_location(PUBLIC_IP) == UNKNOWN_LOCATION


def test_lookup_treats_empty_fields_as_unknown(monkeypatch):
    monkeypatch.setattr(
        geolocation.httpx, "get", fake_response({"status": "success", "country": "Rwanda", "city": ""})
    )

    assert lookup_location(PUBLIC_IP) == Location(city=None, country="Rwanda")