# yt-dlp Front End

A lightweight desktop GUI for [yt-dlp](https://github.com/yt-dlp/yt-dlp), built with [PySide6](https://doc.qt.io/qtforpython-6/) (Qt for Python). Paste a URL, pick audio or video, and go.

## Status

🚧 **Work in progress.** The interface is functional — URL input, a log window, and audio/video buttons all work — but the download actions are currently stubbed out (they echo a status message rather than invoking yt-dlp). Actual download logic is coming next.

## Features

- Simple, single-window Qt interface
- URL input field
- Read-only log/output panel for status messages
- Separate **Download Audio Only** and **Download Video** actions

## Project Structure

```
yt_dlp_fe/
├── modules/
│   └── GUI.py          # Main GUI widget (QWidget) and layout
├── main.py               # Application entry point
├── requirements.txt       # Python dependencies
├── .gitignore
└── README.md
```

## Requirements

- Python 3.9+
- [PySide6](https://pypi.org/project/PySide6/)
- [yt-dlp](https://pypi.org/project/yt-dlp/) (for the upcoming download integration)

Exact pinned versions are listed in `requirements.txt`.

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
python main.py
```

1. Paste a video/audio URL into the input field.
2. Click **Download Audio Only** or **Download Video**.
3. Progress/status messages appear in the log panel below the input.

## Roadmap

- [ ] Wire the buttons up to real `yt-dlp` calls
- [ ] Stream download progress into the log panel
- [ ] Basic URL validation and error handling
- [ ] Output/format/quality selection

## License

Add your license of choice here (e.g. MIT).