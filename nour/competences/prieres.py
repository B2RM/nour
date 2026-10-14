import re

from .. import outils

ORDRE = 30
DESCRIPTION = "te donner les heures de prière, par exemple : c'est quand Asr"
MOTIF = re.compile(r"\b(fajr|sobh|dhuhr|dohr|zohr|asr|maghrib|maghreb|isha|icha|priere)\b")


def agir(m, brut, ctx):
    mot = None if m.group(1) == "priere" else m.group(1)
    kw = {"get": ctx.get} if ctx.get else {}
    return outils.repondre_priere(mot, ctx.r, **kw)
