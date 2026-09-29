"""Tests for ``modules.bll.url_validation.validation_result.ValidationResult``."""
from __future__ import annotations

import dataclasses

import pytest

from modules.bll.url_validation.url_category import UrlCategory
from modules.bll.url_validation.validation_result import ValidationResult


@pytest.mark.unit
class TestValidationResult:
    def test_optional_fields_default_to_neutral_values(self) -> None:
        result = ValidationResult(UrlCategory.INVALID)
        assert (result.is_playlist, result.video_id, result.error_message) == (False, None, None)

    @pytest.mark.parametrize(
        ("category", "expected"),
        [
            (UrlCategory.VIDEO, True),
            (UrlCategory.PLAYLIST, True),
            (UrlCategory.UNSUPPORTED, False),
            (UrlCategory.INVALID, False),
        ],
    )
    def test_is_valid_reflects_category(self, category: UrlCategory, expected: bool) -> None:
        assert ValidationResult(category).is_valid is expected

    def test_is_frozen(self) -> None:
        result = ValidationResult(UrlCategory.VIDEO, video_id="dQw4w9WgXcQ")
        with pytest.raises(dataclasses.FrozenInstanceError):
            result.video_id = "other"  # type: ignore[misc]

    def test_value_equality_and_hashing(self) -> None:
        first = ValidationResult(UrlCategory.PLAYLIST, is_playlist=True)
        second = ValidationResult(UrlCategory.PLAYLIST, is_playlist=True)
        assert first == second
        assert hash(first) == hash(second)

    def test_is_valid_is_a_property_not_a_field(self) -> None:
        assert "is_valid" not in {f.name for f in dataclasses.fields(ValidationResult)}
