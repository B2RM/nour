"""Nour apprend tout seul, tous les jours, sans qu'on le lui demande.

Comme quelqu'un qui ouvre le dictionnaire chaque matin, mais dans ce qu'il pratique :
- quelques leçons par jour (commerce, marketing, histoire du commerce en islam), lues sur Wikipédia ;
- un verset du Coran par jour, dans l'ordre, avec sa référence exacte (traduction du sens, Hamidullah) ;
- chaque leçon est rangée dans sa bibliothèque perso (~/.nour/bibliotheque) : il s'en sert ensuite pour répondre.
- les fiches d'expert que Claude prépare arrivent en plus par la mise à jour automatique.

Pour ne pas alourdir le Mac : pas de cerveau utilisé pour apprendre (juste du texte téléchargé, quelques Ko),
seulement quand Nour ne parle pas, et la bibliothèque perso est plafonnée (20 Mo par défaut :
les plus vieux mois sont effacés au-delà).
"""
import datetime as dt
import json
import re
import threading
import time
from pathlib import Path
from urllib.parse import quote

import requests

from . import securite

PROGRAMME = Path(__file__).with_name("savoir") / "programme.json"
UA = {"User-Agent": "Nour/0.6 (assistant personnel ; github.com/B2RM/nour)"}
NB_VERSETS = 6236


class Eleve:
    def __init__(self, reglages: dict, get=None, apres=None):
        self.dossier = Path(reglages["dossier"])
        self.biblio = self.dossier / "bibliotheque"
        self.fichier_etat = self.dossier / "apprentissage.json"
        self.par_jour = int(reglages.get("lecons_par_jour", 3))
        self.max_octets = int(float(reglages.get("bibliotheque_max_mo", 20)) * 1_000_000)
        self.get = get or requests.get
        self.apres = apres or (lambda titres: None)      # appelé après de nouvelles leçons
        self.verrou = threading.Lock()

    # --- état (où il en est) ---
    def etat(self) -> dict:
        try:
            return json.loads(self.fichier_etat.read_text(encoding="utf-8"))
        except Exception:
            return {"index": 0, "verset": 0, "jours": {}}

    def _sauver(self, e: dict) -> None:
        jours = dict(sorted(e["jours"].items())[-60:])      # on garde 60 jours d'historique
        e["jours"] = jours
        self.fichier_etat.write_text(json.dumps(e, ensure_ascii=False, indent=1), encoding="utf-8")

    def appris_aujourdhui(self) -> list[str]:
        return self.etat()["jours"].get(dt.date.today().isoformat(), [])

    # --- les sources ---
    def _json(self, url, **params):
        r = self.get(url, params=params or None, timeout=10, headers=UA)
        r.raise_for_status()
        return r.json()

    def _wikipedia(self, sujet: str) -> tuple[str, str] | None:
        trouve = self._json("https://fr.wikipedia.org/w/api.php", action="opensearch", search=sujet, limit=1,
                            namespace=0, format="json")[1]
        if not trouve:
            return None
        d = self._json(f"https://fr.wikipedia.org/api/rest_v1/page/summary/{quote(trouve[0])}")
        texte = (d.get("extract") or "").strip()
        if not texte or d.get("type") == "disambiguation":
            return None
        return trouve[0], texte[:1500]

    def _verset(self, numero: int) -> tuple[str, str]:
        d = self._json(f"https://api.alquran.cloud/v1/ayah/{numero}/fr.hamidullah")["data"]
        ref = f"Coran {d['surah']['number']}:{d['numberInSurah']}"
        return ref, f"{ref} (sens, traduction Hamidullah) : « {d['text'].strip()} »"

    # --- ranger ---
    def _ecrire(self, domaine: str, titre: str, texte: str, source: str) -> None:
        if securite.sensible(texte) or securite.sensible(titre):
            return                   # rien qui ressemble à un code ou une carte n'entre dans la bibliothèque
        texte = texte.replace("\n## ", "\n").replace("\n# ", "\n")   # un texte appris ne peut pas créer de faux passage
        self.biblio.mkdir(parents=True, exist_ok=True)
        f = self.biblio / f"appris-{domaine}-{dt.date.today():%Y-%m}.md"
        if not f.exists():
            f.write_text(f"# Ce que Nour a appris ({domaine}, {dt.date.today():%m/%Y})\ndomaine: {domaine}\n\n",
                         encoding="utf-8")
        with f.open("a", encoding="utf-8") as fh:
            fh.write(f"## {titre}\n{texte}\n(Source : {source}, appris le {dt.date.today():%d/%m/%Y})\n\n")

    def ranger(self) -> None:
        """Plafond de place : au-delà, on efface les leçons des mois les plus anciens."""
        fichiers = sorted(self.biblio.glob("appris-*.md"), key=lambda f: re.findall(r"\d{4}-\d{2}", f.name))
        while fichiers and sum(f.stat().st_size for f in fichiers) > self.max_octets:
            fichiers.pop(0).unlink()

    # --- apprendre ---
    def apprendre_une(self, e: dict) -> str | None:
        """Une leçon : le verset du jour en premier, puis le programme. Renvoie le titre appris."""
        jour = dt.date.today().isoformat()
        deja = e["jours"].setdefault(jour, [])
        if not any(t.startswith("Coran ") for t in deja):
            ref, texte = self._verset(e["verset"] % NB_VERSETS + 1)
            self._ecrire("religion", ref, texte, "api.alquran.cloud")
            e["verset"] += 1
            deja.append(ref)
            return ref
        programme = json.loads(PROGRAMME.read_text(encoding="utf-8"))
        while e["index"] < len(programme):      # le programme s'allonge avec les mises à jour (Claude en ajoute)
            sujet = programme[e["index"]]
            res = self._wikipedia(sujet["sujet"])     # pas d'internet : erreur, on reprendra au même sujet
            e["index"] += 1
            if res:
                titre, texte = res
                self._ecrire(sujet["domaine"], titre, texte, "Wikipédia")
                deja.append(titre)
                return titre
        return None

    def session(self) -> list[str]:
        """Apprend ce qui manque pour aujourd'hui. Ne plante jamais (pas d'internet = on réessaiera)."""
        if not self.verrou.acquire(blocking=False):
            return []
        nouveaux = []
        try:
            e = self.etat()
            while len(e["jours"].get(dt.date.today().isoformat(), [])) < self.par_jour + 1:   # +1 = le verset
                try:
                    titre = self.apprendre_une(e)
                except Exception:
                    break
                if not titre:
                    break
                nouveaux.append(titre)
                self._sauver(e)
            if nouveaux:
                self.ranger()
                self.apres(nouveaux)
        finally:
            self.verrou.release()
        return nouveaux

    def boucle(self, occupe=lambda: False, intervalle=3 * 3600, aussi=None):
        """Tourne en fond toute la journée : apprend dès que Nour est libre. aussi() = autre tâche régulière."""
        time.sleep(20)               # laisse Nour démarrer tranquillement
        while True:
            if not occupe():
                self.session()
                if aussi:
                    try:
                        aussi()
                    except Exception:
                        pass
            time.sleep(intervalle)

    def demarrer(self, occupe=lambda: False, aussi=None) -> threading.Thread:
        t = threading.Thread(target=self.boucle, kwargs={"occupe": occupe, "aussi": aussi}, daemon=True)
        t.start()
        return t
