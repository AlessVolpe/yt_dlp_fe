"""Tests for ``modules.bll.url_validation.url_validator``.

Coverage strategy:

* exhaustive example tables for every accepted, unsupported and invalid URL
  shape (including host-spoofing attempts),
* structural invariants of `ValidationResult` checked over all examples,
* property-based tests (Hypothesis) for totality and ID handling.
"""
from __future__ import annotations

import re
from typing import Any, Dict, Mapping

import pytest
from hypothesis import given, strategies as st

from modules.bll.url_validation.url_category import UrlCategory
from modules.bll.url_validation.url_validator import validate_url
from modules.bll.url_validation.validation_result import ValidationResult

VID = "dQw4w9WgXcQ"
PLAYLIST_ID = "PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf"
ID_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-"
ID_PATTERN = re.compile(r"[A-Za-z0-9_-]{11}")


def cases(mapping: Mapping[str, Any]) -> list:
    """Convert ``{id: value_or_tuple}`` into ``pytest.param`` entries."""
    return [pytest.param(*(v if isinstance(v, tuple) else (v,)), id=k) for k, v in mapping.items()]


VIDEO_URLS: Dict[str, Any] = {
    "watch-canonical": (f"https://www.youtube.com/watch?v={VID}", VID),
    "watch-no-www": (f"https://youtube.com/watch?v={VID}", VID),
    "watch-http": (f"http://www.youtube.com/watch?v={VID}", VID),
    "watch-no-scheme": (f"youtube.com/watch?v={VID}", VID),
    "watch-www-no-scheme": (f"www.youtube.com/watch?v={VID}", VID),
    "watch-mobile": (f"https://m.youtube.com/watch?v={VID}", VID),
    "watch-music-subdomain": (f"https://music.youtube.com/watch?v={VID}", VID),
    "watch-uppercase-host": (f"https://WWW.YouTube.COM/watch?v={VID}", VID),
    "watch-explicit-port": (f"https://www.youtube.com:443/watch?v={VID}", VID),
    "watch-trailing-slash": (f"https://www.youtube.com/watch/?v={VID}", VID),
    "watch-extra-params-first": (f"https://www.youtube.com/watch?feature=share&v={VID}&t=42s", VID),
    "watch-surrounding-whitespace": (f"  https://www.youtube.com/watch?v={VID}  \n", VID),
    "watch-userinfo-prefix": (f"https://user:pw@www.youtube.com/watch?v={VID}", VID),
    "watch-empty-list-ignored": (f"https://www.youtube.com/watch?v={VID}&list=", VID),
    "watch-index-only": (f"https://www.youtube.com/watch?v={VID}&index=2", VID),
    "watch-id-with-dash-underscore": ("https://www.youtube.com/watch?v=-_-_-_-_-_-", "-_-_-_-_-_-"),
    "short-link": (f"https://youtu.be/{VID}", VID),
    "short-link-no-scheme": (f"youtu.be/{VID}", VID),
    "short-link-trailing-slash": (f"https://youtu.be/{VID}/", VID),
    "short-link-timestamp": (f"https://youtu.be/{VID}?t=30", VID),
    "short-link-www": (f"https://www.youtu.be/{VID}", VID),
    "short-link-uppercase-host": (f"https://YOUTU.BE/{VID}", VID),
    "embed": (f"https://www.youtube.com/embed/{VID}", VID),
    "embed-trailing-slash": (f"https://www.youtube.com/embed/{VID}/", VID),
    "embed-nocookie": (f"https://www.youtube-nocookie.com/embed/{VID}", VID),
    "live": (f"https://www.youtube.com/live/{VID}", VID),
    "live-with-query": (f"https://www.youtube.com/live/{VID}?feature=share", VID),
}

PLAYLIST_URLS: Dict[str, str] = {
    "playlist-page": f"https://www.youtube.com/playlist?list={PLAYLIST_ID}",
    "playlist-no-scheme": f"youtube.com/playlist?list={PLAYLIST_ID}",
    "playlist-music-subdomain": "https://music.youtube.com/playlist?list=OLAK5uy_abcdefghijk",
    "watch-with-list": f"https://www.youtube.com/watch?v={VID}&list={PLAYLIST_ID}",
    "watch-with-list-and-index": f"https://www.youtube.com/watch?v={VID}&list={PLAYLIST_ID}&index=4",
    "short-link-with-list": f"https://youtu.be/{VID}?list={PLAYLIST_ID}",
    "embed-with-list": f"https://www.youtube.com/embed/{VID}?list={PLAYLIST_ID}",
    "live-with-list": f"https://www.youtube.com/live/{VID}?list={PLAYLIST_ID}",
    "mix-playlist": f"https://www.youtube.com/watch?v={VID}&list=RD{VID}",
    "list-before-video": f"https://www.youtube.com/watch?list={PLAYLIST_ID}&v={VID}",
}

