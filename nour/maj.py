"""Mise à jour automatique au démarrage, depuis le dépôt GitHub de Hilal (et lui seul).
Les notes et réglages (~/.nour) ne sont jamais touchés."""
import io
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import requests

ICI = Path(__file__).resolve().parent.parent      # dossier « nour » (code)
A_REMPLACER = ["nour", "tests", "requirements.txt", "README.md", "installer-mac.command", "installer-windows.bat"]


def verifier(depot: str, ici: Path = ICI, get=requests.get) -> str | None:
    """Renvoie un message si une mise à jour a été installée, None sinon. Ne plante jamais."""
    if not depot:
        return None
    try:
        r = get(f"https://api.github.com/repos/{depot}/commits/main", timeout=8,
                headers={"Accept": "application/vnd.github+json"})
        r.raise_for_status()
        sha = r.json()["sha"]
        marque = ici / ".version"
        if marque.exists() and marque.read_text().strip() == sha:
            return None
        z = get(f"https://codeload.github.com/{depot}/zip/{sha}", timeout=60)
        z.raise_for_status()
        avant = (ici / "requirements.txt").read_text() if (ici / "requirements.txt").exists() else ""
        with tempfile.TemporaryDirectory() as tmp:
            zipfile.ZipFile(io.BytesIO(z.content)).extractall(tmp)
            racine = next(Path(tmp).iterdir())
            if not (racine / "nour" / "__main__.py").exists():
                return None   # contenu inattendu : on ne touche à rien
            for nom in A_REMPLACER:
                src, dst = racine / nom, ici / nom
                if not src.exists():
                    continue
                if dst.is_dir():
                    shutil.rmtree(dst)
                if src.is_dir():
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)
        if (ici / "requirements.txt").read_text() != avant:
            subprocess.run([sys.executable, "-m", "pip", "install", "--user", "-q", "-r",
                            str(ici / "requirements.txt")])
        marque.write_text(sha)
        return "J'ai appris de nouvelles choses. Redémarrage."
    except Exception:
        return None
