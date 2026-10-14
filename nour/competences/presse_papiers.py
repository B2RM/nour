import re

from .. import mac, securite

ORDRE = 35
DESCRIPTION = "lire, résumer ou traduire ce que tu as copié"
MOTIF = re.compile(r"(lis|resume|traduis|explique)(?:-moi)?(?: en (\w+))? (?:ce que j'ai copie|le presse-papiers|le texte copie)")


def agir(m, brut, ctx):
    texte = (getattr(ctx, "presse_papiers", None) or mac.presse_papiers)().strip()
    if not texte:
        return "Tu n'as rien copié."
    if securite.sensible(texte):
        return securite.REFUS
    action, langue = m.group(1), m.group(2)
    if action == "lis":
        return texte[:1500]
    consignes = {"resume": "Résume en 3 phrases maximum ce texte",
                 "explique": "Explique simplement ce texte",
                 "traduis": f"Traduis en {langue or 'français'} ce texte (traduction seule)"}
    return ctx.cerveau.repondre(f"{consignes[action]} :\n\n{texte[:6000]}")
