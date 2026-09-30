"""Tests for ``modules.bll.url_validation.url_parser``."""
from __future__ import annotations

import pytest

from modules.bll.url_validation.url_parser import normalize_host, parse_url

VID = "dQw4w9WgXcQ"


@pytest.mark.unit
class TestParseUrl:
    def test_adds_https_when_scheme_is_missing(self) -> None:
        parsed = parse_url(f"youtube.com/watch?v={VID}")

        assert parsed is not None
        assert parsed.scheme == "https"
        assert parsed.netloc == "youtube.com"

    def test_preserves_an_explicit_scheme(self) -> None:
        parsed = parse_url(f"http://youtube.com/watch?v={VID}")

        assert parsed is not None
        assert parsed.scheme == "http"
        assert parsed.netloc == "youtube.com"

    @pytest.mark.parametrize(
        "url",
        [
            "https://[abc",
            "http://[::1",
            "[",
            "https://youtube.com[/watch?v=" + VID,
            "https://\u2100.com",
        ],
        ids=[
            "unclosed-bracket",
            "unclosed-ipv6",
            "lone-bracket",
            "bracket-after-host",
            "nfkc-invalid-netloc",
        ],
    )
    def test_malformed_netloc_returns_none(self, url: str) -> None:
        assert parse_url(url) is None


@pytest.mark.unit
class TestNormalizeHost:
    @pytest.mark.parametrize(
        ("netloc", "expected"),
        [
            ("youtube.com", "youtube.com"),
            ("WWW.YouTube.com:443", "youtube.com"),
            ("m.youtube.com", "youtube.com"),
            ("user:pw@www.youtube.com", "youtube.com"),
            ("music.youtube.com", "music.youtube.com"),
            ("youtu.be", "youtu.be"),
            ("www.m.youtube.com", "m.youtube.com"),
            ("evil.com@youtube.com", "youtube.com"),
            ("youtube.com@evil.com", "evil.com"),
            ("", ""),
        ],
    )
    def test_reduces_to_bare_lowercase_host(self, netloc: str, expected: str) -> None:
        assert normalize_host(netloc) == expected
