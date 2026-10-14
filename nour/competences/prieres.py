import re

from .. import outils

ORDRE = 30
DESCRIPTION = "te donner les heures de prière, par exemple : c'est quand Asr"
MOTIF = re.compile(r"\b(fajr|sobh|dhuhr|dohr|zohr|asr|maghrib|maghreb|isha|icha|priere)\b")


_QUESTION = re.compile(r"\b(islam|coran|hadith|sunna|preuves?|dalil|importance|pourquoi|merite|que dit|comment faire)\b")


def agir(m, brut, ctx):
    if _QUESTION.search(m.string):
        return None          # une question sur la prière (pas l'heure) : l'équipe répond, avec preuves
    mot = None if m.group(1) == "priere" else m.group(1)
    kw = {"get": ctx.get} if ctx.get else {}
    return outils.repondre_priere(mot, ctx.r, **kw)
