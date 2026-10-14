import re
from urllib.parse import quote

from .. import web

ORDRE = 70
DESCRIPTION = "chercher dans Wikipédia, par exemple : qui était Ibn Khaldoun"
MOTIF = re.compile(r"^(?:qui est|qui etait|qui c'est|c'est quoi|c'etait quoi|qu'est-ce que c'est que|qu'est-ce qu'(?:un|une|on appelle)|parle-moi de|dis-moi ce qu'est|definition de) (.+)")


def agir(m, brut, ctx):
    sujet = re.match(r"^(?:qui est|qui était|qui etait|qui c'est|c'est quoi|c'était quoi|qu'est-ce que c'est que|qu'est-ce qu'on appelle|qu'est-ce qu'un|qu'est-ce qu'une|parle-moi de|dis-moi ce qu'est|définition de|definition de)\s+(.+)", brut.strip(" ?!."), re.I)
    sujet = (sujet.group(1) if sujet else m.group(1)).strip(" ?!.")
    try:
        trouve = web.json_de(ctx, "https://fr.wikipedia.org/w/api.php", action="opensearch", search=sujet,
                             limit=1, namespace=0, format="json")[1]
        if not trouve:
            return None
        d = web.json_de(ctx, f"https://fr.wikipedia.org/api/rest_v1/page/summary/{quote(trouve[0])}")
    except Exception:
        return None          # le cerveau prend le relais
    texte = d.get("extract", "")
    if not texte or d.get("type") == "disambiguation":
        return None
    phrases = re.split(r"(?<=[.!?])\s+", texte)
    return " ".join(phrases[:2]) + " (Wikipédia)"
