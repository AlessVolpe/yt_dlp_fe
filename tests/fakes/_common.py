"""Shared helpers for the fake command-line tools used by the test suite.

The fakes are executed as stand-alone scripts (never imported by pytest), so
this module is resolved through the script directory placed first on
``sys.path`` by the interpreter.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List

CONFIG_ENV_VAR = "FAKE_BIN_CONFIG"


def load_config() -> Dict[str, Any]:
    """Load the JSON behaviour description referenced by ``FAKE_BIN_CONFIG``.

    Returns:
        Dict[str, Any]: The parsed configuration, or an empty mapping when
            the variable is unset or the file does not exist.
    """
    path = os.environ.get(CONFIG_ENV_VAR)
    if not path or not Path(path).is_file():
        return {}
    return json.loads(Path(path).read_text(encoding="utf-8"))


def log_call(config: Dict[str, Any], tool: str, argv: List[str]) -> None:
    """Append one invocation record (JSON lines) to the configured call log.

    Args:
        config (Dict[str, Any]): The configuration returned by `load_config`.
        tool (str): The emulated tool name.
        argv (List[str]): The arguments the tool was invoked with.
    """
    log_path = config.get("log")
    if log_path:
        with open(log_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps({"tool": tool, "argv": argv}) + "\n")
