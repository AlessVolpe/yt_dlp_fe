"""Repository-level consistency checks (packaging spec and test-suite layout).

These tests guard conventions that are easy to break silently: stale PyInstaller
hidden imports after a refactor, missing bundled assets, and source modules
without a mirrored test module.
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Any, Dict, List

import pytest

from config.constants import BASE_DIR

SRC = BASE_DIR / "src"
TESTS = BASE_DIR / "tests"
SPEC = BASE_DIR / "main.spec"
NON_MIRRORED_TESTS = {"packaging_test.py"}


def _spec_call_kwargs(name: str) -> Dict[str, Any]:
    """Return the literal keyword arguments of the first call to `name` in main.spec."""
    tree = ast.parse(SPEC.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "id", None) == name:
            kwargs: Dict[str, Any] = {}
            for keyword in node.keywords:
                try:
                    kwargs[keyword.arg] = ast.literal_eval(keyword.value)
                except ValueError:
                    continue
            kwargs["__args__"] = node.args
            return kwargs
    raise AssertionError(f"{name}(...) not found in main.spec")


def _module_file(dotted: str) -> Path:
    return SRC.joinpath(*dotted.split(".")).with_suffix(".py")


def _source_modules() -> List[Path]:
    return sorted(p for p in SRC.rglob("*.py") if p.name != "__init__.py")


@pytest.fixture(scope="module")
def analysis() -> Dict[str, Any]:
    """Literal keyword arguments of the spec's ``Analysis(...)`` call (parsed once)."""
    return _spec_call_kwargs("Analysis")


@pytest.mark.unit
class TestPyInstallerSpec:
    def test_entry_point_and_search_path_exist(self, analysis: Dict[str, Any]) -> None:
        (entry,) = analysis["__args__"][0].elts
        assert (BASE_DIR / entry.value).is_file()
        assert all((BASE_DIR / p).is_dir() for p in analysis["pathex"])

    def test_every_hidden_import_resolves_to_a_source_module(self, analysis: Dict[str, Any]) -> None:
        missing = [name for name in analysis["hiddenimports"] if not _module_file(name).is_file()]
        assert missing == []

    def test_hidden_imports_are_unique(self, analysis: Dict[str, Any]) -> None:
        names = analysis["hiddenimports"]
        assert len(names) == len(set(names))

    def test_bundled_data_sources_exist(self, analysis: Dict[str, Any]) -> None:
        assert all((BASE_DIR / source).exists() for source, _ in analysis["datas"])

    def test_assets_bundle_contains_the_runtime_icon(self, analysis: Dict[str, Any]) -> None:
        assert ("assets", "assets") in analysis["datas"]
        assert (BASE_DIR / "assets" / "icon.ico").is_file()

    def test_executable_icon_exists(self) -> None:
        assert (BASE_DIR / _spec_call_kwargs("EXE")["icon"]).is_file()

    def test_build_is_windowed_and_named_after_the_project(self) -> None:
        exe = _spec_call_kwargs("EXE")
        assert exe["name"] == "yt_dlp_fe" and exe["console"] is False

    def test_build_uses_onedir_without_upx(self) -> None:
        exe = _spec_call_kwargs("EXE")
        collect = _spec_call_kwargs("COLLECT")
        assert exe["exclude_binaries"] is True
        assert exe["upx"] is False
        assert collect["name"] == "yt_dlp_fe"
        assert collect["upx"] is False


@pytest.mark.unit
class TestSuiteLayout:
    @pytest.mark.parametrize("module", _source_modules(), ids=lambda p: str(p.relative_to(SRC)))
    def test_every_source_module_has_a_mirrored_test_module(self, module: Path) -> None:
        relative = module.relative_to(SRC)
        expected = TESTS / relative.parent / f"{relative.stem}_test.py"
        assert expected.is_file(), f"missing {expected.relative_to(BASE_DIR)}"

    def test_every_test_module_mirrors_a_source_module(self) -> None:
        orphans = []
        for test_file in TESTS.rglob("*_test.py"):
            if test_file.name in NON_MIRRORED_TESTS:
                continue
            relative = test_file.relative_to(TESTS)
            source = SRC / relative.parent / f"{relative.stem.removesuffix('_test')}.py"
            if not source.is_file():
                orphans.append(str(relative))
        assert orphans == []

    def test_test_modules_use_unique_base_names(self) -> None:
        names = [p.name for p in TESTS.rglob("*_test.py")]
        assert len(names) == len(set(names))
