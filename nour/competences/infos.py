import re
import xml.etree.ElementTree as ET

from .. import web

ORDRE = 65
DESCRIPTION = "te lire les titres de l'actualité"
MOTIF = re.compile(r"(les infos|l'info|actualites?|les actus|les nouvelles|quoi de neuf dans le monde|les titres)")
FLUX = "https://www.francetvinfo.fr/titres.rss"


def titres(ctx, n=5) -> list[str]:
    r = web.get(ctx)(FLUX, timeout=10)
    r.raise_for_status()
    racine = ET.fromstring(r.content)
    return [i.findtext("title").strip() for i in racine.iter("item")][:n]


def agir(m, brut, ctx):
    try:
        t = titres(ctx)
    except Exception:
        return "Je n'arrive pas à avoir les infos pour le moment."
    if not t:
        return "Je n'ai trouvé aucun titre."
    return "Les titres de franceinfo : " + " ... ".join(t) + "."
