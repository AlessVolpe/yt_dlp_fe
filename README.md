# YT-DLP Front End

A lightweight desktop GUI for [yt-dlp](https://github.com/yt-dlp/yt-dlp), built
with [PySide6](https://doc.qt.io/qtforpython-6/) (Qt for Python). Paste a URL, pick a destination, and download audio or
video.

## Status

🚧 **Early development.** The interface is fully built out and download requests are now wired to real `yt-dlp`
subprocess calls (previously these were placeholder echoes). Packaging via PyInstaller (`main.spec`) is also in place
for building a standalone executable.

### For collaborators

Please I'm trying to keep this repository as clean as possible and I want to ask you to
use [conventional branch](https://conventionalbranch.org/)
and [conventional commits](https://www.conventionalcommits.org/en/v1.0.0/) naming conventions (please only lowercase).
PRs must be titled as a commit, giving a comprehensive name for the work done; try to make also a good PR description.
Soon I'll try to make the workflows function!

**The scope is (dlpfe-ci) for ci related PRs and commits, (dlpfe) for everything else!**

## Features

- Single-window Qt interface with a grouped Source / Activity / Actions layout
- URL input field
- Destination folder picker ("Change") - downloads are organized into `DLP_AUDIO/` and `DLP_VIDEO/` subfolders inside
  the chosen directory
- Separate **Audio only** and **Download video** actions, each shelling out to `yt-dlp`
- Automatic format convertion from `.webm` to `.wav` for audio and `.mp4` for video (currently unreliable)
- Read-only activity log with an Idle / Downloading status badge

## Project Structure

```
yt_dlp_fe/
├── assets/                          # Icons / static resources (e.g. for packaging)
├── src/
│   ├── config/
│   │   ├── __init__.py
│   │   └── constants.py             # Shared path constants (e.g. ICON_PATH)
│   ├── modules/
│   │   ├── bll/                     # Business/backend logic
│   │   │   ├── __init__.py
│   │   │   ├── format_converter.py
│   │   │   ├── process_worker.py    # Background QThread: runs a command, logs output live
│   │   │   └── runner.py            # Runner: builds and runs the yt-dlp subprocess calls
│   │   ├── guis/                    # GUI windows
│   │   │   ├── __init__.py
│   │   │   ├── progress_window.py   # Startup update-check window
│   │   │   └── user_interface.py    # Main application window
│   │   ├── loggers/                 # Real-time logging plumbing
│   │   │   ├── __init__.py
│   │   │   └── log_handler.py       # Bridges Python `logging` records into a Qt signal
│   │   └── __init__.py
│   └── main.py                      # Application entry point
├── requirements.txt
├── .gitignore
└── README.md
```

## Requirements

- Python 3.9+ - I recommend the latest version available
- [PySide6](https://pypi.org/project/PySide6/) - automatically installed if you're building the project
- [yt-dlp](https://pypi.org/project/yt-dlp/) - must be reachable on your `PATH` as the `yt-dlp` command, since it's
  invoked via subprocess
- [FFmpeg](https://ffmpeg.org/) - must be reachable on your `PATH` as the `ffmpeg` command, since it's invoked via
  subprocess

## Installation

### N.B.: The application will be released as a portable `.exe` or packaged nonetheless

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
2. Click **Change** to pick a destination folder (defaults to your system Downloads folder).
3. Click **Audio only** or **Download video**.
4. Progress/status messages appear in the activity log, with the badge switching to "Downloading...".

## Roadmap

- [x] Selector for single video/playlist
- [x] Auto-update feature launching the `yt-dlp -U` command
- [x] Stream real-time yt-dlp progress into the log panel instead of a single log line
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
