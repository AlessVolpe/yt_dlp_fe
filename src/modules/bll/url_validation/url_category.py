"""
Classification bucket assigned to a submitted download URL.
"""

from enum import Enum, auto


class UrlCategory(Enum):
    """
    Classification bucket assigned to a submitted URL.

    Attributes:
        VIDEO: A single downloadable video (or livestream/embed) URL.
        PLAYLIST: A URL referencing a shareable playlist; downloading
            should proceed in playlist mode automatically.
        UNSUPPORTED: A recognized YouTube URL shape the app
            deliberately does not support (channels, Shorts, auth-only
            playlists, non-content pages, ...).
        INVALID: A URL that is empty, malformed, or does not point to
            a YouTube resource at all.
    """

    VIDEO = auto()
    PLAYLIST = auto()
    UNSUPPORTED = auto()
    INVALID = auto()
