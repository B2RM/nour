import math
import re

from .. import web

ORDRE = 31
DESCRIPTION = "t'indiquer la direction de la qibla"
MOTIF = re.compile(r"(qibla|direction de la mecque|ou est la mecque)")
KAABA = (21.4225, 39.8262)
_POINTS = ["le nord", "le nord-est", "l'est", "le sud-est", "le sud", "le sud-ouest", "l'ouest", "le nord-ouest"]


def cap(lat, lon) -> float:
    p1, p2 = math.radians(lat), math.radians(KAABA[0])
    dl = math.radians(KAABA[1] - lon)
    x = math.sin(dl) * math.cos(p2)
    y = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def agir(m, brut, ctx):
    try:
        l = web.lieu(ctx)
    except Exception:
        return "Je n'arrive pas à situer ta ville pour le moment."
    c = cap(l["lat"], l["lon"])
    return (f"Depuis {l['nom']}, la qibla est à {round(c)} degrés par rapport au nord, "
            f"donc vers {_POINTS[round(c / 45) % 8]}. Vérifie avec la boussole de ton téléphone.")
