"""Le cerveau : local (Ollama, 0 €) ou Claude (payant, clé à ton nom).
Pour aller vite : le modèle reste chargé en mémoire, et Nour commence à parler
dès la première phrase prête (sans attendre la fin de la réponse)."""
import datetime as dt
import json
import os
import re
import time

import requests

CONSIGNE = (
    "Tu es {nom}, l'assistant vocal personnel de Hilal. Nous sommes le {date}. Réponds en français, "
    "en 1 à 3 phrases courtes, faites pour être dites à voix haute (pas de listes, pas de markdown, pas d'émojis). "
    "Va droit au but. Sois honnête : si tu ne sais pas, dis-le. "
    "Tu ne demandes ni ne répètes jamais de mot de passe, code, numéro de carte ou IBAN. "
    "Tu ne peux rien acheter, payer ni envoyer. Pour une question religieuse qui fait débat, "
    "conseille de demander à une personne de science.{memoire}"
)
OLLAMA = "http://localhost:11434"
# Toujours les MÊMES réglages : si la taille de contexte change d'un appel à l'autre, Ollama recharge
# tout le modèle (plusieurs secondes perdues à chaque fois : c'était une cause de lenteur).
OPTIONS = {"num_ctx": 4096, "temperature": 0.6}
GARDER = "6h"                 # le cerveau reste chargé 6 h : pas d'attente au réveil
_FIN_PHRASE = re.compile(r"(.+?[.!?…])(\s+|$)", re.S)


class Cerveau:
    def __init__(self, reglages: dict, memoire=None):
        self.r = reglages
        self.memoire = memoire
        self.historique: list[dict] = []
        self.vitesse = None         # mots (jetons) par seconde, mesuré au démarrage

    def consigne(self) -> str:
        mem = self.memoire.pour_le_cerveau() if self.memoire else ""
        return CONSIGNE.format(nom=self.r["nom"], date=f"{dt.date.today():%d/%m/%Y}", memoire=mem)

    def ollama_pret(self, lancer=None, attente=25) -> bool:
        """Ollama répond-il ? Sinon on l'ouvre (l'application est déjà installée) et on attend un peu."""
        def ok():
            try:
                return requests.get(f"{OLLAMA}/api/tags", timeout=2).ok
            except Exception:
                return False
        if ok():
            return True
        try:
            (lancer or (lambda: __import__("subprocess").Popen(["open", "-a", "Ollama"])))()
        except Exception:
            return False
        for _ in range(attente):
            time.sleep(1)
            if ok():
                return True
        return False

    def prechauffer(self) -> None:
        """Charge le modèle à l'avance (mêmes réglages que les vraies questions) et mesure sa vitesse."""
        if self.r["cerveau"] == "claude":
            return
        try:
            r = requests.post(f"{OLLAMA}/api/chat", timeout=180, json={
                "model": self.r["modele_local"], "stream": False, "keep_alive": GARDER,
                "options": {**OPTIONS, "num_predict": 12},
                "messages": [{"role": "user", "content": "Dis bonjour en trois mots."}]})
            d = r.json()
            if d.get("eval_duration"):
                self.vitesse = round(d["eval_count"] / (d["eval_duration"] / 1e9), 1)
        except Exception:
            pass

    def repondre(self, question: str, au_fil=None) -> str:
        """au_fil(phrase) est appelé pour chaque phrase dès qu'elle est prête (si fourni)."""
        self.historique.append({"role": "user", "content": question})
        self.historique = self.historique[-12:]
        try:
            if self.r["cerveau"] == "claude":
                texte = self._claude()
                if au_fil:
                    au_fil(texte)
            else:
                texte = self._local(au_fil)
        except Exception as e:
            self.historique.pop()
            return f"Mon cerveau ne répond pas ({type(e).__name__}). Vérifie qu'Ollama est bien ouvert."
        self.historique.append({"role": "assistant", "content": texte})
        return texte

    def appeler(self, systeme: str, messages: list[dict], max_mots: int = 200, au_fil=None) -> str:
        """Appel direct, utilisé par l'équipe (directeur et managers). Ne touche pas l'historique."""
        if self.r["cerveau"] == "claude":
            texte = self._claude(systeme, messages, max_mots)
            if au_fil:
                au_fil(texte)
            return texte
        return self._local(au_fil, systeme, messages, max_mots)

    def _local(self, au_fil=None, systeme=None, messages=None, max_mots=200) -> str:
        r = requests.post(f"{OLLAMA}/api/chat", timeout=(5, 90), stream=True, json={
            "model": self.r["modele_local"], "stream": True, "keep_alive": GARDER,
            "options": {**OPTIONS, "num_predict": max_mots},
            "messages": [{"role": "system", "content": systeme or self.consigne()}] + (messages or self.historique),
        })
        r.raise_for_status()
        tout, tampon = "", ""
        for ligne in r.iter_lines():
            if not ligne:
                continue
            morceau = json.loads(ligne)
            bout = morceau.get("message", {}).get("content", "")
            tout += bout
            tampon += bout
            while au_fil and (m := _FIN_PHRASE.match(tampon)) and m.group(2):
                au_fil(m.group(1).strip())
                tampon = tampon[m.end():]
            if morceau.get("done"):
                break
        if au_fil and tampon.strip():
            au_fil(tampon.strip())
        return tout.strip()

    def _claude(self, systeme=None, messages=None, max_mots=300) -> str:
        import anthropic  # installé seulement si Hilal choisit Claude
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        msg = client.messages.create(model=self.r["modele_claude"], max_tokens=max_mots,
                                     system=systeme or self.consigne(), messages=messages or self.historique)
        return "".join(b.text for b in msg.content if b.type == "text").strip()
