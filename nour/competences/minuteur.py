import re

ORDRE = 12
DESCRIPTION = "lancer un minuteur, par exemple : minuteur de 10 minutes"
MOTIF = re.compile(r"(?:minuteur|chrono|compte a rebours|timer)(?: de| d'| pour)? (\d+(?:[.,]\d+)?|\w+) (secondes?|minutes?|min|heures?)")
_NOMBRES = {"une": 1, "un": 1, "deux": 2, "trois": 3, "quatre": 4, "cinq": 5, "six": 6, "sept": 7, "huit": 8,
            "neuf": 9, "dix": 10, "quinze": 15, "vingt": 20, "trente": 30, "quarante": 40, "soixante": 60}


def agir(m, brut, ctx):
    n = m.group(1)
    try:
        val = float(n.replace(",", ".")) if n[0].isdigit() else _NOMBRES[n]
    except (KeyError, ValueError):
        return "Je n'ai pas compris la durée du minuteur."
    u = m.group(2)
    minutes = val / 60 if u.startswith("seconde") else val * 60 if u.startswith("heure") else val
    libelle = f"{n} {u}"
    ctx.journal("minuteur", libelle)
    ctx.rappels.programmer(minutes, f"le minuteur de {libelle} est terminé")
    return f"Minuteur de {libelle} lancé."
