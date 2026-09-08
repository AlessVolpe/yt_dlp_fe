"""
URL validation and classification for user-submitted download links.

Classifies a pasted URL against known YouTube link shapes *before* any
`yt-dlp` subprocess is spawned, so invalid, malformed, or deliberately
unsupported links (channels, Shorts, auth-gated playlists, ...) fail
fast with a clear message instead of surfacing as an opaque `yt-dlp`
error several seconds later.
"""

from __future__ import annotations

import re
from urllib.parse import ParseResult, parse_qs, urlparse

from bll.url_validation.url_category import UrlCategory
from bll.url_validation.validation_result import ValidationResult

# A YouTube video ID is exactly 11 characters drawn from this alphabet.
_VIDEO_ID = r"[A-Za-z0-9_-]{11}"

# Playlist IDs that reference a signed-in user's personal lists rather
# than a shareable playlist. The app has no authenticated session, so
# these can never be downloaded regardless of how the link is phrased.
_AUTH_ONLY_PLAYLISTS = frozenset({"WL", "LL"})

_YOUTU_BE_PATH_RE = re.compile(rf"^/({_VIDEO_ID})/?$")
_EMBED_PATH_RE = re.compile(rf"^/embed/({_VIDEO_ID})/?$")
_LIVE_PATH_RE = re.compile(rf"^/live/({_VIDEO_ID})/?$")
_SHORTS_PATH_RE = re.compile(r"^/shorts/")
_CHANNEL_PATH_RE = re.compile(r"^/(channel/|c/|user/|@)")
# Known non-content YouTube pages: search results, home feeds, and
# other browse surfaces that were never a single video or playlist.
_UNSUPPORTED_PAGE_RE = re.compile(
    r"^/(results|feed(/|$)|gaming|premium|movies|account|upload|clip/|post/|hashtag/)"
)


def validate_url(raw_url: str) -> ValidationResult:
    """
    Classify a user-submitted URL before it reaches `yt-dlp`.

    Args:
        raw_url (str): The URL exactly as typed/pasted by the user.

    Returns:
        ValidationResult: The classification, ready to drive both the
            download flow (`is_playlist`, `video_id`) and, on failure,
            the activity log (`error_message`).
    """
    url = (raw_url or "").strip()
    if not url:
        return ValidationResult(
            UrlCategory.INVALID,
            error_message="Paste a URL before starting a download."
        )

    if "://" not in url:
        url = f"https://{url}"

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return ValidationResult(
            UrlCategory.INVALID,
            error_message=f"'{raw_url}' is not a valid URL."
        )

    host = _normalize_host(parsed.netloc)

    if host == "youtu.be":
        return _classify_youtu_be(parsed, raw_url)

    if host == "youtube.com" or host.endswith(".youtube.com") or host == "youtube-nocookie.com":
        return _classify_youtube_host(parsed, raw_url)

    return ValidationResult(
        UrlCategory.INVALID,
        error_message=f"'{raw_url}' does not look like a YouTube link."
    )


def _normalize_host(netloc: str) -> str:
    """
    Reduce a URL's netloc to a bare, lowercase comparison host.

    Strips any userinfo/port and the common `www.`/`m.` prefix, so
    `WWW.YouTube.com:443` and `m.youtube.com` both normalize to
    `youtube.com`. Using an exact/suffix comparison against this
    normalized value (rather than a substring check) is what keeps
    lookalike hosts such as `youtube.com.evil.net` from validating.

    Args:
        netloc (str): The raw netloc component from `urlparse`.

    Returns:
        str: The normalized host.
    """
    host = netloc.rsplit("@", 1)[-1].split(":", 1)[0].lower()
    for prefix in ("www.", "m."):
        if host.startswith(prefix):
            return host[len(prefix):]
    return host


