import re

ORDRE = 8
DESCRIPTION = "te dire ce que j'ai appris aujourd'hui (j'apprends tout seul chaque jour)"
MOTIF = re.compile(r"(qu'as-tu appris|qu'est-ce que tu as appris|tu as appris quoi|t'as appris quoi|"
                   r"ce que tu as appris|ta lecon du jour|quoi de neuf dans ta tete)")


def agir(m, brut, ctx):
    eleve = getattr(ctx, "eleve", None)
    if not eleve:
        return "Mon apprentissage du jour n'est pas lancé."
    appris = eleve.appris_aujourdhui()
    if not appris:
        nouveaux = eleve.session()
        appris = eleve.appris_aujourdhui()
        if not nouveaux and not appris:
            return "Je n'ai encore rien appris aujourd'hui : je n'ai pas réussi à me connecter. Je réessaie plus tard."
    if hasattr(ctx, "recharger_bibliotheque"):
        ctx.recharger_bibliotheque()
    exemple = next((t for t in reversed(appris) if not t.startswith("Coran")), None)
    return ("Aujourd'hui j'ai appris : " + ", ".join(appris) +
            ". C'est rangé dans ma bibliothèque, je m'en sers pour te répondre." +
            (f" Demande-moi par exemple : explique-moi {exemple}." if exemple else ""))
