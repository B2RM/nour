import re
import threading

import requests

from .. import config

ORDRE = 6
DESCRIPTION = "changer de cerveau : « cerveau rapide » (petit, très vif) ou « cerveau normal » (plus réfléchi)"
MOTIF = re.compile(r"^(?:passe en |mets le |prends le |utilise le )?(?:cerveau|mode) (rapide|normal|precis)$")
MODELES = {"rapide": "qwen2.5:3b", "normal": "qwen2.5:7b", "precis": "qwen2.5:7b"}
OLLAMA = "http://localhost:11434"


def agir(m, brut, ctx):
    modele = MODELES[m.group(1)]
    if ctx.r.get("cerveau") == "claude":
        return "J'utilise Claude en ce moment, ce réglage concerne seulement le cerveau local."
    try:
        presents = [x["name"] for x in requests.get(f"{OLLAMA}/api/tags", timeout=3).json().get("models", [])]
    except Exception:
        return "Ollama ne répond pas. Ouvre l'application Ollama, puis redemande-moi."

    def basculer():
        ctx.r["modele_local"] = modele
        config.enregistrer("modele_local", modele, ctx.r["dossier"])
        if hasattr(ctx.cerveau, "prechauffer"):
            ctx.cerveau.prechauffer()

    if any(n.startswith(modele) for n in presents):
        threading.Thread(target=basculer, daemon=True).start()
        return f"C'est fait, je passe au cerveau {m.group(1)}."

    def telecharger():          # Hilal l'a demandé : gratuit, environ 2 Go, une seule fois
        try:
            requests.post(f"{OLLAMA}/api/pull", json={"model": modele, "stream": False}, timeout=3600)
            basculer()
            ctx.rappels.dire(f"Mon cerveau {m.group(1)} est prêt.")
        except Exception:
            pass

    threading.Thread(target=telecharger, daemon=True).start()
    return (f"Je télécharge le cerveau {m.group(1)} (gratuit, environ 2 Go, une seule fois). "
            "Je continue avec l'ancien en attendant, je te préviens quand c'est prêt.")
