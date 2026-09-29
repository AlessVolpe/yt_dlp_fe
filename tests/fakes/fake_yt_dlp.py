"""Deterministic stand-in for the ``yt-dlp`` command-line client.

Behaviour is driven by the ``yt-dlp`` section of the JSON file referenced by
``FAKE_BIN_CONFIG``. Supported options:

* ``exit_code`` (int): process exit status; non-zero writes nothing.
* ``extensions`` (list[str]): extensions cycled over-produced files.
* ``playlist_items`` (int): number of items produced in playlist mode.
* ``write_files`` (bool): set to ``False`` to produce no output at all.
* ``delay`` (float): seconds to sleep before producing output.
* ``stdout`` (list[str]): lines printed to stdout.
* ``update_exit_code`` (int): exit status for the ``-U`` self-update call.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Dict, List
from urllib.parse import parse_qs, urlparse

from _common import load_config, log_call


def _video_id(url: str) -> str:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    if "v" in query:
        return query["v"][0]
    return parsed.path.rstrip("/").rsplit("/", 1)[-1]


def _write(template: str, fields: Dict[str, str]) -> None:
    rendered = template
    for key, value in fields.items():
        rendered = rendered.replace(f"%({key})s", value)
    target = Path(rendered)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"fake-media")


def main(argv: List[str]) -> int:
    config = load_config()
    log_call(config, "yt-dlp", argv)
    options = config.get("yt-dlp", {})

    if "-U" in argv:
        print("yt-dlp is up to date", flush=True)
        return int(options.get("update_exit_code", 0))

    for line in options.get("stdout", ["[download] fake yt-dlp run"]):
        print(line, flush=True)

    delay = float(options.get("delay", 0))
    if delay:
        time.sleep(delay)

    exit_code = int(options.get("exit_code", 0))
    if exit_code:
        print("ERROR: fake yt-dlp failure", file=sys.stderr, flush=True)
        return exit_code
    if not options.get("write_files", True):
        return 0

    template = argv[argv.index("-o") + 1]
    url = argv[-1]
    extensions = options.get("extensions", ["webm"])

    if "--yes-playlist" in argv:
        playlist_id = parse_qs(urlparse(url).query).get("list", ["PLfake"])[0]
        count = int(options.get("playlist_items", 3))
        width = len(str(count))
        for index in range(1, count + 1):
            _write(template, {
                "id": f"vid{index:08d}",
                "ext": extensions[(index - 1) % len(extensions)],
                "playlist_id": playlist_id,
                "playlist_index": str(index).zfill(width),
            })
    else:
        _write(template, {"id": _video_id(url), "ext": extensions[0]})
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
