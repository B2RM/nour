import re

ORDRE = 10
DESCRIPTION = "te faire un rappel, par exemple : rappelle-moi dans 20 minutes de prier"
MOTIF = re.compile(r"rappelle[- ]moi dans (\d+(?:[.,]\d+)?|\w+(?:-\w+)?) (minutes?|min|heures?) (?:de |d'|que |qu')?(.+)")

_NOMBRES = {"une": 1, "un": 1, "deux": 2, "trois": 3, "cinq": 5, "dix": 10, "quinze": 15,
            "vingt": 20, "trente": 30, "quarante": 40, "quarante-cinq": 45, "soixante": 60}


def _duree(nombre: str, unite: str) -> float:
    n = float(nombre.replace(",", ".")) if nombre[0].isdigit() else _NOMBRES[nombre]
    return n * 60 if unite.startswith("heure") else n


def agir(m, brut, ctx):
    try:
        minutes = _duree(m.group(1), m.group(2))
    except (KeyError, ValueError):
        return "Je n'ai pas compris la durée. Dis par exemple : rappelle-moi dans 20 minutes de prier."
    ctx.journal("rappel", f"{minutes} min : {m.group(3)}")
    return ctx.rappels.programmer(minutes, m.group(3))
