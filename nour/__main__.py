"""Lancer : python -m nour            (voix + écran)
           python -m nour --ecran    (écran seul, sans micro)
           python -m nour --texte    (clavier dans le Terminal, pour tester)"""
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
    p.add_argument("--ecran", action="store_true", help="écran seul, sans micro")
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
            dits = []
            rep = routeur.traiter(demande, au_fil=lambda p: (dits.append(p), print(f"{nom} : {p}", flush=True)))
            if not dits:
                dire(rep)
        return

    lancer(reglages, micro=not a.ecran)


VARIANTES_APPEL = {"nour": ["nour", "noor", "nur", "nours", "noure", "nourr"]}


def lancer(reglages, micro=True):
    import threading
    import time
    import webbrowser
    from .interface import Bus, demarrer

    nom = reglages["nom"]
    bus = Bus()
    dire_brut = fabriquer_dire(reglages["dossier"], reglages.get("voix_mac", "systeme"), reglages.get("debit_mac", 165))
    parole = {"verrou": threading.Lock(), "fin": 0.0}

    def dire(texte, bulle=True):
        with parole["verrou"]:
            bus.emettre("etat", etat="parle")
            if bulle:
                bus.emettre("message", qui="nour", texte=texte)
            dire_brut(texte)
            parole["fin"] = time.time()

    def dire_seul(texte):           # rappels et minuteurs, qui arrivent à tout moment
        dire(texte)
        bus.emettre("etat", etat="veille")

    routeur = Routeur(reglages, dire_seul)
    routeur.suivi = lambda t: bus.emettre("message", qui="equipe", texte=t)
    verrou_demande = threading.Lock()

    def traiter(demande):
        with verrou_demande:
            bus.emettre("message", qui="toi", texte=demande)
            bus.emettre("etat", etat="reflechit")
            dits = []
            rep = routeur.traiter(demande, au_fil=lambda p: (dits.append(p), dire(p, bulle=False)))
            if dits:
                bus.emettre("message", qui="nour", texte=rep)
            elif len(rep) > 350:          # long travail de l'équipe : on dit le début, le reste est à l'écran
                bus.emettre("message", qui="nour", texte=rep)
                debut_rep = " ".join(re.split(r"(?<=[.!?])\s+", rep.strip())[:2])
                dire(debut_rep + " Le détail est sur l'écran.", bulle=False)
            else:
                dire(rep)
            bus.emettre("etat", etat="veille")

    threading.Thread(target=routeur.cerveau.prechauffer, daemon=True).start()
    if reglages.get("interface", True):
        url = demarrer(bus, routeur, traiter)
        print(f"Écran de {nom} : {url}", flush=True)
        webbrowser.open(url)

    if not micro:
        dire_seul(f"Salam Hilal, {nom} est prêt. Écris-moi dans l'écran.")
        while True:
            time.sleep(3600)

    from .oreille import Oreille
    print("Chargement de l'oreille... (la première fois : téléchargement, quelques minutes)", flush=True)
    oreille = Oreille(reglages.get("modele_oreille", "base"))
    print("Oreille prête. Le micro écoute.", flush=True)
    appels = VARIANTES_APPEL.get(_sans_accents(nom), [_sans_accents(nom)])
    motif_appel = re.compile(r"\b(" + "|".join(map(re.escape, appels)) + r")\b[\s,.!?]*", re.I)
    dire_seul("Salam Hilal, je suis prêt.")
    while True:
        debut = time.time()
        entendu = oreille.ecouter(quand_voix=lambda: bus.emettre("etat", etat="ecoute"))
        if parole["verrou"].locked() or parole["fin"] > debut:
            continue                    # c'était ma propre voix
        simple = _sans_accents(entendu)
        m = motif_appel.search(simple)
        if not m:
            bus.emettre("etat", etat="veille")
            continue
        demande = entendu[m.end():].strip(" ,.!?")   # même longueur : les accents ne décalent rien
        if not demande:
            dire("Oui ?", bulle=False)
            bus.emettre("etat", etat="ecoute")
            demande = oreille.ecouter().strip(" ,.!?")
        if _sans_accents(demande).strip(" .!") in {"stop", "au revoir", "arrete-toi", "eteins-toi"}:
            dire_seul("À bientôt, in sha Allah.")
            break
        if demande:
            traiter(demande)
        else:
            bus.emettre("etat", etat="veille")


if __name__ == "__main__":
    main()
