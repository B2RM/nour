import re
import webbrowser
from urllib.parse import quote_plus

ORDRE = 42
DESCRIPTION = "lancer une recherche, par exemple : cherche recette de couscous sur YouTube"
MOTIF = re.compile(r"^(?:cherche|recherche|trouve-moi|montre-moi)(?: moi)? (.+?)(?: sur (youtube|google|maps|wikipedia))?$")
URLS = {"google": "https://www.google.com/search?q=", "youtube": "https://www.youtube.com/results?search_query=",
        "maps": "https://www.google.com/maps/search/", "wikipedia": "https://fr.wikipedia.org/w/index.php?search="}
NOMS = {"google": "Google", "youtube": "YouTube", "maps": "Google Maps", "wikipedia": "Wikipédia"}


def agir(m, brut, ctx):
    ou = m.group(2) or "google"
    quoi = re.sub(r"^(?:cherche|recherche|trouve-moi|montre-moi)(?: moi)?\s+", "", brut.strip(" ?!."), flags=re.I)
    quoi = re.sub(rf"\s+sur\s+{ou}$", "", quoi, flags=re.I)
    (ctx.ouvrir or webbrowser.open)(URLS[ou] + quote_plus(quoi))
    ctx.journal("recherche", f"{ou} : {quoi}")
    return f"Je cherche « {quoi} » sur {NOMS[ou]}."
