"""Écouter : micro -> texte, sur le PC (faster-whisper). Rien n'est envoyé dehors."""
import queue

import numpy as np

TAUX = 16000


class Oreille:
    def __init__(self, modele: str = "small"):
        from faster_whisper import WhisperModel
        import sounddevice  # noqa: F401  (vérifie la présence du micro)
        self.modele = WhisperModel(modele, device="cpu", compute_type="int8")

    def ecouter(self, max_secondes: float = 12, silence_fin: float = 1.2, seuil: float = 0.01) -> str:
        """Enregistre jusqu'à un silence, puis transcrit."""
        import sounddevice as sd
        q: queue.Queue = queue.Queue()
        bloc = int(TAUX * 0.1)
        morceaux, silence, parle = [], 0.0, False
        with sd.InputStream(samplerate=TAUX, channels=1, blocksize=bloc, callback=lambda d, *_: q.put(d.copy())):
            while len(morceaux) * 0.1 < max_secondes:
                d = q.get()[:, 0]
                morceaux.append(d)
                fort = float(np.sqrt(np.mean(d ** 2))) > seuil
                parle = parle or fort
                silence = 0.0 if fort else silence + 0.1
                if parle and silence >= silence_fin:
                    break
        if not parle:
            return ""
        audio = np.concatenate(morceaux).astype(np.float32)
        segs, _ = self.modele.transcribe(audio, language="fr", vad_filter=True)
        return " ".join(s.text for s in segs).strip()
