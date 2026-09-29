"""Tests for ``modules.bll.url_validation.url_category.UrlCategory``."""
from __future__ import annotations

from enum import Enum

import pytest

from modules.bll.url_validation.url_category import UrlCategory


@pytest.mark.unit
class TestUrlCategory:
    def test_is_an_enum(self) -> None:
        assert issubclass(UrlCategory, Enum)

    def test_exposes_exactly_the_four_documented_buckets(self) -> None:
        assert [member.name for member in UrlCategory] == ["VIDEO", "PLAYLIST", "UNSUPPORTED", "INVALID"]

    def test_members_are_distinct(self) -> None:
        assert len({member.value for member in UrlCategory}) == len(UrlCategory)

    def test_members_are_not_integer_comparable(self) -> None:
        assert UrlCategory.VIDEO != 1
