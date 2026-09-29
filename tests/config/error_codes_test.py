"""Tests for ``config.error_codes.ExitCode``."""
from __future__ import annotations

from enum import IntEnum

import pytest

from config.error_codes import ExitCode

EXPECTED = {
    "SUCCESS": 0,
    "GENERAL_ERROR": 1,
    "PROCESS_FAILED": -1,
    "CANCELED": -2,
    "MISSING_EXECUTABLE": -3,
}


@pytest.mark.unit
class TestExitCode:
    def test_is_an_int_enum(self) -> None:
        assert issubclass(ExitCode, IntEnum)

    def test_member_set_is_exactly_the_documented_one(self) -> None:
        assert {member.name: member.value for member in ExitCode} == EXPECTED

    @pytest.mark.parametrize(("name", "value"), EXPECTED.items())
    def test_lookup_by_value_round_trips(self, name: str, value: int) -> None:
        assert ExitCode(value) is ExitCode[name]

    def test_values_are_unique(self) -> None:
        values = [member.value for member in ExitCode]
        assert len(values) == len(set(values))

    @pytest.mark.parametrize("value", [2, 42, 127, 255, -4, 4294967294])
    def test_unmapped_values_are_rejected(self, value: int) -> None:
        with pytest.raises(ValueError):
            ExitCode(value)

    def test_members_compare_equal_to_plain_integers(self) -> None:
        assert ExitCode.SUCCESS == 0
        assert ExitCode.CANCELED == -2
        assert 1 == ExitCode.GENERAL_ERROR

    def test_negative_members_fit_a_signed_32_bit_signal(self) -> None:
        assert all(-(2**31) <= member <= 2**31 - 1 for member in ExitCode)
