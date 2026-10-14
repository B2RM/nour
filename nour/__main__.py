"""Lancer : python -m nour            (voix)
           python -m nour --texte    (clavier, pour tester)"""
import argparse
import os
import sys
import re
import unicodedata

from . import config
from .routeur import Routeur
from .voix import fabriquer_dire


def _sans_accents(t: str) -> str:
    t = unicodedata.normalize("NFD", t.lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def main():
    p = argparse.ArgumentParser(prog="nour")
    p.add_argument("--texte", action="store_true", help="mode clavier")
    p.add_argument("--voix", nargs="?", const="", help="choisir la voix (sans nom : les essayer)")
    p.add_argument("--nom", help="changer le mot d'appel")
    p.add_argument("--debit", type=int, help="vitesse de la voix (ex. 150 = posé, 190 = rapide)")
    a = p.parse_args()
    reglages = config.charger()
    nom = reglages["nom"]

    if a.nom:
        config.enregistrer("nom", a.nom.strip())
        print(f"C'est fait : dis maintenant « {a.nom.strip()} » pour l'appeler.")
        return
    if a.debit:
        import subprocess
        config.enregistrer("debit_mac", a.debit)
        from .voix import commande_say
        subprocess.run(commande_say(reglages.get("voix_mac", "systeme"), a.debit, "Salam Hilal. Voici ma voix, à cette vitesse."))
        print(f"Vitesse enregistrée : {a.debit}")
        return
    if a.voix is not None:
        from .voix import voix_francaises_mac
        import subprocess
        if a.voix:
            config.enregistrer("voix_mac", a.voix)
            from .voix import commande_say
            subprocess.run(commande_say(a.voix, reglages.get("debit_mac", 165), f"Salam Hilal, je suis {nom}. Voici ma nouvelle voix."))
            print(f"Voix enregistrée : {a.voix}")
            return
        noms = voix_francaises_mac()
        if not noms:
            print("Aucune voix française trouvée.")
        for v in noms:
            print(f"→ {v}")
            subprocess.run(["say", "-v", v, "-r", str(reglages.get("debit_mac", 165)),
                            f"Bonjour Hilal, je suis la voix {v}."])
        print('Pour choisir : python3 -m nour --voix "NOM EXACT"')
        return

    from . import maj
    if message := maj.verifier(reglages.get("depot_maj", "")):
        print(message, flush=True)
        os.execv(sys.executable, [sys.executable, "-m", "nour", *sys.argv[1:]])

    if a.texte:
        dire = lambda t: print(f"{nom} : {t}")
        routeur = Routeur(reglages, dire)
        print(f"{nom} est prêt (mode texte). Tape « quitter » pour sortir.")
        while (demande := input("Toi : ").strip()).lower() not in {"quitter", "exit"}:
            dire(routeur.traiter(demande))
        return

    from .oreille import Oreille
    dire = fabriquer_dire(reglages["dossier"], reglages.get("voix_mac", "systeme"), reglages.get("debit_mac", 165))
    routeur = Routeur(reglages, dire)
    print("Chargement de l'oreille... (la première fois : téléchargement d'environ 500 Mo, quelques minutes)", flush=True)
    oreille = Oreille()
    print("Oreille prête. Le micro écoute.", flush=True)
    appel = _sans_accents(nom)
    dire(f"Salam Hilal, {nom} est prêt. Dis « {nom} » puis ta demande.")
    while True:
        entendu = oreille.ecouter()
        simple = _sans_accents(entendu)
        if appel not in simple:
            continue
        parties = re.split(re.escape(nom), entendu, maxsplit=1, flags=re.I)
        demande = (parties[1] if len(parties) > 1 else re.split(re.escape(appel), simple, maxsplit=1)[1]).strip(" ,.!?")
        if not demande:
            dire("Oui ?")
            demande = oreille.ecouter()
        if _sans_accents(demande).strip(" .!") in {"stop", "au revoir", "arrete-toi"}:
            dire("À bientôt, in sha Allah.")
            break
        if demande:
            dire(routeur.traiter(demande))


if __name__ == "__main__":
    main()
