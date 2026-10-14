"""Comprend la demande. Chaque compétence (dossier competences/) reconnaît ses demandes
par des règles fixes (sûr et prévisible) ; tout le reste part au cerveau."""
import re
import unicodedata

from . import competences, journal, outils, securite
from .memoire import Memoire
from .equipe import TACHE, Directeur
from .cerveau import Cerveau
from .bibliotheque import ICI as SAVOIR, Bibliotheque

R_AIDE = re.compile(r"(qu'est-ce que tu sais faire|que sais-tu faire|tu sais faire quoi|^aide(?:-moi)?$)")


def _simple(t: str) -> str:
    t = unicodedata.normalize("NFD", t.lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn").strip(" .!?")


class Routeur:
    def __init__(self, reglages: dict, dire, cerveau: Cerveau | None = None, ouvrir=None, get=None):
        self.r = reglages
        self.carnet = outils.Carnet(reglages["dossier"])
        self.memoire = Memoire(reglages["dossier"])
        self.rappels = outils.Rappels(dire)
        self.cerveau = cerveau or Cerveau(reglages, self.memoire)
        self.ouvrir = ouvrir
        self.get = get
        self.apps = None            # tests : faux catalogue d'applications
        self.ouvrir_app = None
        self.presse_papiers = None
        self.dernier = None         # (demande, réponse) : pour « c'est faux »
        self.suivi = None           # l'écran affiche le travail de l'équipe
        self.eleve = None           # l'apprentissage quotidien (branché au lancement)
        self.directeur = Directeur(self.cerveau, lambda t: self.suivi and self.suivi(t), self._bibliotheque())
        self.competences = competences.charger()

    def _bibliotheque(self) -> Bibliotheque:
        return Bibliotheque([SAVOIR, self.r["dossier"] / "bibliotheque"])

    def recharger_bibliotheque(self) -> None:
        """Après une leçon apprise : Nour s'en sert tout de suite."""
        self.directeur.bibliotheque = self._bibliotheque()

    def journal(self, action: str, detail: str = "") -> None:
        journal.ecrire(self.r["dossier"], action, detail)

    def traiter(self, demande: str, au_fil=None) -> str:
        """au_fil : pour dire la réponse du cerveau phrase par phrase, au fur et à mesure."""
        reponse = self._traiter(demande, au_fil)
        if not re.match(r"^\s*(c'est faux|c'est pas ça|ce n'est pas ça|tu t'es trompé)", demande, re.I):
            self.dernier = (demande, reponse)
        return reponse

    def _traiter(self, demande: str, au_fil=None) -> str:
        brut = demande.strip()
        t = _simple(brut)
        if not t:
            return "Je n'ai rien entendu."
        if securite.sensible(brut):
            self.journal("refus", "donnée sensible")
            return securite.REFUS
        if R_AIDE.search(t):
            courts = [c.DESCRIPTION.split(",")[0].split(" : ")[0] for c in self.competences]
            return (f"Je sais faire {len(courts)} choses, par exemple : " + ", ".join(courts[:6]) +
                    ". Et répondre à tes questions. Tout est listé dans l'écran, bouton Compétences.")
        for c in self.competences:
            if m := c.MOTIF.search(t):
                try:
                    rep = c.agir(m, brut, self)
                except Exception as e:
                    self.journal("erreur", f"{c.__name__} : {type(e).__name__}")
                    rep = "Désolé, cette compétence a eu un souci. Je l'ai noté."
                    from .competences import ameliorer
                    ameliorer.noter(self, brut, rep, f"plantage {c.__name__.split('.')[-1]} : {type(e).__name__}")
                if rep is not None:      # None = « pas pour moi », on passe à la suite
                    return rep
        if TACHE.match(t) and hasattr(self.cerveau, "appeler"):
            self.journal("equipe", brut)
            return self.directeur.traiter(brut)
        if au_fil:
            return self.cerveau.repondre(brut, au_fil)
        return self.cerveau.repondre(brut)
