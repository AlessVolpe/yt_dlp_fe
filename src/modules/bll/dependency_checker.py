import shutil
from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class Dependency:
    """
    An external command-line tool the app depends on.

    Attributes:
        executable (str): The name of the executable to look for on the
            system PATH (e.g. "yt-dlp").
        description (str): A short, human-readable explanation of what
            the app uses this dependency for.
        install_url (str): A URL pointing to installation instructions
            for this dependency.
    """

    executable: str
    description: str
    install_url: str


REQUIRED_DEPENDENCIES = [
    Dependency(
        executable="yt-dlp",
        description="Used to download audio and video from the URL provided",
        install_url="https://github.com/yt-dlp/yt-dlp#installation"
    ),
    Dependency(
        executable="ffmpeg",
        description="Used to convert downloaded files to their final .wav/.mp4 format",
        install_url="https://ffmpeg.org/download.html"
    )
]


def is_available(exe: str) -> bool:
    """
    Check whether an executable is reachable on the system PATH.

    Args:
        exe (str): The name of the executable to look for (e.g. "ffmpeg").

    Returns:
        bool: True if the executable is found on the PATH, False
            otherwise.
    """
    return shutil.which(exe) is not None


def find_missing_dependencies() -> Tuple[Dependency, ...]:
    """
    Determine which required dependencies are missing from the PATH.

    Checks every entry in `REQUIRED_DEPENDENCIES` and collects the ones
    whose executable cannot be found.

    Returns:
        Tuple[Dependency, ...]: The subset of `REQUIRED_DEPENDENCIES`
            that are missing from the system PATH. Empty if every
            dependency is available.
    """
    return tuple(
        dependency
        for dependency in REQUIRED_DEPENDENCIES
        if not is_available(dependency.executable)
    )
