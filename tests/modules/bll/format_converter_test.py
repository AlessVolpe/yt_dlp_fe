"""Tests for ``modules.bll.format_converter.FormatConverter``."""
from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, List, Optional
from unittest.mock import MagicMock

import pytest

from config.error_codes import ExitCode
from modules.bll.format_converter import FormatConverter


@pytest.fixture
def make_source(tmp_path: Path) -> Callable[..., Path]:
    """Create ``<stem>.webm`` inside `tmp_path` and return its extension-less base path."""

    def _make(stem: str = "clip", directory: Optional[Path] = None) -> Path:
        base = (directory or tmp_path) / stem
        base.parent.mkdir(parents=True, exist_ok=True)
        base.with_suffix(".webm").write_bytes(b"fake-webm")
        return base

    return _make


@pytest.fixture
def convert(qtbot: Any, converter_gui: SimpleNamespace, caplog: pytest.LogCaptureFixture) -> Callable[..., FormatConverter]:
    """Run a full conversion and return the converter once it has signalled completion."""
    caplog.set_level(logging.INFO)

    def _convert(base: Path, download_type: str = "audio", is_playlist: bool = False) -> FormatConverter:
        converter = FormatConverter(converter_gui, download_type, str(base), is_playlist)
        with qtbot.waitSignal(converter.finished_conversion, timeout=10000):
            converter.convert_file()
        if converter._worker is not None:
            converter._worker.wait(5000)
        return converter

    return _convert


def dialog_text(gui: SimpleNamespace) -> str:
    return gui.dialog_box.toPlainText()


@pytest.mark.integration
class TestSuccessfulConversion:
    @pytest.mark.parametrize(("download_type", "extension"), [("audio", "wav"), ("video", "mp4")])
    def test_target_format_follows_download_type(
        self, convert: Callable[..., FormatConverter], make_source: Callable[..., Path],
        fake_binaries: Any, download_type: str, extension: str,
    ) -> None:
        base = make_source()
        convert(base, download_type)
        assert base.with_suffix(f".{extension}").read_bytes() == b"fake-converted"
        assert fake_binaries.argvs("ffmpeg") == [["-i", f"{base}.webm", f"{base}.{extension}"]]

    def test_unknown_download_type_falls_back_to_mp4(
        self, convert: Callable[..., FormatConverter], make_source: Callable[..., Path], fake_binaries: Any
    ) -> None:
        base = make_source()
        convert(base, "podcast")
        assert base.with_suffix(".mp4").exists()

    def test_source_is_removed_after_success(
        self, convert: Callable[..., FormatConverter], make_source: Callable[..., Path], fake_binaries: Any
    ) -> None:
        base = make_source()
        convert(base)
        assert not base.with_suffix(".webm").exists()

    def test_status_badge_and_logs_describe_the_conversion(
        self, convert: Callable[..., FormatConverter], make_source: Callable[..., Path], fake_binaries: Any,
        converter_gui: SimpleNamespace, caplog: pytest.LogCaptureFixture,
    ) -> None:
        convert(make_source())
        assert converter_gui.status_badge.text() == "Converting..."
        assert "Converting the audio webm file to wav file" in caplog.text
        assert "Conversion finished (exit code: 0)" in caplog.text

    @pytest.mark.parametrize(("is_playlist", "wording"), [(False, "files"), (True, "file")])
    def test_cleanup_message_wording_depends_on_playlist_flag(
        self, convert: Callable[..., FormatConverter], make_source: Callable[..., Path], fake_binaries: Any,
        converter_gui: SimpleNamespace, is_playlist: bool, wording: str,
    ) -> None:
        convert(make_source(), is_playlist=is_playlist)
        assert dialog_text(converter_gui) == f"Deleting temporary {wording}..."

    def test_paths_with_spaces_and_unusual_characters_are_quoted(
        self, convert: Callable[..., FormatConverter], make_source: Callable[..., Path], fake_binaries: Any,
        tmp_path: Path,
    ) -> None:
        base = make_source("1 - vid_00-01", directory=tmp_path / "my downloads" / "PL list")
        convert(base)
        assert base.with_suffix(".wav").exists() and not base.with_suffix(".webm").exists()

    def test_completion_signal_is_emitted_exactly_once(
        self, qtbot: Any, converter_gui: SimpleNamespace, make_source: Callable[..., Path], fake_binaries: Any
    ) -> None:
        converter = FormatConverter(converter_gui, "audio", str(make_source()))
        count: List[int] = []
        converter.finished_conversion.connect(lambda: count.append(1))
        with qtbot.waitSignal(converter.finished_conversion, timeout=10000):
            converter.convert_file()
        converter._worker.wait(5000)
        qtbot.wait(50)
        assert len(count) == 1


