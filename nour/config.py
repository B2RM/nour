"""Réglages. Modifiables dans reglages.json à côté du programme."""
import json
from pathlib import Path

DOSSIER = Path.home() / ".nour"

DEFAUT = {
    "nom": "Nour",                 # mot d'appel
    "ville": "Creil",
    "pays": "France",
    "methode_priere": 12,          # 12 = UOIF (France) sur Aladhan ; réglable
    "voix_mac": "systeme",         # "systeme" = la voix choisie dans Réglages > Contenu énoncé ; sinon un nom (python3 -m nour --voix)
    "debit_mac": 165,              # mots par minute ; plus bas = plus posé (narrateur)
    "depot_maj": "B2RM/nour",      # dépôt GitHub de Nour (mises à jour auto)
    "cerveau": "local",            # "local" (Ollama, 0 €) ou "claude" (payant, clé à ton nom)
    "modele_local": "qwen2.5:7b",  # plus rapide mais moins bon : "qwen2.5:3b"
    "modele_oreille": "base",      # "base" = rapide ; "small" = plus précis mais plus lent
    "interface": True,             # ouvre le bel écran de Nour dans le navigateur
    "modele_claude": "claude-haiku-5-5",
    "sites": {
        "mail": "https://mail.google.com",
        "youtube": "https://www.youtube.com",
        "shopify": "https://admin.shopify.com",
        "agenda": "https://calendar.google.com",
    },
}


def charger(dossier: Path = DOSSIER) -> dict:
    dossier.mkdir(parents=True, exist_ok=True)
    fichier = dossier / "reglages.json"
    reglages = dict(DEFAUT)
    if fichier.exists():
        reglages.update(json.loads(fichier.read_text(encoding="utf-8")))
    else:
        fichier.write_text(json.dumps(DEFAUT, ensure_ascii=False, indent=2), encoding="utf-8")
    reglages["dossier"] = dossier
    return reglages


def enregistrer(cle: str, valeur, dossier: Path = DOSSIER) -> None:
    fichier = dossier / "reglages.json"
    reglages = json.loads(fichier.read_text(encoding="utf-8")) if fichier.exists() else dict(DEFAUT)
    reglages[cle] = valeur
    fichier.write_text(json.dumps(reglages, ensure_ascii=False, indent=2), encoding="utf-8")
