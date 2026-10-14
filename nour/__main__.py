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


VARIANTES_APPEL = {"nour": ["nour", "noor", "nur", "nours", "noure", "nourr", "nhour", "noure", "nooor", "nouhr", "nourre"]}


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
        if verrou_demande.locked():          # jamais de silence : on dit qu'on a bien reçu
            bus.emettre("message", qui="equipe", texte="Bien reçu, je finis la demande d'avant puis je fais celle-ci.")
        with verrou_demande:
            bus.emettre("message", qui="toi", texte=demande)
            bus.emettre("etat", etat="reflechit")
            dits = []
            try:
                rep = routeur.traiter(demande, au_fil=lambda p: (dits.append(p), dire(p, bulle=False)))
            except Exception as e:           # un souci ne doit jamais rendre Nour sourd ou muet
                routeur.journal("erreur", f"traiter : {type(e).__name__} : {e}"[:300])
                rep = "Désolé, j'ai eu un souci sur cette demande. Je l'ai noté. Tu peux réessayer."
            if dits:
                bus.emettre("message", qui="nour", texte=rep)
            elif len(rep) > 350:          # long travail de l'équipe : on dit le début, le reste est à l'écran
                bus.emettre("message", qui="nour", texte=rep)
                debut_rep = " ".join(re.split(r"(?<=[.!?])\s+", rep.strip())[:2])
                dire(debut_rep + " Le détail est sur l'écran.", bulle=False)
            else:
                dire(rep)
            bus.emettre("etat", etat="veille")
            fin_reponse[0] = time.time()

    fin_reponse = [0.0]
    # l'équipe prévient tout de suite (on n'attend pas la fin du travail pour savoir qu'il a compris)
    routeur.annonce = lambda t: threading.Thread(target=dire, args=(t,), kwargs={"bulle": False}, daemon=True).start()

    def reveiller_cerveau():
        if reglages.get("cerveau") != "claude" and not routeur.cerveau.ollama_pret():
            bus.emettre("message", qui="equipe", texte="Ollama ne répond pas : ouvre l'application Ollama.")
            return
        routeur.cerveau.prechauffer()
        if routeur.cerveau.vitesse:
            bus.emettre("message", qui="equipe", texte=f"Cerveau prêt ({routeur.cerveau.vitesse} mots/s).")
            if routeur.cerveau.vitesse < 8 and "3b" not in reglages.get("modele_local", ""):
                bus.emettre("message", qui="equipe",
                            texte="Mon cerveau est lent sur ce Mac. Pour des réponses au tac au tac, dis : « Nour, cerveau rapide ».")

    threading.Thread(target=reveiller_cerveau, daemon=True).start()

    # Apprentissage quotidien, tout seul, quand Nour est libre (et vérifie les nouveautés de Claude sur GitHub)
    from .apprendre import Eleve
    from . import maj

    def appris(titres):
        routeur.recharger_bibliotheque()
        bus.emettre("message", qui="equipe", texte="J'ai appris : " + ", ".join(titres))

    from . import sante

    def controle():
        controles = sante.bilan(routeur, routeur.url_ecran)
        routeur.journal("sante", " | ".join(c["titre"] for c in controles if not c["ok"]) or "tout va bien")
        for a in sante.alertes(controles):
            bus.emettre("message", qui="equipe", texte=f"⚠️ Sécurité : {a}")

    def nouveautes():
        controle()
        if maj.verifier(reglages.get("depot_maj", "")) and not occupe():
            bus.emettre("message", qui="equipe", texte="Nouvelles fiches reçues : je redémarre.")
            os.execv(sys.executable, [sys.executable, "-m", "nour", *sys.argv[1:]])

    routeur.url_ecran = ""
    occupe = lambda: parole["verrou"].locked() or verrou_demande.locked()
    routeur.eleve = Eleve(reglages, apres=appris)
    routeur.eleve.demarrer(occupe=occupe, aussi=nouveautes)

    if reglages.get("interface", True):
        url = demarrer(bus, routeur, traiter)
        routeur.url_ecran = url
        print(f"Écran de {nom} : {url}", flush=True)
        webbrowser.open(url)

    if not micro:
        dire_seul(f"Salam Hilal, {nom} est prêt. Écris-moi dans l'écran.")
        while True:
            time.sleep(3600)

    from .oreille import Oreille
    print("Chargement de l'oreille... (la première fois : téléchargement, quelques minutes)", flush=True)
    oreille = Oreille(reglages.get("modele_oreille", "base"), nom)
    routeur.oreille = oreille
    print("Oreille prête. Le micro écoute.", flush=True)
    motif_appel = motif_d_appel(nom)
    dire_seul("Salam Hilal, je suis prêt.")
    while True:
        try:
            ecouter_une_fois(oreille, motif_appel, parole, bus, dire, dire_seul, traiter, fin_reponse,
                             reglages.get("conversation_secondes", 8))
        except StopIteration:
            break
        except Exception as e:           # micro débranché, etc. : on note, on attend un peu, on réécoute
            routeur.journal("erreur", f"oreille : {type(e).__name__} : {e}"[:300])
            bus.emettre("etat", etat="veille")
            time.sleep(1)


def motif_d_appel(nom: str):
    appels = VARIANTES_APPEL.get(_sans_accents(nom), [_sans_accents(nom)])
    return re.compile(r"\b(" + "|".join(map(re.escape, appels)) + r")\b[\s,.!?]*", re.I)


def extraire_demande(entendu: str, motif_appel, en_conversation: bool) -> str | None:
    """La demande dans ce qui a été entendu. None = pas pour Nour.
    En conversation (juste après une réponse), pas besoin de redire « Nour »."""
    m = motif_appel.search(_sans_accents(entendu))
    if m:
        return entendu[m.end():].strip(" ,.!?")    # même longueur : les accents ne décalent rien
    if en_conversation and len(entendu.strip(" ,.!?")) > 2:
        return entendu.strip(" ,.!?")
    return None


def ecouter_une_fois(oreille, motif_appel, parole, bus, dire, dire_seul, traiter, fin_reponse, conversation):
    import time
    en_conversation = time.time() - fin_reponse[0] < conversation
    debut = time.time()
    entendu = oreille.ecouter(quand_voix=lambda: bus.emettre("etat", etat="ecoute"),
                              attente_max=(conversation if en_conversation else None))
    if parole["verrou"].locked() or parole["fin"] > debut:
        return                          # c'était ma propre voix
    if not entendu:
        bus.emettre("etat", etat="veille")
        return
    demande = extraire_demande(entendu, motif_appel, en_conversation)
    if demande is None:
        bus.emettre("message", qui="equipe", texte=f"(entendu sans « Nour » : {entendu[:80]})")
        bus.emettre("etat", etat="veille")
        return
    if not demande:
        dire("Oui ?", bulle=False)
        bus.emettre("etat", etat="ecoute")
        demande = oreille.ecouter(attente_max=8).strip(" ,.!?")
    if _sans_accents(demande).strip(" .!") in {"stop", "au revoir", "arrete-toi", "eteins-toi"}:
        dire_seul("À bientôt, in sha Allah.")
        raise StopIteration
    if demande:
        traiter(demande)
    else:
        bus.emettre("etat", etat="veille")


if __name__ == "__main__":
    main()
