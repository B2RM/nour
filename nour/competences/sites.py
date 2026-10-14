import re

from .. import outils

ORDRE = 40
DESCRIPTION = "ouvrir un de tes sites, par exemple : ouvre YouTube"
MOTIF = re.compile(r"^(?:ouvre|lance|va sur) (?:le |la |l'|mon |ma |mes )?(\w+)")


def agir(m, brut, ctx):
    kw = {"ouvrir": ctx.ouvrir} if ctx.ouvrir else {}
    ctx.journal("ouvrir", m.group(1))
    return outils.ouvrir_site(m.group(1), ctx.r, **kw)
