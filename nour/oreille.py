"""Écouter : micro -> texte, sur le Mac (faster-whisper). Rien n'est envoyé dehors.

Le seuil de voix s'adapte tout seul au bruit de la pièce (au lieu d'un seuil fixe qui ratait les voix douces),
et Whisper est prévenu (hotwords) que le mot « Nour » va revenir souvent (il l'écrit mieux).
"""
import queue
from collections import deque

import numpy as np

TAUX = 16000


def seuil_pour(bruit: float) -> float:
    """Seuil de voix : 3 fois le bruit de fond, entre 0,004 et 0,03."""
    return min(0.03, max(0.004, bruit * 3))


class Oreille:
    def __init__(self, modele: str = "base", nom: str = "Nour"):
        from faster_whisper import WhisperModel
        import sounddevice  # noqa: F401  (vérifie la présence du micro)
        self.modele = WhisperModel(modele, device="cpu", compute_type="int8")
        self.nom = nom
        self.niveaux: deque = deque([0.004] * 20, maxlen=150)   # 15 dernières secondes de son

    @property
    def bruit(self) -> float:
        """Bruit de fond de la pièce : le niveau des moments calmes (20e centile des 15 dernières secondes)."""
        return float(np.percentile(self.niveaux, 20))

    @property
    def seuil(self) -> float:
        return seuil_pour(self.bruit)

    def ecouter(self, max_secondes: float = 15, silence_fin: float = 0.8, quand_voix=None,
                attente_max: float | None = None) -> str:
        """Enregistre jusqu'à un court silence, puis transcrit. quand_voix() est appelé dès qu'on parle.
        attente_max : si personne ne parle pendant ce temps, on rend "" (mode conversation)."""
        import sounddevice as sd
        q: queue.Queue = queue.Queue()
        bloc = int(TAUX * 0.1)
        morceaux, silence, parle, attendu = [], 0.0, False, 0.0
        with sd.InputStream(samplerate=TAUX, channels=1, blocksize=bloc, callback=lambda d, *_: q.put(d.copy())):
            while True:
                d = q.get()[:, 0]
                niveau = float(np.sqrt(np.mean(d ** 2)))
                fort = niveau > self.seuil
                self.niveaux.append(niveau)
                if not parle and not fort:
                    attendu += 0.1
                    if attente_max is not None and attendu >= attente_max:
                        return ""
                if fort and not parle:
                    parle = True
                    if quand_voix:
                        quand_voix()
                if parle:
                    morceaux.append(d)
                else:                            # garde un petit début pour ne pas couper le premier mot
                    morceaux = (morceaux + [d])[-4:]
                silence = 0.0 if fort else silence + 0.1
                if parle and silence >= silence_fin:
                    break
                if parle and len(morceaux) * 0.1 >= max_secondes:
                    break
        audio = np.concatenate(morceaux).astype(np.float32)
        options = dict(language="fr", beam_size=1, vad_filter=True, condition_on_previous_text=False)
        try:
            segs, _ = self.modele.transcribe(audio, hotwords=self.nom, **options)
        except TypeError:                       # ancienne version de faster-whisper
            segs, _ = self.modele.transcribe(audio, initial_prompt=self.nom, **options)
        return " ".join(s.text for s in segs).strip()
