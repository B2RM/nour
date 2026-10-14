import re

from .. import sante

ORDRE = 7
DESCRIPTION = "faire mon bilan de santé et de sécurité : « bilan de santé »"
MOTIF = re.compile(r"(bilan de sante|controle de securite|tu vas bien|tout va bien chez toi|verifie[- ]toi)")


def agir(m, brut, ctx):
    controles = sante.bilan(ctx, getattr(ctx, "url_ecran", ""))
    rates = [c for c in controles if not c["ok"]]
    if not rates:
        return (f"Tout va bien : {len(controles)} contrôles réussis, sécurité comprise. "
                "Le détail est dans le bouton Santé de l'écran.")
    return (f"{len(controles) - len(rates)} contrôles sur {len(controles)} sont bons. À regarder : " +
            " ; ".join(c["titre"] for c in rates) + ". Le détail est dans le bouton Santé, à copier pour Claude.")
