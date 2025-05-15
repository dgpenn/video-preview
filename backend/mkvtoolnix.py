import json
import subprocess
from pathlib import Path
import shutil


def get_metadata_title(video: Path) -> str:
    """
    Get metadata title for a given MKV file
    """
    mkvmerge = Path(shutil.which("mkvmerge"))
    if not mkvmerge:
        raise FileNotFoundError("mkvmerge not in PATH!")

    command = [mkvmerge.as_posix(), "-J", video.as_posix()]

    try:
        output = subprocess.check_output(command, stderr=subprocess.DEVNULL)
        data = json.loads(output)

        if "container" in data:
            if "properties" in data["container"]:
                if "title" in data["container"]["properties"]:
                    return data["container"]["properties"]["title"].strip()

    except subprocess.CalledProcessError:
        return ""


def set_metadata_title(title: str, video: Path) -> None:
    """
    Set metadata title for a given MKV file
    """
    title = title.strip()
    mkvpropedit = Path(shutil.which("mkvpropedit"))
    if not mkvpropedit:
        raise FileNotFoundError("mkvpropedit not in PATH!")
    command = [
        mkvpropedit.as_posix(),
        video.as_posix(),
        "--edit",
        "info",
        "--set",
        "title={}".format(title),
    ]
    try:
        subprocess.check_call(
            command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    except subprocess.CalledProcessError:
        pass
