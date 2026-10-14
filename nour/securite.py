"""Garde-fou : rien de sensible n'entre dans le carnet ni ne part vers le cerveau."""
import re

_MOTIFS = [
    (re.compile(r"\b(?:\d[ -]?){13,19}\b"), "numéro de carte"),
    (re.compile(r"\bFR\d{2}(?:\s?\w{4}){5,6}", re.I), "IBAN"),
    (re.compile(r"\b(mot de passe|mdp|password|code pin|code secret|cryptogramme|cvv)\b", re.I), "secret"),
]


def sensible(texte: str) -> str | None:
    """Renvoie le type de donnée sensible trouvée, ou None."""
    for motif, nom in _MOTIFS:
        if motif.search(texte):
            return nom
    return None


REFUS = ("Je ne garde et ne transmets jamais ce genre d'information "
         "(mot de passe, code, carte, IBAN). Garde-la dans un gestionnaire de mots de passe.")