AUTH_ONLY_URLS: Dict[str, str] = {
    "playlist-watch-later": "https://www.youtube.com/playlist?list=WL",
    "playlist-liked": "https://www.youtube.com/playlist?list=LL",
    "watch-with-watch-later": f"https://www.youtube.com/watch?v={VID}&list=WL",
    "short-link-with-liked": f"https://youtu.be/{VID}?list=LL",
}

UNSUPPORTED_URLS: Dict[str, Any] = {
    "shorts": (f"https://www.youtube.com/shorts/{VID}", "YouTube Shorts are not supported."),
    "shorts-with-list": (f"https://www.youtube.com/shorts/{VID}?list={PLAYLIST_ID}", "Shorts"),
    "channel-id": ("https://www.youtube.com/channel/UCabcdefghijklmnopqrstuv", "Channel links"),
    "channel-custom": ("https://www.youtube.com/c/SomeChannel", "Channel links"),
    "channel-legacy-user": ("https://www.youtube.com/user/SomeUser", "Channel links"),
    "channel-handle": ("https://www.youtube.com/@handle", "Channel links"),
    "channel-handle-videos": ("https://www.youtube.com/@handle/videos", "Channel links"),
    "search-results": ("https://www.youtube.com/results?search_query=lofi", "not a downloadable"),
    "feed-subscriptions": ("https://www.youtube.com/feed/subscriptions", "not a downloadable"),
    "feed-root": ("https://www.youtube.com/feed", "not a downloadable"),
    "gaming": ("https://www.youtube.com/gaming", "not a downloadable"),
    "premium": ("https://www.youtube.com/premium", "not a downloadable"),
    "movies": ("https://www.youtube.com/movies", "not a downloadable"),
    "account": ("https://www.youtube.com/account", "not a downloadable"),
    "upload": ("https://www.youtube.com/upload", "not a downloadable"),
    "clip": ("https://www.youtube.com/clip/UgkxAbCdEfGh", "not a downloadable"),
    "community-post": ("https://www.youtube.com/post/UgxAbCdEfGh", "not a downloadable"),
    "hashtag": ("https://www.youtube.com/hashtag/music", "not a downloadable"),
    "feed-with-list-param": (f"https://www.youtube.com/feed/history?list={PLAYLIST_ID}", "not a downloadable"),
    "domain-root": ("https://www.youtube.com/", "not a downloadable"),
    "bare-domain": ("https://www.youtube.com", "not a downloadable"),
    "unknown-path": ("https://www.youtube.com/somethingelse", "not a downloadable"),
    "embed-without-id": ("https://www.youtube.com/embed/", "not a downloadable"),
    "embed-short-id": ("https://www.youtube.com/embed/short", "not a downloadable"),
    "live-short-id": ("https://www.youtube.com/live/short", "not a downloadable"),
}

