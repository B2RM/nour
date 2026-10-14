"""Une compétence = un fichier dans ce dossier. Pour en ajouter une : copier le modèle ci-dessous.

    ORDRE = 50                      # plus petit = testé en premier
    DESCRIPTION = "ce qu'elle fait, en une phrase dite à voix haute"
    MOTIF = re.compile(r"...")      # sur la demande en minuscules, sans accents

    def agir(m, brut, ctx) -> str:  # m = résultat du motif, brut = demande telle quelle
        return "réponse dite par Nour"

ctx donne : ctx.r (réglages), ctx.carnet, ctx.rappels, ctx.ouvrir, ctx.get, ctx.journal(action, detail).
Règle : une compétence n'achète, ne paie, n'envoie et n'installe rien.
"""
import importlib
import pkgutil


def charger():
    mods = []
    for info in pkgutil.iter_modules(__path__):
        mod = importlib.import_module(f"{__name__}.{info.name}")
        if hasattr(mod, "MOTIF") and hasattr(mod, "agir"):
            mods.append(mod)
    return sorted(mods, key=lambda m: getattr(m, "ORDRE", 50))
