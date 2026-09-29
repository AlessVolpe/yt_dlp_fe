"""Tests for ``config.constants``: path resolution and asset integrity."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

from config import constants

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_isolated() -> ModuleType:
    """Execute constants.py as a fresh module, leaving the imported one untouched."""
    spec = importlib.util.spec_from_file_location("constants_isolated", constants.__file__)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.unit
class TestPathResolution:
    def test_source_mode_base_dir_is_repository_root(self) -> None:
        assert constants.BASE_DIR == REPO_ROOT

    def test_assets_dir_is_child_of_base_dir(self) -> None:
        assert constants.ASSETS_DIR == constants.BASE_DIR / "assets"

    @pytest.mark.parametrize(
        ("attribute", "filename"),
        [("ICON_PATH", "icon.ico"), ("SVG_PATH", "icon.svg"), ("PNG_PATH", "icon_256.png")],
    )
    def test_icon_paths_point_into_assets_dir(self, attribute: str, filename: str) -> None:
        assert getattr(constants, attribute) == constants.ASSETS_DIR / filename

    def test_frozen_mode_resolves_against_meipass(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
        module = _load_isolated()
        assert module.BASE_DIR == tmp_path
        assert module.ICON_PATH == tmp_path / "assets" / "icon.ico"

    def test_falsy_frozen_flag_ignores_meipass(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        monkeypatch.setattr(sys, "frozen", False, raising=False)
        monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
        assert _load_isolated().BASE_DIR == REPO_ROOT

    def test_frozen_without_meipass_fails_loudly(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.delattr(sys, "_MEIPASS", raising=False)
        with pytest.raises(AttributeError):
            _load_isolated()


@pytest.mark.unit
class TestAssetIntegrity:
    SIGNATURES = {
        "ICON_PATH": b"\x00\x00\x01\x00",
        "PNG_PATH": b"\x89PNG\r\n\x1a\n",
    }

    @pytest.mark.parametrize("attribute", ["ICON_PATH", "SVG_PATH", "PNG_PATH"])
    def test_asset_exists_and_is_non_empty(self, attribute: str) -> None:
        path: Path = getattr(constants, attribute)
        assert path.is_file()
        assert path.stat().st_size > 0

    @pytest.mark.parametrize("attribute", ["ICON_PATH", "PNG_PATH"])
    def test_binary_asset_has_expected_magic_number(self, attribute: str) -> None:
        signature = self.SIGNATURES[attribute]
        assert getattr(constants, attribute).read_bytes()[: len(signature)] == signature

    def test_svg_asset_is_an_svg_document(self) -> None:
        assert "<svg" in constants.SVG_PATH.read_text(encoding="utf-8")


@pytest.mark.unit
def test_max_positive_integer_is_signed_32_bit_maximum() -> None:
    assert constants.MAX_POSITIVE_INTEGER == 2**31 - 1 == 2147483647
