"""The public redirect endpoint, GET /{short_code}/.

It lives outside /api/v1 on purpose: short links are shared and saved
everywhere, so this path must never change between API versions.
"""

import ipaddress

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from app.api.deps import SessionDep
from app.services import url as url_service

router = APIRouter(tags=["Redirect"])


def get_client_ip(request: Request) -> str:
    """Return the visitor's IP address, or "0.0.0.0" if it is missing or invalid.

    The clicks table stores IPs in a Postgres INET column, which rejects
    invalid values. Falling back keeps a bad value from crashing the redirect.
    """
    host = request.client.host if request.client else ""
    try:
        ipaddress.ip_address(host)
        return host
    except ValueError:
        return "0.0.0.0"


@router.get("/{short_code}/")
def redirect_to_original(short_code: str, request: Request, db: SessionDep):
    """Redirect to the original URL with a 302 and record the click.

    302 (temporary) is used instead of 301 because browsers cache 301
    permanently, which would skip this server on later visits: clicks would
    go unrecorded and deactivated links would keep working.
    """
    original_url = url_service.resolve_short_code(
        db,
        short_code,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent", ""),
        referrer=request.headers.get("referer"),
    )
    return RedirectResponse(url=original_url, status_code=302)