"""Écouter : micro -> texte, sur le Mac (faster-whisper). Rien n'est envoyé dehors."""
import queue

import numpy as np

TAUX = 16000


class Oreille:
    def __init__(self, modele: str = "base"):
        from faster_whisper import WhisperModel
        import sounddevice  # noqa: F401  (vérifie la présence du micro)
        self.modele = WhisperModel(modele, device="cpu", compute_type="int8")

    def ecouter(self, max_secondes: float = 12, silence_fin: float = 0.7, seuil: float = 0.012,
                quand_voix=None) -> str:
        """Enregistre jusqu'à un court silence, puis transcrit. quand_voix() est appelé dès qu'on parle."""
        import sounddevice as sd
        q: queue.Queue = queue.Queue()
        bloc = int(TAUX * 0.1)
        morceaux, silence, parle = [], 0.0, False
        with sd.InputStream(samplerate=TAUX, channels=1, blocksize=bloc, callback=lambda d, *_: q.put(d.copy())):
            while True:
                d = q.get()[:, 0]
                fort = float(np.sqrt(np.mean(d ** 2))) > seuil
                if fort and not parle:
                    parle = True
                    if quand_voix:
                        quand_voix()
                if parle:
                    morceaux.append(d)
                else:                            # garde un petit début pour ne pas couper le premier mot
                    morceaux = (morceaux + [d])[-3:]
                silence = 0.0 if fort else silence + 0.1
                if parle and silence >= silence_fin:
                    break
                if parle and len(morceaux) * 0.1 >= max_secondes:
                    break
        audio = np.concatenate(morceaux).astype(np.float32)
        segs, _ = self.modele.transcribe(audio, language="fr", beam_size=1, vad_filter=True,
                                         condition_on_previous_text=False)
        return " ".join(s.text for s in segs).strip()
