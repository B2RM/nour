"""Les seules actions que Nour sait faire (liste fermée)."""
import datetime as dt
import json
import threading
import webbrowser
from pathlib import Path
from typing import Callable

import requests

PRIERES = {"fajr": "Fajr", "sobh": "Fajr", "sobh ": "Fajr", "dhuhr": "Dhuhr", "dohr": "Dhuhr",
           "zohr": "Dhuhr", "asr": "Asr", "maghrib": "Maghrib", "maghreb": "Maghrib",
           "isha": "Isha", "icha": "Isha"}


class Carnet:
    def __init__(self, dossier: Path):
        self.fichier = dossier / "carnet.json"

    def _lire(self) -> list:
        if self.fichier.exists():
            return json.loads(self.fichier.read_text(encoding="utf-8"))
        return []

    def noter(self, texte: str) -> str:
        notes = self._lire()
        notes.append({"quand": f"{dt.datetime.now():%d/%m %H:%M}", "texte": texte})
        self.fichier.write_text(json.dumps(notes, ensure_ascii=False, indent=1), encoding="utf-8")
        return f"C'est noté : {texte}."

    def relire(self, combien: int = 5) -> str:
        notes = self._lire()[-combien:]
        if not notes:
            return "Ton carnet est vide."
        return "Tes dernières notes : " + " ; ".join(n["texte"] for n in notes) + "."

    def effacer(self) -> str:
        self.fichier.write_text("[]", encoding="utf-8")
        return "Carnet vidé."


class Rappels:
    def __init__(self, dire: Callable[[str], None]):
        self.dire = dire
        self.actifs: list[threading.Timer] = []

    def programmer(self, minutes: float, quoi: str) -> str:
        t = threading.Timer(minutes * 60, self.dire, args=(f"Rappel : {quoi}.",))
        t.daemon = True
        t.start()
        self.actifs.append(t)
        heure = dt.datetime.now() + dt.timedelta(minutes=minutes)
        return f"D'accord, je te rappelle à {heure:%H:%M} : {quoi}."


def horaires_priere(ville: str, pays: str, methode: int, get=requests.get) -> dict:
    r = get("https://api.aladhan.com/v1/timingsByCity",
            params={"city": ville, "country": pays, "method": methode}, timeout=10)
    r.raise_for_status()
    return r.json()["data"]["timings"]


def repondre_priere(mot: str | None, reglages: dict, get=requests.get) -> str:
    try:
        h = horaires_priere(reglages["ville"], reglages["pays"], reglages["methode_priere"], get)
    except Exception:
        return "Je n'arrive pas à récupérer les horaires de prière pour le moment."
    ville = reglages["ville"]
    if mot:
        nom = PRIERES[mot]
        return f"{nom} est à {h[nom]} à {ville}."
    maintenant = f"{dt.datetime.now():%H:%M}"
    for nom in ("Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"):
        if h[nom] > maintenant:
            return f"La prochaine prière est {nom}, à {h[nom]} à {ville}."
    return f"Isha est passée. Demain, Fajr est vers {h['Fajr']} à {ville}."


def ouvrir_site(nom: str, reglages: dict, ouvrir=webbrowser.open) -> str:
    url = reglages["sites"].get(nom)
    if not url:
        connus = ", ".join(reglages["sites"])
        return f"Je ne connais pas ce site. Ceux que je peux ouvrir : {connus}."
    ouvrir(url)
    return f"J'ouvre {nom}."
