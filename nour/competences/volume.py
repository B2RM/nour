import re

from .. import mac

ORDRE = 45
DESCRIPTION = "régler le son du Mac, par exemple : monte le son, volume à 30"
MOTIF = re.compile(r"(monte|augmente|baisse|diminue|coupe|remets|reactive)(?: le| un peu le)? (?:son|volume)|volume a (\d+)|(mets le son|son) a (\d+)")


def agir(m, brut, ctx):
    if not mac.SUR_MAC:
        return "Je ne peux régler le son que sur le Mac."
    t = m.string
    chiffre = re.search(r"a (\d+)", t)
    if chiffre:
        mac.regler_volume(int(chiffre.group(1)))
        return f"Volume à {min(100, int(chiffre.group(1)))}."
    if "coupe" in t:
        mac.couper_son(True)
        return "Son coupé."
    if "remets" in t or "reactive" in t:
        mac.couper_son(False)
        return "Son remis."
    v = mac.volume()
    nv = v + 15 if ("monte" in t or "augmente" in t) else v - 15
    mac.regler_volume(nv)
    return f"Volume à {max(0, min(100, nv))}."
