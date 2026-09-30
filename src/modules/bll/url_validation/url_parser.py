"""
Utilities for safely parsing user-submitted URLs.

Keeps syntax-level URL parsing separate from YouTube-specific
classification so malformed input cannot leak parser exceptions into
the validation flow.
"""

from __future__ import annotations

from typing import Optional
from urllib.parse import ParseResult, urlparse


def parse_url(raw_url: str) -> Optional[ParseResult]:
    """
    Parse a user-submitted URL without propagating ``urlparse`` failures.

    Surrounding whitespace is ignored and ``https://`` is added when no
    scheme separator is present. ``urllib.parse.urlparse`` raises
    ``ValueError`` for malformed netlocs such as unclosed IPv6 brackets
    or NFKC-invalid hostnames; those inputs are represented by ``None``
    so the validator can return a normal user-facing result.

    Args:
        raw_url (str): The URL exactly as typed/pasted by the user.

    Returns:
        Optional[ParseResult]: The parsed URL, or ``None`` when urllib
            rejects the URL's netloc.
    """
    url = (raw_url or "").strip()
    if "://" not in url:
        url = f"https://{url}"

    try:
        return urlparse(url)
    except ValueError:
        return None


def normalize_host(netloc: str) -> str:
    """
    Reduce a URL netloc to a bare, lowercase comparison host.

    Strips userinfo, a port, and the common ``www.``/``m.`` prefix so
    host classification can use exact/suffix comparisons without
    accepting lookalike domains.
    """
    host = netloc.rsplit("@", 1)[-1].split(":", 1)[0].lower()
    for prefix in ("www.", "m."):
        if host.startswith(prefix):
            return host[len(prefix):]
    return host
