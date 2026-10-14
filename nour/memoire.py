"""Mémoire à long terme : ce que Hilal demande à Nour de retenir pour toujours.
Stockée sur le Mac (~/.nour/memoire.json), jamais sur GitHub."""
import datetime as dt
import json
import unicodedata
from pathlib import Path


def _simple(t: str) -> str:
    t = unicodedata.normalize("NFD", t.lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


class Memoire:
    def __init__(self, dossier: Path):
        self.fichier = dossier / "memoire.json"

    def faits(self) -> list[dict]:
        if self.fichier.exists():
            return json.loads(self.fichier.read_text(encoding="utf-8"))
        return []

    def _ecrire(self, faits):
        self.fichier.write_text(json.dumps(faits, ensure_ascii=False, indent=1), encoding="utf-8")

    def retenir(self, fait: str) -> str:
        faits = [f for f in self.faits() if f["fait"].lower() != fait.lower()]
        faits.append({"depuis": f"{dt.date.today():%d/%m/%Y}", "fait": fait})
        self._ecrire(faits)
        return f"Je m'en souviendrai : {fait}."

    def oublier(self, mot: str) -> str:
        faits = self.faits()
        restants = [f for f in faits if _simple(mot) not in _simple(f["fait"])]
        if len(restants) == len(faits):
            return "Je n'ai rien trouvé à oublier là-dessus."
        self._ecrire(restants)
        n = len(faits) - len(restants)
        return f"C'est oublié ({n} souvenir{'s' if n > 1 else ''})."

    def tout_oublier(self) -> str:
        self._ecrire([])
        return "J'ai tout oublié."

    def resume(self) -> str:
        faits = self.faits()
        if not faits:
            return "Je ne sais encore rien de toi. Dis-moi : souviens-toi que…"
        return "Voici ce que je sais : " + " ; ".join(f["fait"] for f in faits[-15:]) + "."

    def pour_le_cerveau(self) -> str:
        faits = self.faits()[-40:]
        if not faits:
            return ""
        return "\nCe que tu sais de Hilal (il te l'a demandé) :\n" + "\n".join(f"- {f['fait']}" for f in faits)