INVALID_URLS: Dict[str, Any] = {
    "empty": ("", "Paste a URL"),
    "spaces-only": ("    ", "Paste a URL"),
    "whitespace-mix": ("\n\t \r", "Paste a URL"),
    "unsupported-scheme-ftp": (f"ftp://www.youtube.com/watch?v={VID}", "is not a valid URL"),
    "unsupported-scheme-file": ("file:///etc/passwd", "is not a valid URL"),
    "scheme-without-host": ("https://", "is not a valid URL"),
    "triple-slash-no-host": (f"http:///watch?v={VID}", "is not a valid URL"),
    "bare-separator": ("://", "is not a valid URL"),
    "other-site": ("https://vimeo.com/12345", "does not look like a YouTube link"),
    "other-site-same-shape": (f"https://example.com/watch?v={VID}", "does not look like a YouTube link"),
    "plain-text": ("not a url", "does not look like a YouTube link"),
    "bare-video-id": (VID, "does not look like a YouTube link"),
    "javascript-pseudo-url": ("javascript:alert(1)", "does not look like a YouTube link"),
    "spoof-subdomain-suffix": (f"https://www.youtube.com.evil.net/watch?v={VID}", "does not look like a YouTube link"),
    "spoof-prefix": (f"https://evilyoutube.com/watch?v={VID}", "does not look like a YouTube link"),
    "spoof-short-prefix": (f"https://notyoutu.be/{VID}", "does not look like a YouTube link"),
    "spoof-short-suffix": (f"https://youtu.be.evil.net/{VID}", "does not look like a YouTube link"),
    "spoof-userinfo": (f"https://youtube.com@evil.com/watch?v={VID}", "does not look like a YouTube link"),
    "spoof-userinfo-port": (f"https://youtube.com:80@evil.com/watch?v={VID}", "does not look like a YouTube link"),
    "spoof-in-query": (f"https://evil.com/?u=https://youtube.com/watch?v={VID}", "does not look like a YouTube link"),
    "spoof-in-path": (f"https://evil.com/youtube.com/watch?v={VID}", "does not look like a YouTube link"),
    "nocookie-subdomain": (f"https://sub.youtube-nocookie.com/embed/{VID}", "does not look like a YouTube link"),
    "short-link-subdomain": (f"https://music.youtu.be/{VID}", "does not look like a YouTube link"),
    "short-link-id-too-short": ("https://youtu.be/short", "not a recognized YouTube video link"),
    "short-link-id-too-long": ("https://youtu.be/dQw4w9WgXcQx", "not a recognized YouTube video link"),
    "short-link-id-bad-char": ("https://youtu.be/dQw4w9WgXc!", "not a recognized YouTube video link"),
    "short-link-empty-path": ("https://youtu.be/", "not a recognized YouTube video link"),
    "short-link-extra-segment": (f"https://youtu.be/{VID}/extra", "not a recognized YouTube video link"),
    "watch-without-id": ("https://www.youtube.com/watch", "missing a valid video ID"),
    "watch-empty-id": ("https://www.youtube.com/watch?v=", "missing a valid video ID"),
    "watch-id-too-short": ("https://www.youtube.com/watch?v=short", "missing a valid video ID"),
    "watch-id-too-long": (f"https://www.youtube.com/watch?v={VID}extra", "missing a valid video ID"),
    "watch-id-bad-char": ("https://www.youtube.com/watch?v=dQw4w9WgX!Q", "missing a valid video ID"),
}


def assert_invariants(result: ValidationResult) -> None:
    """Structural contract shared by every `ValidationResult` the validator returns."""
    assert isinstance(result, ValidationResult)
    assert isinstance(result.category, UrlCategory)
    assert result.is_playlist is (result.category is UrlCategory.PLAYLIST)
    if result.is_valid:
        assert result.error_message is None
        assert (result.video_id is not None) is (result.category is UrlCategory.VIDEO)
        if result.video_id is not None:
            assert ID_PATTERN.fullmatch(result.video_id)
    else:
        assert isinstance(result.error_message, str) and result.error_message
        assert result.video_id is None


def _all_string_inputs() -> list:
    urls = [u for u, _ in VIDEO_URLS.values()]
    urls += list(PLAYLIST_URLS.values()) + list(AUTH_ONLY_URLS.values())
    urls += [u for u, _ in UNSUPPORTED_URLS.values()] + [u for u, _ in INVALID_URLS.values()]
    return urls


@pytest.mark.unit
class TestAcceptedVideos:
    @pytest.mark.parametrize(("url", "video_id"), cases(VIDEO_URLS))
    def test_classified_as_video_with_extracted_id(self, url: str, video_id: str) -> None:
        result = validate_url(url)
        assert result.category is UrlCategory.VIDEO
        assert result.video_id == video_id
        assert result.is_playlist is False
        assert result.error_message is None


@pytest.mark.unit
class TestPlaylists:
    @pytest.mark.parametrize("url", cases(PLAYLIST_URLS))
    def test_classified_as_playlist(self, url: str) -> None:
        result = validate_url(url)
        assert result.category is UrlCategory.PLAYLIST
        assert result.is_playlist is True
        assert result.video_id is None
        assert result.is_valid

    @pytest.mark.parametrize("url", cases(AUTH_ONLY_URLS))
    def test_auth_gated_lists_are_unsupported(self, url: str) -> None:
        result = validate_url(url)
        assert result.category is UrlCategory.UNSUPPORTED
        assert "Watch Later" in (result.error_message or "")
        assert not result.is_valid and not result.is_playlist

    def test_only_exact_uppercase_auth_ids_are_gated(self) -> None:
        assert validate_url("https://www.youtube.com/playlist?list=WL2").category is UrlCategory.PLAYLIST


