"""La bibliothèque de Nour : des fiches d'experts qu'il relit avant de répondre.

- Fiches fournies : nour/savoir/*.md (mises à jour automatiquement depuis GitHub).
- Fiches perso de Hilal : ~/.nour/bibliotheque/*.md (jamais envoyées sur GitHub).
Chaque fiche commence par « # Titre » et une ligne « domaine: … ». Chaque « ## » est un passage.
Recherche par mots-clés (BM25 simplifié) : rapide, gratuite, sans internet.
"""
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path

ICI = Path(__file__).with_name("savoir")
VIDES = set("""a au aux avec ce ces c ca dans de des du elle en et est etre il ils je la le les leur lui ma mais me
meme mes moi mon ne nos notre nous on ou par pas pour qu que qui sa se ses son sur ta te tes toi ton tu un une vos
votre vous y d l j m n s t qu est-ce comment pourquoi quoi quel quelle quels quelles faire fait plus tres bien tout
tous toute sont ont avoir peut dire donne moi dit selon""".split())


def mots(t: str) -> list[str]:
    t = unicodedata.normalize("NFD", t.lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return [m[:7] for m in re.findall(r"[a-z0-9]+", t) if m not in VIDES and len(m) > 1]   # racine grossière


class Bibliotheque:
    def __init__(self, dossiers=None):
        self.passages: list[dict] = []
        for d in dossiers or [ICI, Path.home() / ".nour" / "bibliotheque"]:
            if Path(d).exists():
                for f in sorted(Path(d).glob("*.md")):
                    self._charger(f)
        self.df = Counter(m for p in self.passages for m in set(p["mots"]))
        self.moy = sum(len(p["mots"]) for p in self.passages) / max(1, len(self.passages))

    def _charger(self, f: Path):
        texte = f.read_text(encoding="utf-8")
        titre = (re.search(r"^# (.+)$", texte, re.M) or [None, f.stem])[1].strip()
        domaine = (re.search(r"^domaine: (.+)$", texte, re.M) or [None, "general"])[1].strip()
        for bloc in re.split(r"^## ", texte, flags=re.M)[1:]:
            entete, _, corps = bloc.partition("\n")
            corps = corps.strip()
            if corps:
                self.passages.append({"fiche": titre, "titre": entete.strip(), "domaine": domaine,
                                      "texte": corps, "mots": mots(entete + " " + entete + " " + corps)})

    def chercher(self, question: str, k: int = 3, domaines=None) -> list[dict]:
        q = mots(question)
        n = len(self.passages)
        res = []
        for p in self.passages:
            if domaines and p["domaine"] not in domaines:
                continue
            tf = Counter(p["mots"])
            score = 0.0
            for m in q:
                if tf[m]:
                    idf = math.log(1 + (n - self.df[m] + 0.5) / (self.df[m] + 0.5))
                    score += idf * tf[m] * 2.2 / (tf[m] + 1.2 * (0.25 + 0.75 * len(p["mots"]) / self.moy))
            if score > 0:
                res.append((score, p))
        res.sort(key=lambda x: -x[0])
        return [p for s, p in res[:k] if s >= 0.4 * res[0][0]]   # on écarte ce qui est loin du meilleur

    @staticmethod
    def pour_le_cerveau(passages: list[dict]) -> str:
        if not passages:
            return ""
        return "\n\nSOURCES À UTILISER (cite-les par leur nom, n'invente rien d'autre) :\n" + "\n\n".join(
            f"[{p['fiche']} — {p['titre']}]\n{p['texte']}" for p in passages)
