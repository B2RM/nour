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
from .bibliotheque import Bibliotheque

REGLES = ("Règles de la maison : honnêteté totale (pas de mensonge, pas de fausse urgence, pas de faux avis), "
          "rien de haram (alcool, porc, jeux d'argent, intérêts/riba, contenu indécent), pas de promesse de revenus "
          "ni de promesse médicale, respect du droit français. Réponds en français.")

MANAGERS = {
    "redaction": {
        "titre": "Manager rédaction",
        "domaines": ["marketing"],
        "mots": ["ecris", "redige", "message", "mail", "e-mail", "lettre", "post", "texte", "legende", "slogan",
                 "annonce", "description", "reponds a", "reformule", "corrige"],
        "role": "Tu es le manager rédaction de Nour. Tu écris des textes clairs, chaleureux et professionnels, "
                "prêts à copier. Va à l'essentiel."},
    "business": {
        "titre": "Manager business",
        "mots": ["business", "commerce", "e-commerce", "boutique", "client", "vente", "vendre", "prix", "marge",
                 "produit", "shopify", "pignon", "satr", "concurrent", "strategie", "idee", "argent", "gagner",
                 "lancer", "entreprise", "bezos", "buffett", "jobs", "walton", "hormozi", "revenu"],
        "domaines": ["business", "marketing", "religion"],
        "role": "Tu es le manager business de Nour, expert en e-commerce et petites entreprises françaises, "
                "inspiré des plus grands entrepreneurs (Bezos, Walton, Buffett…) et de l'éthique du commerce en islam. "
                "Tu donnes des conseils concrets, chiffrés quand c'est possible, avec la prochaine action à faire. "
                "Tu dis clairement ce qui est une estimation."},
    "marketing": {
        "titre": "Manager marketing",
        "mots": ["marketing", "pub", "publicite", "accroche", "hook", "tiktok", "instagram", "reseaux", "audience",
                 "abonnes", "contenu", "video", "ogilvy", "positionnement", "persuasion", "convertir", "attirer"],
        "domaines": ["marketing", "business"],
        "role": "Tu es le manager marketing de Nour, formé aux méthodes des maîtres (Ogilvy, Schwartz, Godin, "
                "Cialdini en version honnête). Tu proposes des idées concrètes et testables, jamais de fausse "
                "urgence ni de faux avis."},
    "religion": {
        "titre": "Manager religion",
        "mots": ["islam", "coran", "hadith", "sunna", "prophete", "allah", "halal", "haram", "riba", "zakat",
                 "preuve", "dalil", "verset", "sourate", "musulman", "religion", "licite", "illicite", "savant"],
        "domaines": ["religion"],
        "role": "Tu es le manager religion de Nour. Tu réponds avec des preuves : tu cites UNIQUEMENT les versets "
                "et hadiths présents dans les SOURCES fournies, avec leur référence exacte (ex. Coran 2:275, "
                "Bukhari 2079). Tu n'inventes jamais une référence ni un texte. Si les sources ne suffisent pas, "
                "dis-le simplement. Tu ne donnes pas de fatwa : pour un cas précis ou un point qui fait débat, "
                "conseille de demander à une personne de science."},
    "organisation": {
        "titre": "Manager organisation",
        "domaines": [],
        "mots": ["plan", "planning", "planifie", "organise", "programme", "etapes", "liste", "priorites",
                 "emploi du temps", "semaine", "routine", "objectif"],
        "role": "Tu es le manager organisation de Nour. Tu fais des plans simples et réalistes, en étapes "
                "numérotées courtes, avec un ordre de priorité."},
    "savoir": {
        "titre": "Manager savoir",
        "mots": ["explique", "comment", "pourquoi", "difference", "compare", "apprends", "resume", "c'est quoi"],
        "domaines": None,
        "role": "Tu es le manager savoir de Nour. Tu expliques simplement, avec un exemple concret. "
                "Si tu n'es pas sûr, tu le dis."},
}

# Demandes qui méritent l'équipe (sinon : réponse directe, plus rapide)
TACHE = re.compile(r"^(?:ecris|redige|prepare|fais[- ]moi|aide[- ]moi|donne[- ]moi des idees|propose|planifie|organise|"
                   r"cree|trouve[- ]moi des idees|explique[- ]moi en detail|compare|reformule|corrige|analyse|"
                   r"fais un plan|fais une liste)"
                   # questions d'expert : religion avec preuves, business, marketing
                   r"|.*\b(?:islam|coran|hadith|sunna|prophete|halal|haram|riba|zakat|dalil|avec (?:des )?preuves?)\b"
                   r"|^(?:comment|quelle est la meilleure facon de|que ferait|que dirait|qu'aurait fait|"
                   r"donne-moi des conseils|des conseils|quels conseils|quelle strategie)\b.*\b(?:vendre|lancer|"
                   r"gagner|argent|clients?|business|commerce|boutique|marketing|pub|entreprise|bezos|buffett|"
                   r"jobs|walton|produit|prix|audience|abonnes|vente)")
# Références religieuses : « Coran 2:275 », « sourate 2 verset 275 », « Bukhari 2079 », « Muslim 1532 »...
_REF_CORAN = re.compile(r"(?:coran|sourate)\s*(\d{1,3})\s*(?::|,|\.|verset)\s*(\d{1,3})")
_REF_HADITH = re.compile(r"(bukhari|boukhari|muslim|mouslim|tirmidhi|tirmidhi|abu dawud|abou daoud|abu dawoud|"
                         r"nasa'?i|ibn majah|ibn maja)\D{0,12}?(\d{1,5})")
