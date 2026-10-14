"""Le cerveau : local (Ollama, 0 €) ou Claude (payant, clé à ton nom)."""
import os

import requests

CONSIGNE = (
    "Tu es {nom}, l'assistant vocal personnel de Hilal. Réponds en français, en 1 à 3 phrases courtes, "
    "faites pour être dites à voix haute (pas de listes, pas de markdown). Sois honnête : si tu ne sais pas, dis-le. "
    "Tu ne demandes ni ne répètes jamais de mot de passe, code, numéro de carte ou IBAN. "
    "Tu ne peux rien acheter, payer ni envoyer. Pour une question religieuse qui fait débat, "
    "conseille de demander à une personne de science."
)


class Cerveau:
    def __init__(self, reglages: dict):
        self.r = reglages
        self.consigne = CONSIGNE.format(nom=reglages["nom"])
        self.historique: list[dict] = []

    def repondre(self, question: str) -> str:
        self.historique.append({"role": "user", "content": question})
        self.historique = self.historique[-10:]
        try:
            texte = self._claude() if self.r["cerveau"] == "claude" else self._local()
        except Exception as e:
            self.historique.pop()
            return f"Mon cerveau ne répond pas ({type(e).__name__}). Vérifie qu'il est bien lancé."
        self.historique.append({"role": "assistant", "content": texte})
        return texte

    def _local(self) -> str:
        r = requests.post("http://localhost:11434/api/chat", timeout=120, json={
            "model": self.r["modele_local"], "stream": False,
            "messages": [{"role": "system", "content": self.consigne}] + self.historique,
        })
        r.raise_for_status()
        return r.json()["message"]["content"].strip()

    def _claude(self) -> str:
        import anthropic  # installé seulement si Hilal choisit Claude
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        msg = client.messages.create(model=self.r["modele_claude"], max_tokens=300,
                                     system=self.consigne, messages=self.historique)
        return "".join(b.text for b in msg.content if b.type == "text").strip()
