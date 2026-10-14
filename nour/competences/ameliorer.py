"""Boucle d'amélioration (idée de la vidéo 1) : Nour note ses erreurs ;
Hilal colle la liste à Claude, qui corrige et pousse la mise à jour."""
import datetime as dt
import json
import re

ORDRE = 3
DESCRIPTION = "noter mes erreurs pour que je m'améliore : dis « c'est faux » quand je me trompe"
_FAUX = re.compile(r"^(?:c'est faux|c'est pas ca|ce n'est pas ca|tu t'es trompe|tu te trompes|mauvaise reponse|non c'est faux)")
_LISTE = re.compile(r"(qu'est-ce que tu dois ameliorer|tes erreurs|liste (?:de )?tes erreurs)")
MOTIF = re.compile(f"(?:{_FAUX.pattern})|(?:{_LISTE.pattern})")


def fichier(ctx):
    return ctx.r["dossier"] / "a-ameliorer.json"


def noter(ctx, demande, reponse, pourquoi):
    f = fichier(ctx)
    liste = json.loads(f.read_text(encoding="utf-8")) if f.exists() else []
    liste.append({"quand": f"{dt.datetime.now():%d/%m %H:%M}", "demande": demande, "reponse": reponse,
                  "pourquoi": pourquoi})
    f.write_text(json.dumps(liste[-100:], ensure_ascii=False, indent=1), encoding="utf-8")


def agir(m, brut, ctx):
    if _LISTE.search(m.string):
        f = fichier(ctx)
        liste = json.loads(f.read_text(encoding="utf-8")) if f.exists() else []
        if not liste:
            return "Je n'ai noté aucune erreur pour l'instant."
        return (f"J'ai noté {len(liste)} erreur{'s' if len(liste) > 1 else ''}. La liste est dans l'écran de Nour, "
                "bouton « Mes erreurs » : copie-la et envoie-la à Claude pour qu'il me corrige.")
    if not ctx.dernier:
        return "Je n'ai encore rien dit à corriger."
    demande, reponse = ctx.dernier
    noter(ctx, demande, reponse, brut)
    return "Merci, j'ai noté mon erreur. Claude pourra me corriger."
