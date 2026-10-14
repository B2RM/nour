"""Parler. Piper (voix française naturelle) si installé, sinon la voix du système."""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def fabriquer_dire(dossier: Path, voix_mac: str = "systeme", debit_mac: int = 165):
    modele = dossier / "voix" / "fr_FR-siwis-medium.onnx"
    if shutil.which("piper") and modele.exists():
        def dire(texte: str):
            print(f"🔊 {texte}")
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                subprocess.run(["piper", "-m", str(modele), "-f", f.name], input=texte.encode(), check=True,
                               capture_output=True)
                _jouer(f.name)
        return dire
    if sys.platform == "darwin":
        def dire(texte: str):
            print(f"🔊 {texte}")
            subprocess.run(commande_say(voix_mac, debit_mac, texte))
        return dire
    try:
        import pyttsx3
        moteur = pyttsx3.init()
        for v in moteur.getProperty("voices"):
            if "fr" in (v.id + v.name).lower():
                moteur.setProperty("voice", v.id)
                break

        def dire(texte: str):
            print(f"🔊 {texte}")
            moteur.say(texte)
            moteur.runAndWait()
        return dire
    except Exception:
        return lambda texte: print(f"🔊 {texte}")


def _jouer(chemin: str):
    if sys.platform.startswith("win"):
        import winsound
        winsound.PlaySound(chemin, winsound.SND_FILENAME)
    elif sys.platform == "darwin":
        subprocess.run(["afplay", chemin])
    else:
        subprocess.run(["aplay", "-q", chemin])


def voix_francaises_mac() -> list[str]:
    """Noms des voix françaises installées sur le Mac (les meilleures en premier)."""
    sortie = subprocess.run(["say", "-v", "?"], capture_output=True, text=True).stdout
    noms = []
    for ligne in sortie.splitlines():
        if " fr_" in ligne:
            noms.append(ligne.split(" fr_")[0].strip())
    rang = lambda n: 0 if "premium" in n.lower() else 1 if ("enhanced" in n.lower() or "amélior" in n.lower()) else 2
    return sorted(noms, key=rang)


def commande_say(voix: str, debit: int, texte: str) -> list[str]:
    """Sans nom de voix, le Mac prend sa voix système (celle de Contenu énoncé, Siri compris)."""
    cmd = ["say", "-r", str(debit)]
    if voix and voix.lower() not in {"systeme", "système"}:
        cmd += ["-v", voix]
    return cmd + [texte]
