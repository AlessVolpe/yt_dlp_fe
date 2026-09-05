# yt-dlp Front End

A lightweight desktop GUI for [yt-dlp](https://github.com/yt-dlp/yt-dlp), built with [PySide6](https://doc.qt.io/qtforpython-6/) (Qt for Python). Paste a URL, pick a destination, and download audio or video — including full playlists.

## Status

🚧 **Active development.** The app downloads audio and video (including full playlists) via real `yt-dlp` subprocess calls, streams `yt-dlp`'s own output into the activity log in real time, converts downloaded files with `ffmpeg`, and checks for `yt-dlp` updates on startup before the main window appears.

## Features

- Single-window Qt interface with a grouped Source / Activity / Actions layout
- URL input field, with a playlist toggle for downloading an entire playlist instead of a single video
- Destination folder picker ("Change") — downloads are organized into `DLP_AUDIO/` and `DLP_VIDEO/` subfolders inside the chosen directory (playlists additionally get one numbered subfolder per item)
- Separate **Audio only** and **Download video** actions, run on a background thread so the window stays responsive for the whole download
- Automatic format conversion from `.webm` to `.wav` (audio) or `.mp4` (video) via `ffmpeg` — for playlists, every downloaded file is converted in turn (currently unreliable, see Roadmap)
- Activity log streaming `yt-dlp`'s real-time output, with an Idle / Downloading / Converting status badge and action buttons that update live
- Checks for `yt-dlp` updates on startup before the main window appears

## Project Structure

```
yt_dlp_fe/
├── .github/                          # CI workflow configs
├── assets/                           # Icons / static resources (e.g. for packaging)
├── src/
│   ├── config/
│   │   ├── __init__.py
│   │   └── constants.py              # Shared path constants (e.g. ICON_PATH)
│   ├── modules/
│   │   ├── bll/                      # Business/backend logic
│   │   │   ├── __init__.py
│   │   │   ├── format_converter.py   # Converts a downloaded file via ffmpeg (.webm -> .wav/.mp4)
│   │   │   ├── process_worker.py     # Background QThread: runs a command, logs output live
│   │   │   └── runner.py             # Runner: builds and runs the yt-dlp subprocess calls
│   │   ├── guis/                     # GUI windows
│   │   │   ├── __init__.py
│   │   │   ├── progress_window.py    # Startup update-check window
│   │   │   └── user_interface.py     # Main application window
│   │   ├── loggers/                  # Real-time logging plumbing
│   │   │   ├── __init__.py
│   │   │   └── log_handler.py        # Bridges Python `logging` records into a Qt signal
│   │   └── __init__.py
│   └── main.py                       # Application entry point
├── requirements.txt
├── main.spec                         # PyInstaller build spec
├── .gitignore
└── README.md

# Generated / git-ignored, not tracked:
# .venv/, build/, dist/, .vscode/
```

## Requirements

- Python 3.9+ — the latest available version is recommended
- [PySide6](https://pypi.org/project/PySide6/) — installed automatically via `pip install -r requirements.txt` when running from source (a packaged `.exe` bundles it, so end users won't need this)
- [yt-dlp](https://pypi.org/project/yt-dlp/) — must be reachable on your `PATH` as the `yt-dlp` command, since it's invoked via subprocess
- [FFmpeg](https://ffmpeg.org/) — must be reachable on your `PATH` as the `ffmpeg` command, since it's invoked via subprocess

## Installation

> **Note:** the app will eventually be distributed as a portable `.exe` (or an equivalent package for other platforms) — for now, run it from source.

1. Clone the repository:
   ```bash
   git clone https://github.com/AlessVolpe/yt_dlp_fe.git
   cd yt_dlp_fe
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the app from the project root:

```bash
python src/main.py
```

1. Paste a video/audio URL into the input field.
2. Check **Is it a Playlist?** if the URL points to a playlist rather than a single video.
3. Click **Change** to pick a destination folder (defaults to your system Downloads folder).
4. Click **Audio only** or **Download video**.
5. Progress/status messages appear in the activity log in real time, with the badge cycling through "Downloading...", "Converting...", and back to "Idle".

## Contributing

I'm trying to keep this repository as clean as possible, so please follow the [Conventional Branch](https://conventionalbranch.org/) and [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) naming conventions — everything lowercase, including the commit description.

PR titles should follow the same conventional-commit format (`type(scope): description`) with a clear, descriptive summary of the work; please also write a good PR description.

Use the `dlpfe-ci` scope for CI-related PRs and commits, and `dlpfe` for everything else.

CI workflows to enforce this automatically are coming soon.

## Roadmap

- [x] Selector for single video/playlist
- [x] Auto-update feature launching the `yt-dlp -U` command
- [x] Stream real-time yt-dlp progress into the log panel instead of a single log line
- [x] Convert every file downloaded from a playlist, not just a single video
- [ ] Fix unreliable format conversion (`FormatConverter` assumes a `.webm` source file, which isn't always what yt-dlp downloads)
- [ ] Basic URL validation and error handling
- [ ] Output/format/quality selection

## License

Copyright (c) 2026 Alessandro Volpe

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.