_RECUEILS = {"boukhari": "bukhari", "mouslim": "muslim", "abou daoud": "abu dawud", "abu dawoud": "abu dawud",
             "nasai": "nasa'i", "ibn maja": "ibn majah"}
_INTERDIT = re.compile(r"(revenu garanti|gains? garantis?|devenir riche|guerit|guerison assuree|100 ?% efficace|"
                       r"casino|paris sportifs|credit a taux)", re.I)
_ANGLAIS = re.compile(r"\b(the|and|you|is|with|for|this)\b", re.I)


def _simple(t: str) -> str:
    t = unicodedata.normalize("NFD", t.lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def choisir_manager(demande: str) -> str:
    t = _simple(demande)
    scores = {nom: sum(1 for mot in m["mots"] if mot in t) for nom, m in MANAGERS.items()}
    if scores["religion"]:          # une question de religion va toujours au manager religion (preuves)
        return "religion"
    meilleur = max(scores, key=scores.get)
    return meilleur if scores[meilleur] else "savoir"


def decouper(demande: str) -> list[str]:
    """Plusieurs demandes en une ? (« … et aussi … », « ensuite », « ; »)"""
    morceaux = re.split(r"\s*(?:;|\bet aussi\b|\bensuite\b|\bpuis aussi\b)\s*", demande)
    morceaux = [m.strip(" ,.") for m in morceaux if len(m.strip(" ,.")) > 8]
    return morceaux if len(morceaux) > 1 else [demande]


def references(texte: str) -> set[str]:
    """Les références citées dans un texte, normalisées : « coran 2:275 », « bukhari 2079 »."""
    t = _simple(texte)
    refs = {f"coran {s}:{v}" for s, v in _REF_CORAN.findall(t)}
    refs |= {f"{_RECUEILS.get(r, r)} {n}" for r, n in _REF_HADITH.findall(t)}
    return refs


def references_inventees(travail: str, sources: str) -> set[str]:
    """Références du travail absentes des sources (un verset d'une plage « 83:1-3 » compte comme présent)."""
    connues = references(sources)
    for s, v1, v2 in re.findall(r"coran (\d{1,3}):(\d{1,3})-(\d{1,3})", _simple(sources)):
        connues |= {f"coran {s}:{v}" for v in range(int(v1), int(v2) + 1)}
    return references(travail) - connues


def controle_gratuit(travail: str, sources: str = "") -> str | None:
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
    if inventees := references_inventees(t, sources):
        return ("la réponse cite des références absentes des sources (" + ", ".join(sorted(inventees)) +
                ") : enlève-les ou remplace-les par celles des sources")
    if re.search(r"(en tant qu'(?:ia|intelligence artificielle|assistant)|je ne peux pas vous aider)", _simple(t)):
        return "la réponse refuse ou tourne autour du pot au lieu d'aider"
    return None


class Directeur:
    def __init__(self, cerveau, suivi=None, bibliotheque=None):
        self.cerveau = cerveau
        self.suivi = suivi or (lambda texte: None)   # affiche le travail de l'équipe à l'écran
        self.bibliotheque = bibliotheque or Bibliotheque()

    def sources(self, nom: str, demande: str) -> str:
        """Les passages de la bibliothèque utiles au manager (0 jeton : recherche par mots-clés)."""
        domaines = MANAGERS[nom].get("domaines", None)
        if domaines == []:
            return ""
        passages = self.bibliotheque.chercher(demande, k=4 if nom == "religion" else 3, domaines=domaines)
        if passages:
            self.suivi("Bibliothèque : " + ", ".join(dict.fromkeys(p["titre"] for p in passages)))
        return Bibliotheque.pour_le_cerveau(passages)

    def _produire(self, nom: str, demande: str, remarque: str | None = None, precedent: str | None = None,
                  sources: str = "") -> str:
        m = MANAGERS[nom]
        systeme = f"{m['role']} {REGLES} Hilal parle par la voix : commence par une phrase de réponse directe."
        if nom == "religion" and not sources:
            systeme += (" Tu n'as AUCUNE source sur ce sujet : ne cite aucune référence, dis que tu n'as pas de "
                        "preuve vérifiée dans ta bibliothèque et conseille une personne de science.")
        systeme += sources
        messages = [{"role": "user", "content": demande}]
        if remarque:
            messages += [{"role": "assistant", "content": precedent or ""},
                         {"role": "user", "content": f"Le directeur refuse ce travail : {remarque}. "
                                                     "Refais-le en corrigeant uniquement ce point."}]
        return self.cerveau.appeler(systeme, messages, max_mots=450).strip()

    def _verifier(self, demande: str, travail: str, sources: str = "") -> str | None:
        raison = controle_gratuit(travail, sources)
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
        sources = self.sources(nom, demande)
        travail = self._produire(nom, demande, sources=sources)
        raison = self._verifier(demande, travail, sources)
        if raison:
            self.suivi(f"Directeur : à reprendre ({raison})")
            nouveau = self._produire(nom, demande, raison, travail, sources)
            if not controle_gratuit(nouveau, sources):          # la reprise n'est revérifiée que gratuitement
                travail = nouveau
            elif references_inventees(travail, sources):       # jamais de fausse référence livrée
                travail = ("Je n'ai pas de preuve vérifiée sur ce point dans ma bibliothèque. "
                           "Pour être sûr, demande à une personne de science.")
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
