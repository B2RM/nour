import re
import unicodedata

from .. import mac, outils

ORDRE = 40
DESCRIPTION = "ouvrir un site ou une application, par exemple : ouvre YouTube, ouvre Calendrier"
MOTIF = re.compile(r"^(?:ouvre|lance|va sur|demarre) (?:le |la |l'|les |mon |ma |mes |l'application |l'appli )?(.+)")


def _simple(t):
    t = unicodedata.normalize("NFD", t.lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def agir(m, brut, ctx):
    cible = m.group(1).strip()
    mot = cible.split()[0]
    if mot in ctx.r["sites"]:
        kw = {"ouvrir": ctx.ouvrir} if ctx.ouvrir else {}
        ctx.journal("ouvrir", mot)
        return outils.ouvrir_site(mot, ctx.r, **kw)
    apps = getattr(ctx, "apps", None) or (mac.applications() if mac.SUR_MAC else {})
    simples = {_simple(k): v for k, v in apps.items()}
    nom = simples.get(cible) or next((v for k, v in simples.items() if k.startswith(cible) or cible.startswith(k)), None)
    if nom:
        ctx.journal("ouvrir_app", nom)
        (getattr(ctx, "ouvrir_app", None) or mac.ouvrir_app)(nom)
        return f"J'ouvre {nom}."
    connus = ", ".join(ctx.r["sites"])
    return f"Je ne trouve ni site ni application « {cible} ». Sites connus : {connus}."
