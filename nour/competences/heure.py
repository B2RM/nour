import datetime as dt
import re

ORDRE = 50
DESCRIPTION = "te dire l'heure et la date"
MOTIF = re.compile(r"^(quelle heure|il est quelle heure|on est quel jour|quel jour)")
_JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]


def agir(m, brut, ctx):
    n = dt.datetime.now()
    return f"Il est {n:%H:%M}, nous sommes {_JOURS[n.weekday()]} {n:%d/%m}."
