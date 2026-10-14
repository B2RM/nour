"""L'équipe de Nour : un directeur, des managers spécialisés, et des sous-tâches si besoin.

Comment ça marche (et pourquoi c'est économe) :
1. Le directeur découpe la demande en sous-tâches seulement si elle en contient plusieurs (règle fixe, 0 jeton).
2. Il choisit le bon manager par mots-clés (règle fixe, 0 jeton).
3. Le manager produit le travail (1 appel au cerveau).
4. Le directeur vérifie d'abord avec des contrôles gratuits (vide, coupé, anglais, données sensibles,
   promesses interdites…). Seulement si tout est bon, il fait un contrôle très court par le cerveau
   (« OUI/NON + raison », environ 20 mots).
5. S'il refuse, il dit au manager quoi corriger : UNE seule reprise maximum. Puis il livre le meilleur résultat.
"""
import re
import unicodedata

from . import securite

REGLES = ("Règles de la maison : honnêteté totale (pas de mensonge, pas de fausse urgence, pas de faux avis), "
          "rien de haram (alcool, porc, jeux d'argent, intérêts/riba, contenu indécent), pas de promesse de revenus "
          "ni de promesse médicale, respect du droit français. Réponds en français.")

MANAGERS = {
    "redaction": {
        "titre": "Manager rédaction",
        "mots": ["ecris", "redige", "message", "mail", "e-mail", "lettre", "post", "texte", "legende", "slogan",
                 "annonce", "description", "reponds a", "reformule", "corrige"],
        "role": "Tu es le manager rédaction de Nour. Tu écris des textes clairs, chaleureux et professionnels, "
                "prêts à copier. Va à l'essentiel."},
    "business": {
        "titre": "Manager business",
        "mots": ["business", "commerce", "e-commerce", "boutique", "client", "vente", "vendre", "prix", "marge",
                 "produit", "marketing", "pub", "shopify", "pignon", "satr", "concurrent", "strategie", "idee"],
        "role": "Tu es le manager business de Nour, expert en e-commerce et petites entreprises françaises. "
                "Tu donnes des conseils concrets, chiffrés quand c'est possible, avec la prochaine action à faire. "
                "Tu dis clairement ce qui est une estimation."},
    "organisation": {
        "titre": "Manager organisation",
        "mots": ["plan", "planning", "planifie", "organise", "programme", "etapes", "liste", "priorites",
                 "emploi du temps", "semaine", "routine", "objectif"],
        "role": "Tu es le manager organisation de Nour. Tu fais des plans simples et réalistes, en étapes "
                "numérotées courtes, avec un ordre de priorité."},
    "savoir": {
        "titre": "Manager savoir",
        "mots": ["explique", "comment", "pourquoi", "difference", "compare", "apprends", "resume", "c'est quoi"],
        "role": "Tu es le manager savoir de Nour. Tu expliques simplement, avec un exemple concret. "
                "Si tu n'es pas sûr, tu le dis."},
}

# Demandes qui méritent l'équipe (sinon : réponse directe, plus rapide)
TACHE = re.compile(r"^(?:ecris|redige|prepare|fais[- ]moi|aide[- ]moi|donne[- ]moi des idees|propose|planifie|organise|"
                   r"cree|trouve[- ]moi des idees|explique[- ]moi en detail|compare|reformule|corrige|analyse|"
                   r"fais un plan|fais une liste)")
_INTERDIT = re.compile(r"(revenu garanti|gains? garantis?|devenir riche|guerit|guerison assuree|100 ?% efficace|"
                       r"casino|paris sportifs|credit a taux)", re.I)
_ANGLAIS = re.compile(r"\b(the|and|you|is|with|for|this)\b", re.I)


