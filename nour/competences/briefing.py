import datetime as dt
import re

from .. import outils
from . import meteo

ORDRE = 5
DESCRIPTION = "te faire le point du jour : météo, prochaine prière, tes notes"
MOTIF = re.compile(r"^(?:bonjour|salam|salam aleykoum|salam alaykoum|as-salamu alaykum|briefing|(?:fais-moi |fais moi )?le point(?: du jour)?|mon point du jour|quoi de neuf)$")


def agir(m, brut, ctx):
    h = dt.datetime.now().hour
    salut = "Wa alaykoum salam" if m.string.startswith(("salam", "as-salam")) else ("Bonjour" if h < 18 else "Bonsoir")
    morceaux = [f"{salut} Hilal."]
    try:
        morceaux.append(meteo.agir(meteo.MOTIF.search("meteo"), "météo", ctx))
    except Exception:
        pass
    kw = {"get": ctx.get} if ctx.get else {}
    morceaux.append(outils.repondre_priere(None, ctx.r, **kw))
    n = len(ctx.carnet._lire())
    if n:
        morceaux.append(f"Tu as {n} note{'s' if n > 1 else ''} dans ton carnet.")
    return " ".join(morceaux)
