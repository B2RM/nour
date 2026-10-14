import datetime as dt
from pathlib import Path


def ecrire(dossier: Path, action: str, detail: str = "") -> None:
    ligne = f"{dt.datetime.now():%Y-%m-%d %H:%M:%S} | {action} | {detail}\n"
    with open(dossier / "journal.log", "a", encoding="utf-8") as f:
        f.write(ligne)