def _simple(t: str) -> str:
    t = unicodedata.normalize("NFD", t.lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def choisir_manager(demande: str) -> str:
    t = _simple(demande)
    scores = {nom: sum(1 for mot in m["mots"] if mot in t) for nom, m in MANAGERS.items()}
    meilleur = max(scores, key=scores.get)
    return meilleur if scores[meilleur] else "savoir"


def decouper(demande: str) -> list[str]:
    """Plusieurs demandes en une ? (« … et aussi … », « ensuite », « ; »)"""
    morceaux = re.split(r"\s*(?:;|\bet aussi\b|\bensuite\b|\bpuis aussi\b)\s*", demande)
    morceaux = [m.strip(" ,.") for m in morceaux if len(m.strip(" ,.")) > 8]
    return morceaux if len(morceaux) > 1 else [demande]


def controle_gratuit(travail: str) -> str | None:
    """Renvoie la raison du refus, ou None si rien à redire. Ne coûte aucun jeton."""
    t = travail.strip()
    if len(t) < 15:
        return "la réponse est vide ou beaucoup trop courte"
    if securite.sensible(t):
        return "la réponse contient une donnée sensible (mot de passe, carte, IBAN)"
    if _INTERDIT.search(_simple(t)):
        return "la réponse contient une promesse ou un sujet interdit par nos règles"
    mots = re.findall(r"\w+", t)
    if mots and len(_ANGLAIS.findall(t)) / len(mots) > 0.08:
        return "la réponse n'est pas en français"
    if t[-1] not in ".!?»)…:" and not t.endswith(("\n",)) and len(t) > 300:
        return "la réponse semble coupée au milieu"
    if re.search(r"(en tant qu'(?:ia|intelligence artificielle|assistant)|je ne peux pas vous aider)", _simple(t)):
        return "la réponse refuse ou tourne autour du pot au lieu d'aider"
    return None


class Directeur:
    def __init__(self, cerveau, suivi=None):
        self.cerveau = cerveau
        self.suivi = suivi or (lambda texte: None)   # affiche le travail de l'équipe à l'écran

    def _produire(self, nom: str, demande: str, remarque: str | None = None, precedent: str | None = None) -> str:
        m = MANAGERS[nom]
        systeme = f"{m['role']} {REGLES} Hilal parle par la voix : commence par une phrase de réponse directe."
        messages = [{"role": "user", "content": demande}]
        if remarque:
            messages += [{"role": "assistant", "content": precedent or ""},
                         {"role": "user", "content": f"Le directeur refuse ce travail : {remarque}. "
                                                     "Refais-le en corrigeant uniquement ce point."}]
        return self.cerveau.appeler(systeme, messages, max_mots=450).strip()

    def _verifier(self, demande: str, travail: str) -> str | None:
        raison = controle_gratuit(travail)
        if raison:
            return raison
        avis = self.cerveau.appeler(
            "Tu es le directeur. Tu vérifies le travail d'un manager. Réponds uniquement « OUI » s'il répond "
            "correctement à la demande, sinon « NON : » suivi de la raison en 12 mots maximum.",
            [{"role": "user", "content": f"Demande : {demande}\n\nTravail rendu :\n{travail[:2500]}"}],
            max_mots=25).strip()
        if _simple(avis).startswith("non"):
            return avis.split(":", 1)[-1].strip() or "la réponse ne répond pas à la demande"
        return None

    def traiter_une(self, demande: str) -> str:
        nom = choisir_manager(demande)
        titre = MANAGERS[nom]["titre"]
        self.suivi(f"Directeur → {titre}")
        travail = self._produire(nom, demande)
        raison = self._verifier(demande, travail)
        if raison:
            self.suivi(f"Directeur : à reprendre ({raison})")
            nouveau = self._produire(nom, demande, raison, travail)
            if not controle_gratuit(nouveau):          # la reprise n'est revérifiée que gratuitement
                travail = nouveau
            self.suivi(f"{titre} : corrigé")
        else:
            self.suivi("Directeur : vérifié ✓")
        return travail

    def traiter(self, demande: str) -> str:
        parts = decouper(demande)
        if len(parts) == 1:
            return self.traiter_une(demande)
        self.suivi(f"Directeur : {len(parts)} sous-tâches")
        return "\n\n".join(self.traiter_une(p) for p in parts)