def _classify_youtu_be(parsed: ParseResult, raw_url: str) -> ValidationResult:
    """
    Classify a `youtu.be/<id>` short link.

    Args:
        parsed (ParseResult): The parsed URL.
        raw_url (str): The original URL, for error messages.

    Returns:
        ValidationResult: `PLAYLIST` (or an auth-only `UNSUPPORTED`)
            if a `list` query parameter is present, `VIDEO` if the
            path is a bare video ID, otherwise `INVALID`.
    """
    match = _YOUTU_BE_PATH_RE.match(parsed.path)
    if not match:
        return ValidationResult(
            UrlCategory.INVALID,
            error_message=f"'{raw_url}' is not a recognized YouTube video link."
        )

    playlist_id = parse_qs(parsed.query).get("list", [None])[0]
    if playlist_id:
        return _playlist_or_auth_error(playlist_id)

    return ValidationResult(UrlCategory.VIDEO, video_id=match.group(1))


def _classify_youtube_host(parsed: ParseResult, raw_url: str) -> ValidationResult:
    """
    Classify a URL on `youtube.com` or one of its subdomains.

    Args:
        parsed (ParseResult): The parsed URL.
        raw_url (str): The original URL, for error messages.

    Returns:
        ValidationResult: `UNSUPPORTED` for Shorts, channel pages, and
            other non-content pages; `PLAYLIST` (or an auth-only
            `UNSUPPORTED`) when a `list` parameter is present; `VIDEO`
            for a `/watch`, `/embed/<id>`, or `/live/<id>` link;
            `UNSUPPORTED` for anything else on the domain.
    """
    path = parsed.path

    if _SHORTS_PATH_RE.match(path):
        return ValidationResult(
            UrlCategory.UNSUPPORTED,
            error_message="YouTube Shorts are not supported."
        )

    if _CHANNEL_PATH_RE.match(path):
        return ValidationResult(
            UrlCategory.UNSUPPORTED,
            error_message="Channel links are not supported; paste a direct video or playlist link instead."
        )

    if _UNSUPPORTED_PAGE_RE.match(path):
        return ValidationResult(
            UrlCategory.UNSUPPORTED,
            error_message=f"'{raw_url}' is not a downloadable video or playlist."
        )

    query = parse_qs(parsed.query)
    playlist_id = query.get("list", [None])[0]
    if playlist_id:
        return _playlist_or_auth_error(playlist_id)

    if path.rstrip("/") == "/watch":
        video_id = query.get("v", [None])[0]
        if video_id and re.fullmatch(_VIDEO_ID, video_id):
            return ValidationResult(UrlCategory.VIDEO, video_id=video_id)
        return ValidationResult(
            UrlCategory.INVALID,
            error_message=f"'{raw_url}' is missing a valid video ID."
        )

    embed_match = _EMBED_PATH_RE.match(path)
    if embed_match:
        return ValidationResult(UrlCategory.VIDEO, video_id=embed_match.group(1))

    live_match = _LIVE_PATH_RE.match(path)
    if live_match:
        return ValidationResult(UrlCategory.VIDEO, video_id=live_match.group(1))

    return ValidationResult(
        UrlCategory.UNSUPPORTED,
        error_message=f"'{raw_url}' is not a downloadable video or playlist."
    )


def _playlist_or_auth_error(playlist_id: str) -> ValidationResult:
    """
    Classify a non-empty `list` query parameter.

    Args:
        playlist_id (str): The raw value of the `list` query
            parameter.

    Returns:
        ValidationResult: `UNSUPPORTED` for auth-only lists (Watch
            Later, Liked Videos), `PLAYLIST` otherwise.
    """
    if playlist_id in _AUTH_ONLY_PLAYLISTS:
        return ValidationResult(
            UrlCategory.UNSUPPORTED,
            error_message="'Watch Later' and 'Liked Videos' playlists require a signed-in session and aren't supported."
        )
    return ValidationResult(UrlCategory.PLAYLIST, is_playlist=True)
