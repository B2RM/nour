"""Comprend la demande. Chaque compétence (dossier competences/) reconnaît ses demandes
par des règles fixes (sûr et prévisible) ; tout le reste part au cerveau."""
import re
import unicodedata

from . import competences, journal, outils, securite
from .cerveau import Cerveau

R_AIDE = re.compile(r"(qu'est-ce que tu sais faire|que sais-tu faire|tu sais faire quoi|aide-moi|aide$)")


def _simple(t: str) -> str:
    t = unicodedata.normalize("NFD", t.lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn").strip(" .!?")


class Routeur:
    def __init__(self, reglages: dict, dire, cerveau: Cerveau | None = None, ouvrir=None, get=None):
        self.r = reglages
        self.carnet = outils.Carnet(reglages["dossier"])
        self.rappels = outils.Rappels(dire)
        self.cerveau = cerveau or Cerveau(reglages)
        self.ouvrir = ouvrir
        self.get = get
        self.competences = competences.charger()

    def journal(self, action: str, detail: str = "") -> None:
        journal.ecrire(self.r["dossier"], action, detail)

    def traiter(self, demande: str) -> str:
        brut = demande.strip()
        t = _simple(brut)
        if not t:
            return "Je n'ai rien entendu."
        if securite.sensible(brut):
            self.journal("refus", "donnée sensible")
            return securite.REFUS
        if R_AIDE.search(t):
            return "Je sais " + " ; ".join(c.DESCRIPTION for c in self.competences) + ". Et répondre à tes questions."
        for c in self.competences:
            if m := c.MOTIF.search(t):
                return c.agir(m, brut, self)
        return self.cerveau.repondre(brut)
