"""Actions sur le Mac (seulement des choses sans risque : ouvrir, son, presse-papiers)."""
import subprocess
import sys
from pathlib import Path

SUR_MAC = sys.platform == "darwin"


def applications() -> dict:
    """Nom simplifié -> nom exact des applications installées."""
    apps = {}
    for dossier in (Path("/Applications"), Path("/System/Applications"), Path.home() / "Applications"):
        if dossier.exists():
            for a in dossier.glob("*.app"):
                apps[a.stem.lower()] = a.stem
    return apps


def ouvrir_app(nom_exact: str) -> None:
    subprocess.run(["open", "-a", nom_exact])


def osascript(script: str) -> str:
    return subprocess.run(["osascript", "-e", script], capture_output=True, text=True).stdout.strip()


def volume() -> int:
    try:
        return int(osascript("output volume of (get volume settings)"))
    except ValueError:
        return 50


def regler_volume(v: int) -> None:
    osascript(f"set volume output volume {max(0, min(100, v))}")


def couper_son(oui: bool) -> None:
    osascript(f"set volume output muted {'true' if oui else 'false'}")


def presse_papiers() -> str:
    return subprocess.run(["pbpaste"], capture_output=True, text=True).stdout
