"""
Result object returned by URL validation/classification.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from modules.bll.url_validation.url_category import UrlCategory


@dataclass(frozen=True)
class ValidationResult:
    """
    The outcome of validating and classifying a submitted URL.

    Attributes:
        category (UrlCategory): The classification assigned to the URL.
        is_playlist (bool): Whether the download should run in
            playlist mode. Only ever True for `UrlCategory.PLAYLIST`.
        video_id (Optional[str]): The 11-character YouTube video ID
            extracted from the URL, populated when `category` is
            `VIDEO`. None otherwise.
        error_message (Optional[str]): A human-readable explanation
            suitable for display in the activity log. None when the
            URL is valid (`VIDEO` or `PLAYLIST`).
    """

    category: UrlCategory
    is_playlist: bool = False
    video_id: Optional[str] = None
    error_message: Optional[str] = None

    @property
    def is_valid(self) -> bool:
        """
        Whether this URL can be handed off to `yt-dlp`.

        Returns:
            bool: True for `VIDEO` and `PLAYLIST` categories, False
                for `UNSUPPORTED` and `INVALID`.
        """
        return self.category in (UrlCategory.VIDEO, UrlCategory.PLAYLIST)