@pytest.mark.integration
class TestSkippedAndFailedConversion:
    def test_missing_source_skips_ffmpeg_and_signals_immediately(
        self, convert: Callable[..., FormatConverter], tmp_path: Path, fake_binaries: Any,
        converter_gui: SimpleNamespace, caplog: pytest.LogCaptureFixture,
    ) -> None:
        converter = convert(tmp_path / "absent")
        assert converter._worker is None
        assert fake_binaries.calls("ffmpeg") == []
        assert "no conversion needed" in caplog.text
        assert converter_gui.status_badge.text() == "Idle"

    def test_source_with_other_extension_is_ignored(
        self, convert: Callable[..., FormatConverter], tmp_path: Path, fake_binaries: Any
    ) -> None:
        (tmp_path / "clip.m4a").write_bytes(b"x")
        convert(tmp_path / "clip")
        assert fake_binaries.calls("ffmpeg") == []
        assert (tmp_path / "clip.m4a").exists()

    @pytest.mark.parametrize("status", [1, 2, 137])
    def test_ffmpeg_failure_keeps_the_source_and_skips_cleanup(
        self, convert: Callable[..., FormatConverter], make_source: Callable[..., Path], fake_binaries: Any,
        converter_gui: SimpleNamespace, caplog: pytest.LogCaptureFixture, status: int,
    ) -> None:
        fake_binaries.configure("ffmpeg", exit_code=status)
        base = make_source()
        convert(base)
        assert base.with_suffix(".webm").exists()
        assert not base.with_suffix(".wav").exists()
        assert dialog_text(converter_gui) == ""
        assert f"Conversion finished (exit code: {status})" in caplog.text

    def test_source_removed_during_conversion_is_reported_not_raised(
        self, convert: Callable[..., FormatConverter], make_source: Callable[..., Path], fake_binaries: Any,
        converter_gui: SimpleNamespace,
    ) -> None:
        fake_binaries.configure("ffmpeg", remove_source=True)
        base = make_source()
        convert(base)
        assert base.with_suffix(".wav").exists()
        assert dialog_text(converter_gui).splitlines()[-1] == "Temporary file not found."


@pytest.mark.unit
class TestConversionEndHandler:
    def make(self, converter_gui: SimpleNamespace, base: Path) -> FormatConverter:
        return FormatConverter(converter_gui, "audio", str(base))

    def test_worker_is_joined_before_completion_is_signalled(
        self, converter_gui: SimpleNamespace, tmp_path: Path
    ) -> None:
        converter = self.make(converter_gui, tmp_path / "clip")
        events: List[str] = []
        converter._worker = MagicMock()
        converter._worker.wait.side_effect = lambda *a: events.append("wait")
        converter.finished_conversion.connect(lambda: events.append("signal"))
        converter._on_conversion_end(ExitCode.GENERAL_ERROR)
        assert events == ["wait", "signal"]

    def test_absent_worker_is_tolerated(self, converter_gui: SimpleNamespace, tmp_path: Path) -> None:
        converter = self.make(converter_gui, tmp_path / "clip")
        fired: List[int] = []
        converter.finished_conversion.connect(lambda: fired.append(1))
        converter._on_conversion_end(ExitCode.GENERAL_ERROR)
        assert fired == [1]

    def test_success_with_missing_source_reports_it(self, converter_gui: SimpleNamespace, tmp_path: Path) -> None:
        converter = self.make(converter_gui, tmp_path / "clip")
        converter._on_conversion_end(ExitCode.SUCCESS)
        assert dialog_text(converter_gui).splitlines() == ["Deleting temporary files...", "Temporary file not found."]

    def test_success_deletes_only_the_webm_source(self, converter_gui: SimpleNamespace, tmp_path: Path) -> None:
        (tmp_path / "clip.webm").write_bytes(b"x")
        (tmp_path / "clip.wav").write_bytes(b"y")
        self.make(converter_gui, tmp_path / "clip")._on_conversion_end(ExitCode.SUCCESS)
        assert sorted(p.name for p in tmp_path.iterdir()) == ["clip.wav"]

    def test_status_helper_updates_the_badge(self, converter_gui: SimpleNamespace, tmp_path: Path) -> None:
        self.make(converter_gui, tmp_path / "clip")._set_status("Working")
        assert converter_gui.status_badge.text() == "Working"


@pytest.mark.integration
@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="real ffmpeg not installed")
class TestRealFfmpeg:
    """End-to-end check against the genuine ffmpeg binary (skipped when unavailable)."""

    def test_webm_audio_is_transcoded_to_a_valid_wav(
        self, convert: Callable[..., FormatConverter], tmp_path: Path
    ) -> None:
        source = tmp_path / "tone.webm"
        produced = subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", "sine=frequency=440:duration=0.2",
             "-c:a", "libopus", str(source)],
            capture_output=True,
        )
        if produced.returncode != 0:
            pytest.skip("this ffmpeg build cannot encode WebM/Opus test material")

        convert(tmp_path / "tone")
        wav = tmp_path / "tone.wav"
        assert wav.read_bytes()[:4] == b"RIFF"
        assert not source.exists()
