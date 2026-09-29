"""Deterministic stand-in for the ``ffmpeg`` command-line tool.

Behaviour is driven by the ``ffmpeg`` section of the JSON file referenced by
``FAKE_BIN_CONFIG``. Supported options:

* ``exit_code`` (int): exit status returned for every invocation.
* ``fail_on`` (str): fail (with ``fail_exit_code``) only when the source path
  contains this substring.
* ``fail_exit_code`` (int): exit status used together with ``fail_on``.
* ``remove_source`` (bool): delete the source file during the conversion.
* ``delay`` (float): seconds to sleep before converting.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import List

from _common import load_config, log_call


def main(argv: List[str]) -> int:
    config = load_config()
    log_call(config, "ffmpeg", argv)
    options = config.get("ffmpeg", {})

    source = argv[argv.index("-i") + 1]
    target = argv[-1]
    print(f"fake ffmpeg: {source} -> {target}", flush=True)

    delay = float(options.get("delay", 0))
    if delay:
        time.sleep(delay)

    exit_code = int(options.get("exit_code", 0))
    fail_on = options.get("fail_on")
    if fail_on and fail_on in source:
        exit_code = int(options.get("fail_exit_code", 1))
    if exit_code:
        print("fake ffmpeg: conversion failed", file=sys.stderr, flush=True)
        return exit_code

    if options.get("remove_source"):
        Path(source).unlink()
    Path(target).write_bytes(b"fake-converted")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