@pytest.mark.unit
class TestUnsupported:
    @pytest.mark.parametrize(("url", "fragment"), cases(UNSUPPORTED_URLS))
    def test_classified_as_unsupported_with_explanation(self, url: str, fragment: str) -> None:
        result = validate_url(url)
        assert result.category is UrlCategory.UNSUPPORTED
        assert fragment in (result.error_message or "")
        assert not result.is_valid

    def test_shorts_take_precedence_over_playlist_parameter(self) -> None:
        url = f"https://www.youtube.com/shorts/{VID}?list={PLAYLIST_ID}"
        assert validate_url(url).category is UrlCategory.UNSUPPORTED


@pytest.mark.unit
class TestInvalid:
    @pytest.mark.parametrize(("url", "fragment"), cases(INVALID_URLS))
    def test_classified_as_invalid_with_explanation(self, url: str, fragment: str) -> None:
        result = validate_url(url)
        assert result.category is UrlCategory.INVALID
        assert fragment in (result.error_message or "")
        assert not result.is_valid

    def test_none_is_treated_as_empty_input(self) -> None:
        result = validate_url(None)  # type: ignore[arg-type]
        assert result.category is UrlCategory.INVALID
        assert "Paste a URL" in (result.error_message or "")

    @pytest.mark.parametrize(
        "url",
        [u for u, fragment in INVALID_URLS.values() if "Paste a URL" not in fragment],
    )
    def test_error_messages_quote_the_input_as_typed(self, url: str) -> None:
        assert url in (validate_url(url).error_message or "")


@pytest.mark.unit
class TestMalformedNetlocs:
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
    def test_reported_as_invalid_instead_of_raising(self, url: str) -> None:
        result = validate_url(url)

        assert result.category is UrlCategory.INVALID
        assert url in (result.error_message or "")
        assert not result.is_valid


@pytest.mark.unit
class TestInvariants:
    @pytest.mark.parametrize("url", _all_string_inputs())
    def test_every_example_satisfies_result_invariants(self, url: str) -> None:
        assert_invariants(validate_url(url))

    @pytest.mark.parametrize("url", _all_string_inputs())
    def test_validation_is_idempotent_and_side_effect_free(self, url: str) -> None:
        assert validate_url(url) == validate_url(url)

    @pytest.mark.parametrize("url", [u for u, _ in VIDEO_URLS.values()])
    def test_surrounding_whitespace_never_changes_the_classification(self, url: str) -> None:
        assert validate_url(f" \t{url}\n ") == validate_url(url.strip())


@pytest.mark.unit
class TestProperties:
    @given(st.text(alphabet=st.characters(codec="ascii")))
    def test_total_over_ascii_text(self, raw: str) -> None:
        assert_invariants(validate_url(raw))

    @given(st.text(alphabet=ID_ALPHABET, min_size=11, max_size=11))
    def test_every_well_formed_id_is_accepted_on_all_host_shapes(self, video_id: str) -> None:
        for url in (
            f"https://www.youtube.com/watch?v={video_id}",
            f"https://youtu.be/{video_id}",
            f"https://www.youtube.com/embed/{video_id}",
            f"https://www.youtube.com/live/{video_id}",
        ):
            result = validate_url(url)
            assert result.category is UrlCategory.VIDEO
            assert result.video_id == video_id

    @given(st.text(alphabet=ID_ALPHABET, max_size=20).filter(lambda s: len(s) != 11))
    def test_ids_of_the_wrong_length_are_never_videos(self, video_id: str) -> None:
        for url in (f"https://www.youtube.com/watch?v={video_id}", f"https://youtu.be/{video_id}"):
            assert validate_url(url).category is not UrlCategory.VIDEO

    @given(st.text(alphabet=ID_ALPHABET, min_size=1, max_size=40), st.sampled_from(["youtube.com", "youtu.be"]))
    def test_hosts_embedding_a_trusted_name_but_not_ending_in_it_are_rejected(self, label: str, trusted: str) -> None:
        url = f"https://{trusted}.{label.lower()}.example/watch?v={VID}"
        assert validate_url(url).category is UrlCategory.INVALID
