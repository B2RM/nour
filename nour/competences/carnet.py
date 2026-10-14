import re

ORDRE = 20
DESCRIPTION = "noter ce que tu me dis, te le relire, ou vider ton carnet"
_EFFACER = re.compile(r"(efface|vide) (?:mon |le )?carnet")
_RELIRE = re.compile(r"(qu'est-ce que j'ai note|mes notes|relis (?:mes|le) (?:notes|carnet)|mes taches)")
_NOTER = re.compile(r"^(?:note|notes|ecris|retiens) (?:que |qu')?(.+)")
MOTIF = re.compile("|".join(f"(?:{p.pattern})" for p in (_EFFACER, _RELIRE, _NOTER)))


def agir(m, brut, ctx):
    t = m.string
    if _EFFACER.search(t):
        ctx.journal("carnet", "vidé")
        return ctx.carnet.effacer()
    if _RELIRE.search(t):
        return ctx.carnet.relire()
    texte = re.sub(r"^\s*\w+\s+(?:que |qu')?", "", brut, count=1, flags=re.I).rstrip(" .")
    ctx.journal("note", texte)
    return ctx.carnet.noter(texte)
