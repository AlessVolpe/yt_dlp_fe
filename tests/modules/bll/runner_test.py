"""Tests for ``modules.bll.runner.Runner``.

Unit tests cover command construction, dispatch and dialog handling; the
integration tests drive the complete download/convert pipeline through the
real main window using the fake ``yt-dlp`` and ``ffmpeg`` executables.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable, List
from unittest.mock import MagicMock

import pytest
from PySide6 import QtCore, QtWidgets

from modules.bll import runner as runner_module
from modules.bll.runner import Runner

LEFT = QtCore.Qt.MouseButton.LeftButton
VID = "dQw4w9WgXcQ"
VIDEO_URL = f"https://www.youtube.com/watch?v={VID}"
PLAYLIST_ID = "PLtestlist"
PLAYLIST_URL = f"https://www.youtube.com/playlist?list={PLAYLIST_ID}"


@pytest.fixture(autouse=True)
def _capture_info_logs(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO)


@pytest.fixture
def start(qtbot: Any, main_window: Any) -> Callable[[str, str], None]:
    """Return a callable that types a URL and clicks the requested action button."""

    def _start(url: str, kind: str = "audio") -> None:
        main_window.url_input.setText(url)
        button = main_window.audio_only_button if kind == "audio" else main_window.video_button
        qtbot.mouseClick(button, LEFT)

    return _start


def log_text(window: Any) -> str:
    return window.dialog_box.toPlainText()


@pytest.mark.unit
class TestConstruction:
    def test_initial_state(self, main_window: Any) -> None:
        runner = Runner(main_window, "/somewhere")
        assert runner.gui is main_window
        assert runner.selected_directory == "/somewhere"
        assert runner.is_playlist is False
        assert runner._worker is None and runner._converter is None

    def test_download_directory_is_optional(self, main_window: Any) -> None:
        assert Runner(main_window).selected_directory is None

    def test_accepts_path_objects(self, main_window: Any, tmp_path: Path) -> None:
        assert Runner(main_window, tmp_path).selected_directory == tmp_path


@pytest.mark.unit
class TestBuildCommand:
    def test_single_video_command(self, main_window: Any) -> None:
        runner = main_window.runner
        runner.is_playlist = False
        output_path = Path("C:/out/DLP_VIDEO")
        expected_template = output_path / "%(id)s.%(ext)s"
        assert runner._build_cmd('yt-dlp -f "best"', str(output_path), "https://u") == (
            f'yt-dlp -f "best" --no-playlist -o "{expected_template}" "https://u"'
        )

    def test_playlist_command(self, main_window: Any) -> None:
        runner = main_window.runner
        runner.is_playlist = True
        output_path = Path("C:/out/DLP_AUDIO")
        expected_template = (
            output_path
            / "%(playlist_id)s"
            / "%(playlist_index)s - %(id)s.%(ext)s"
        )
        assert runner._build_cmd('yt-dlp -f "best"', str(output_path), "https://u") == (
            f'yt-dlp -f "best" --yes-playlist -o "{expected_template}" "https://u"'
        )

    def test_build_is_pure_with_respect_to_the_base_command(self, main_window: Any) -> None:
        base = "yt-dlp"
        main_window.runner._build_cmd(base, "/o", "u")
        assert base == "yt-dlp"


@pytest.mark.unit
class TestDispatch:
    @pytest.mark.parametrize(
        ("button_name", "expected"), [("audio_only_button", "audio"), ("video_button", "video")]
    )
    def test_buttons_are_wired_to_the_matching_download_type(
        self, qtbot: Any, main_window: Any, monkeypatch: pytest.MonkeyPatch, button_name: str, expected: str
    ) -> None:
        spy = MagicMock()
        monkeypatch.setattr(main_window.runner, "_start_download", spy)
        qtbot.mouseClick(getattr(main_window, button_name), LEFT)
        spy.assert_called_once_with(expected)

    def test_status_helper_updates_the_badge(self, main_window: Any) -> None:
        main_window.runner._set_status("Anything")
        assert main_window.status_badge.text() == "Anything"


@pytest.mark.unit
class TestInputRejection:
    @pytest.mark.parametrize(
        ("url", "fragment"),
        [
            ("", "Paste a URL"),
            ("https://vimeo.com/1", "does not look like a YouTube link"),
            (f"https://www.youtube.com/shorts/{VID}", "Shorts are not supported"),
            ("https://www.youtube.com/@channel", "Channel links are not supported"),
            ("https://www.youtube.com/playlist?list=WL", "Watch Later"),
            ("https://www.youtube.com/watch?v=bad", "missing a valid video ID"),
        ],
    )
    def test_invalid_input_never_spawns_a_process(
        self, main_window: Any, start: Callable[..., None], fake_binaries: Any, url: str, fragment: str
    ) -> None:
        start(url)
        assert fragment in log_text(main_window)
        assert fake_binaries.calls() == []
        assert main_window.audio_only_button.isEnabled() and main_window.video_button.isEnabled()
        assert main_window.status_badge.text() == "Idle"
        assert main_window.runner._worker is None

    def test_previous_log_content_is_cleared_first(
        self, main_window: Any, start: Callable[..., None], fake_binaries: Any
    ) -> None:
        main_window.dialog_box.setPlainText("stale entry")
        start("")
        assert "stale entry" not in log_text(main_window)


@pytest.mark.integration
class TestSingleDownload:
    @pytest.mark.parametrize(
        ("kind", "subfolder", "extension", "selector"),
        [("audio", "DLP_AUDIO", "wav", "bestaudio/best"), ("video", "DLP_VIDEO", "mp4", "bestvideo*+bestaudio/best")],
    )
    def test_full_pipeline(
        self, main_window: Any, start: Callable[..., None], wait_idle: Callable[..., None], fake_binaries: Any,
        download_dir: Path, kind: str, subfolder: str, extension: str, selector: str,
    ) -> None:
        start(VIDEO_URL, kind)
        wait_idle()

        folder = download_dir / subfolder
        assert (folder / f"{VID}.{extension}").exists()
        assert not (folder / f"{VID}.webm").exists()

        (argv,) = fake_binaries.argvs("yt-dlp")
        assert argv[:4] == ["-f", selector, "--no-playlist", "-o"]
        assert Path(argv[4]) == folder / "%(id)s.%(ext)s"
        assert argv[5] == VIDEO_URL

        text = log_text(main_window)
        for expected in (f"Starting {kind} download: {VIDEO_URL}", "Download finished (exit code: 0)",
                         f"Converting the {kind} webm file to {extension} file", "Conversion finished (exit code: 0)"):
            assert expected in text

    def test_ui_is_locked_while_the_download_runs(
        self, main_window: Any, start: Callable[..., None], wait_idle: Callable[..., None], fake_binaries: Any
    ) -> None:
        fake_binaries.configure("yt-dlp", delay=0.4)
        start(VIDEO_URL)
        assert main_window.status_badge.text() == "Downloading..."
        assert not main_window.audio_only_button.isEnabled()
        assert not main_window.video_button.isEnabled()
        wait_idle()

    def test_child_output_is_streamed_into_the_activity_log(
        self, main_window: Any, start: Callable[..., None], wait_idle: Callable[..., None], fake_binaries: Any
    ) -> None:
        fake_binaries.configure("yt-dlp", stdout=["[download]   1.0% of 10MiB", "[download] 100% of 10MiB"])
        start(VIDEO_URL)
        wait_idle()
        text = log_text(main_window)
        assert text.index("1.0% of 10MiB") < text.index("100% of 10MiB")

    def test_directory_with_spaces_is_handled(
        self, main_window: Any, start: Callable[..., None], wait_idle: Callable[..., None], fake_binaries: Any,
        tmp_path: Path,
    ) -> None:
        target = tmp_path / "my music & videos"
        main_window.runner.selected_directory = str(target)
        start(VIDEO_URL)
        wait_idle()
        assert (target / "DLP_AUDIO" / f"{VID}.wav").exists()

    def test_non_webm_download_needs_no_conversion(
        self, main_window: Any, start: Callable[..., None], wait_idle: Callable[..., None], fake_binaries: Any,
        download_dir: Path,
    ) -> None:
        fake_binaries.configure("yt-dlp", extensions=["mp4"])
        start(VIDEO_URL, "video")
        wait_idle()
        assert "no conversion needed" in log_text(main_window)
        assert (download_dir / "DLP_VIDEO" / f"{VID}.mp4").exists()
        assert fake_binaries.calls("ffmpeg") == []

    def test_download_that_produces_nothing_still_returns_to_idle(
        self, main_window: Any, start: Callable[..., None], wait_idle: Callable[..., None], fake_binaries: Any
    ) -> None:
        fake_binaries.configure("yt-dlp", write_files=False)
        start(VIDEO_URL)
        wait_idle()
        assert fake_binaries.calls("ffmpeg") == []

    @pytest.mark.parametrize("status", [1, 2, 101, 255])
    def test_download_failure_skips_conversion_and_restores_the_ui(
        self, main_window: Any, start: Callable[..., None], wait_idle: Callable[..., None], fake_binaries: Any,
        status: int,
    ) -> None:
        fake_binaries.configure("yt-dlp", exit_code=status)
        start(VIDEO_URL)
        wait_idle()
        text = log_text(main_window)
        assert f"Download finished (exit code: {status})" in text
        assert "ERROR: fake yt-dlp failure" in text
        assert fake_binaries.calls("ffmpeg") == []

    def test_conversion_failure_keeps_the_source_and_restores_the_ui(
        self, main_window: Any, start: Callable[..., None], wait_idle: Callable[..., None], fake_binaries: Any,
        download_dir: Path,
    ) -> None:
        fake_binaries.configure("ffmpeg", exit_code=1)
        start(VIDEO_URL)
        wait_idle()
        assert (download_dir / "DLP_AUDIO" / f"{VID}.webm").exists()

    def test_consecutive_downloads_reuse_the_runner(
        self, main_window: Any, start: Callable[..., None], wait_idle: Callable[..., None], fake_binaries: Any,
        download_dir: Path,
    ) -> None:
        start(VIDEO_URL, "audio")
        wait_idle()
        start(f"https://youtu.be/{'a' * 11}", "video")
        wait_idle()
        assert (download_dir / "DLP_AUDIO" / f"{VID}.wav").exists()
        assert (download_dir / "DLP_VIDEO" / f"{'a' * 11}.mp4").exists()
        assert "Starting audio download" not in log_text(main_window)  # log cleared per run


@pytest.mark.integration
class TestPlaylistDownload:
    def test_all_items_are_converted_and_sources_removed(
        self, main_window: Any, start: Callable[..., None], wait_idle: Callable[..., None], fake_binaries: Any,
        download_dir: Path,
    ) -> None:
        start(PLAYLIST_URL)
        wait_idle()

        folder = download_dir / "DLP_AUDIO" / PLAYLIST_ID
        assert sorted(p.name for p in folder.iterdir()) == [f"{i} - vid{i:08d}.wav" for i in (1, 2, 3)]
        assert fake_binaries.argvs("yt-dlp")[0][2] == "--yes-playlist"
        assert "Converting 3 webm file(s)..." in log_text(main_window)
        assert main_window.runner.is_playlist is True

    def test_video_mode_produces_mp4_files(
        self, start: Callable[..., None], wait_idle: Callable[..., None], fake_binaries: Any, download_dir: Path
    ) -> None:
        fake_binaries.configure("yt-dlp", playlist_items=2)
        start(PLAYLIST_URL, "video")
        wait_idle()
        assert sorted(p.suffix for p in (download_dir / "DLP_VIDEO" / PLAYLIST_ID).iterdir()) == [".mp4", ".mp4"]

    def test_index_padding_of_large_playlists_is_respected(
        self, start: Callable[..., None], wait_idle: Callable[..., None], fake_binaries: Any, download_dir: Path
    ) -> None:
        fake_binaries.configure("yt-dlp", playlist_items=12)
        start(PLAYLIST_URL)
        wait_idle(30000)
        names = sorted(p.name for p in (download_dir / "DLP_AUDIO" / PLAYLIST_ID).iterdir())
        assert len(names) == 12 and names[0] == "01 - vid00000001.wav"
        assert len(fake_binaries.calls("ffmpeg")) == 12

    def test_single_failed_conversion_does_not_abort_the_queue(
        self, start: Callable[..., None], wait_idle: Callable[..., None], fake_binaries: Any, download_dir: Path
    ) -> None:
        fake_binaries.configure("ffmpeg", fail_on="vid00000002")
        start(PLAYLIST_URL)
        wait_idle()
        folder = download_dir / "DLP_AUDIO" / PLAYLIST_ID
        assert sorted(p.name for p in folder.iterdir()) == [
            "1 - vid00000001.wav", "2 - vid00000002.webm", "3 - vid00000003.wav",
        ]

    def test_only_webm_items_are_queued(
        self, main_window: Any, start: Callable[..., None], wait_idle: Callable[..., None], fake_binaries: Any,
        download_dir: Path,
    ) -> None:
        fake_binaries.configure("yt-dlp", extensions=["webm", "m4a"])
        start(PLAYLIST_URL)
        wait_idle()
        assert "Converting 2 webm file(s)..." in log_text(main_window)
        assert (download_dir / "DLP_AUDIO" / PLAYLIST_ID / "2 - vid00000002.m4a").exists()

    def test_playlist_without_webm_files_ends_gracefully(
        self, main_window: Any, start: Callable[..., None], wait_idle: Callable[..., None], fake_binaries: Any
    ) -> None:
        fake_binaries.configure("yt-dlp", extensions=["m4a"])
        start(PLAYLIST_URL)
        wait_idle()
        assert "No playlist files found to convert." in log_text(main_window)
        assert fake_binaries.calls("ffmpeg") == []

    def test_playlist_flag_is_reset_by_a_subsequent_single_video(
        self, main_window: Any, start: Callable[..., None], wait_idle: Callable[..., None], fake_binaries: Any
    ) -> None:
        start(PLAYLIST_URL)
        wait_idle()
        start(VIDEO_URL)
        wait_idle()
        assert main_window.runner.is_playlist is False
        assert fake_binaries.argvs("yt-dlp")[-1][2] == "--no-playlist"

    def test_download_failure_in_playlist_mode_skips_conversion(
        self, start: Callable[..., None], wait_idle: Callable[..., None], fake_binaries: Any
    ) -> None:
        fake_binaries.configure("yt-dlp", exit_code=1)
        start(PLAYLIST_URL)
        wait_idle()
        assert fake_binaries.calls("ffmpeg") == []


@pytest.mark.integration
class TestPlaylistOrdering:
    def test_queue_is_grouped_by_sorted_playlist_folder(
        self, main_window: Any, wait_idle: Callable[..., None], fake_binaries: Any, download_dir: Path
    ) -> None:
        runner = main_window.runner
        runner._current_download_type = "audio"
        runner._current_subfolder = "DLP_AUDIO"
        for folder in ("PLb", "PLa"):
            target = download_dir / "DLP_AUDIO" / folder
            target.mkdir(parents=True)
            (target / "1 - x.webm").write_bytes(b"x")

        runner._convert_playlist_files()
        wait_idle()

        sources = [argv[1] for argv in fake_binaries.argvs("ffmpeg")]
        assert [Path(s).parent.name for s in sources] == ["PLa", "PLb"]

    def test_empty_folder_short_circuits_to_idle(
        self, main_window: Any, wait_idle: Callable[..., None], download_dir: Path
    ) -> None:
        runner = main_window.runner
        runner._current_download_type = "audio"
        runner._current_subfolder = "DLP_AUDIO"
        runner._convert_playlist_files()
        wait_idle()
        assert "No playlist files found to convert." in log_text(main_window)

    def test_end_of_queue_resets_the_gui(self, main_window: Any) -> None:
        runner = main_window.runner
        runner._playlist_files_to_convert = []
        main_window.audio_only_button.setEnabled(False)
        main_window.status_badge.setText("Converting...")
        runner._convert_next_playlist_file()
        assert main_window.status_badge.text() == "Idle"
        assert main_window.audio_only_button.isEnabled()


@pytest.mark.unit
class TestDestinationDialog:
    def test_confirmed_selection_updates_state_and_label(
        self, main_window: Any, stub_file_dialog: type, tmp_path: Path
    ) -> None:
        stub_file_dialog.accept = True
        stub_file_dialog.selection = [str(tmp_path)]
        main_window.runner.open_file_dialog()
        assert main_window.runner.selected_directory == str(tmp_path)
        assert main_window.location_label.text() == str(tmp_path)

    def test_cancelled_dialog_leaves_state_untouched(self, main_window: Any, stub_file_dialog: type) -> None:
        before_dir, before_label = main_window.runner.selected_directory, main_window.location_label.text()
        stub_file_dialog.accept = False
        stub_file_dialog.selection = ["/should/not/be/used"]
        main_window.runner.open_file_dialog()
        assert main_window.runner.selected_directory == before_dir
        assert main_window.location_label.text() == before_label

    def test_dialog_is_configured_for_directory_selection(self, main_window: Any, stub_file_dialog: type) -> None:
        stub_file_dialog.accept = False
        main_window.runner.open_file_dialog()
        (dialog,) = stub_file_dialog.instances
        assert dialog.parent is main_window
        assert dialog.directory == QtCore.QDir.homePath()
        assert dialog.file_mode == stub_file_dialog.FileMode.Directory
        assert dialog.view_mode == stub_file_dialog.ViewMode.Detail

    def test_new_directory_is_used_by_the_next_download(
        self, main_window: Any, stub_file_dialog: type, tmp_path: Path, start: Callable[..., None],
        wait_idle: Callable[..., None], fake_binaries: Any,
    ) -> None:
        stub_file_dialog.accept = True
        stub_file_dialog.selection = [str(tmp_path / "elsewhere")]
        main_window.runner.open_file_dialog()
        start(VIDEO_URL)
        wait_idle()
        assert (tmp_path / "elsewhere" / "DLP_AUDIO" / f"{VID}.wav").exists()


@pytest.mark.integration
class TestStartupUpdate:
    def test_invokes_yt_dlp_self_update_and_waits_for_it(self, fake_binaries: Any) -> None:
        Runner.update_on_startup()
        assert fake_binaries.argvs("yt-dlp") == [["-U"]]  # already logged => call blocked until completion

    def test_uses_a_shell_command(self, monkeypatch: pytest.MonkeyPatch) -> None:
        popen = MagicMock()
        monkeypatch.setattr(runner_module.subprocess, "Popen", popen)
        Runner.update_on_startup()
        popen.assert_called_once_with("yt-dlp -U", shell=True)
        popen.return_value.__enter__.assert_called_once()

    def test_a_failing_update_does_not_raise(self, fake_binaries: Any) -> None:
        fake_binaries.configure("yt-dlp", update_exit_code=1)
        Runner.update_on_startup()

    def test_is_callable_on_the_class(self) -> None:
        assert isinstance(Runner.__dict__["update_on_startup"], staticmethod)
