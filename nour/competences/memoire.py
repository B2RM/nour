import re

ORDRE = 15
DESCRIPTION = "me souvenir de toi pour toujours, par exemple : souviens-toi que je n'aime pas le café"
_OUBLIER_TOUT = re.compile(r"oublie tout")
_OUBLIER = re.compile(r"^oublie (?:que |qu'|ce que je t'ai dit sur |tout sur )?(.+)")
_RESUME = re.compile(r"(qu'est-ce que tu sais (?:de|sur) moi|que sais-tu (?:de|sur) moi|tu te souviens de quoi)")
_RETENIR = re.compile(r"^(?:souviens[- ]toi|rappelle[- ]toi|retiens pour toujours|n'oublie pas|memorise) (?:que |qu'|de |d')?(.+)")
MOTIF = re.compile("|".join(f"(?:{p.pattern})" for p in (_OUBLIER_TOUT, _OUBLIER, _RESUME, _RETENIR)))


def _original(brut: str, motif: str) -> str:
    """Récupère le texte d'origine (avec accents) après la formule d'appel."""
    m = re.match(motif, brut, flags=re.I)
    return (m.group(1) if m else brut).strip(" .!?")


def agir(m, brut, ctx):
    t = m.string
    if _OUBLIER_TOUT.search(t):
        ctx.journal("memoire", "tout oublié")
        return ctx.memoire.tout_oublier()
    if _RESUME.search(t):
        return ctx.memoire.resume()
    if _OUBLIER.match(t):
        quoi = _OUBLIER.match(t).group(1)
        ctx.journal("memoire", f"oublier {quoi}")
        return ctx.memoire.oublier(quoi)
    fait = _original(brut, r"^\s*(?:souviens[- ]toi|rappelle[- ]toi|retiens pour toujours|n'oublie pas|m[ée]morise)\s+(?:que |qu'|de |d')?(.+)")
    ctx.journal("memoire", fait)
    return ctx.memoire.retenir(fait)
