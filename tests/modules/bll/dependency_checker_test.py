"""Tests for ``modules.bll.dependency_checker``."""
from __future__ import annotations

import dataclasses
import os
from pathlib import Path
from typing import Any

import pytest

from modules.bll import dependency_checker
from modules.bll.dependency_checker import (
    REQUIRED_DEPENDENCIES,
    Dependency,
    find_missing_dependencies,
    is_available,
)


@pytest.fixture
def empty_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Point PATH at an empty directory so that nothing can be resolved."""
    monkeypatch.setenv("PATH", str(tmp_path))
    return tmp_path


@pytest.mark.unit
class TestDependencyRecord:
    def test_is_frozen(self) -> None:
        dependency = Dependency("tool", "desc", "https://example.org")
        with pytest.raises(dataclasses.FrozenInstanceError):
            dependency.executable = "other"  # type: ignore[misc]

    def test_is_hashable_and_value_comparable(self) -> None:
        first = Dependency("tool", "desc", "https://example.org")
        second = Dependency("tool", "desc", "https://example.org")
        assert first == second
        assert len({first, second}) == 1

    def test_registry_lists_the_two_runtime_tools_in_order(self) -> None:
        assert [d.executable for d in REQUIRED_DEPENDENCIES] == ["yt-dlp", "ffmpeg"]

    @pytest.mark.parametrize("dependency", REQUIRED_DEPENDENCIES, ids=lambda d: d.executable)
    def test_registry_entries_are_complete(self, dependency: Dependency) -> None:
        assert dependency.description.strip()
        assert dependency.install_url.startswith("https://")


@pytest.mark.unit
class TestIsAvailable:
    def test_finds_an_executable_on_path(self, fake_binaries: Any) -> None:
        assert is_available("yt-dlp") is True

    def test_reports_absence(self, empty_path: Path) -> None:
        assert is_available("yt-dlp") is False

    @pytest.mark.parametrize("name", ["", " ", "definitely-not-a-real-binary-xyz"])
    def test_rejects_degenerate_names(self, empty_path: Path, name: str) -> None:
        assert is_available(name) is False

    @pytest.mark.skipif(os.name == "nt", reason="POSIX execute-bit semantics")
    def test_non_executable_file_is_not_available(self, empty_path: Path) -> None:
        (empty_path / "plain-file").write_text("data")
        assert is_available("plain-file") is False

    def test_delegates_to_shutil_which(self, monkeypatch: pytest.MonkeyPatch) -> None:
        seen = []
        monkeypatch.setattr(dependency_checker.shutil, "which", lambda exe: seen.append(exe) or "/x/" + exe)
        assert is_available("ffmpeg") is True
        assert seen == ["ffmpeg"]


@pytest.mark.unit
class TestFindMissingDependencies:
    def test_nothing_missing_when_all_tools_present(self, fake_binaries: Any) -> None:
        assert find_missing_dependencies() == ()

    def test_everything_missing_on_empty_path(self, empty_path: Path) -> None:
        assert find_missing_dependencies() == tuple(REQUIRED_DEPENDENCIES)

    @pytest.mark.parametrize("absent", ["yt-dlp", "ffmpeg"])
    def test_reports_only_the_absent_tool(self, monkeypatch: pytest.MonkeyPatch, absent: str) -> None:
        monkeypatch.setattr(
            dependency_checker.shutil, "which", lambda exe: None if exe == absent else "/bin/" + exe
        )
        assert [d.executable for d in find_missing_dependencies()] == [absent]

    def test_returns_a_tuple_preserving_registry_order(self, empty_path: Path) -> None:
        result = find_missing_dependencies()
        assert isinstance(result, tuple)
        assert [d.executable for d in result] == ["yt-dlp", "ffmpeg"]

    def test_honours_a_monkeypatched_registry(self, monkeypatch: pytest.MonkeyPatch, empty_path: Path) -> None:
        custom = [Dependency("only-this", "d", "https://example.org")]
        monkeypatch.setattr(dependency_checker, "REQUIRED_DEPENDENCIES", custom)
        assert find_missing_dependencies() == tuple(custom)

