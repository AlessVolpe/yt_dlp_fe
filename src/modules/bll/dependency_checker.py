import shutil
from dataclasses import dataclass

from packaging import dependency_groups


@dataclass(frozen=True)
class Dependency:
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

def is_available(exe) -> bool:
    return shutil.which(exe) is not None


def find_missing_dependencies() -> tuple[Dependency]:
    return tuple(
        dependency
        for dependency in REQUIRED_DEPENDENCIES
        if not is_available(dependency.executable)
    )