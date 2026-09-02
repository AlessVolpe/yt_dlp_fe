# yt-dlp Front End

A lightweight desktop GUI for [yt-dlp](https://github.com/yt-dlp/yt-dlp), built with [PySide6](https://doc.qt.io/qtforpython-6/) (Qt for Python). Paste a URL, pick a destination, and download audio or video.

## Status

🚧 **Early development.** The interface is fully built out and download requests are now wired to real `yt-dlp` subprocess calls (previously these were placeholder echoes). Packaging via PyInstaller (`main.spec`) is also in place for building a standalone executable.

## Features

- Single-window Qt interface with a grouped Source / Activity / Actions layout
- URL input field
- Destination folder picker ("Change") — downloads are organized into `DLP_AUDIO/` and `DLP_VIDEO/` subfolders inside the chosen directory
- Separate **Audio only** and **Download video** actions, each shelling out to `yt-dlp`
- Read-only activity log with an Idle / Downloading status badge

## Project Structure

```
yt_dlp_fe/
├── src/
│   ├── modules/
│   │   ├── runner.py            # Runner: builds and runs the yt-dlp subprocess calls
│   │   └── user_interface.py    # UserInterface: main GUI window
│   └── main.py                   # Application entry point
├── asset/                         # Icons / static resources (e.g. for packaging)
├── requirements.txt
├── main.spec                      # PyInstaller build spec
├── .gitignore
└── README.md

# Generated / git-ignored, not tracked:
# .venv/, build/, dist/, .vscode/
```

## Requirements

- Python 3.9+
- [PySide6](https://pypi.org/project/PySide6/)
- [yt-dlp](https://pypi.org/project/yt-dlp/) — must be reachable on your `PATH` as the `yt-dlp` command, since it's invoked via subprocess
- [FFmpeg](https://ffmpeg.org/) is recommended alongside yt-dlp for format conversion / audio extraction

See `requirements.txt` for pinned versions.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/<your-username>/yt_dlp_fe.git
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

### Building a standalone executable

A PyInstaller spec is included:

```bash
pyinstaller main.spec
```

The build output lands in `build/` and `dist/` (both git-ignored).

## Roadmap

- [ ] Stream real-time yt-dlp progress into the log panel instead of a single log line
- [ ] Basic URL validation and error handling
- [ ] Output/format/quality selection

## License

Copyright (c) 2026 Alessandro Volpe

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.