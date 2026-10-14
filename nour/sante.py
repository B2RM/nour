"""Bilan de santé et de sécurité : Nour se contrôle lui-même, au démarrage puis toutes les 3 heures.

Ce qu'il vérifie (sans rien envoyer dehors) :
- son écran n'est visible que depuis ce Mac ;
- son dossier (~/.nour) est privé ;
- aucun mot de passe, carte ou IBAN n'est stocké dans sa mémoire, son carnet ou sa bibliothèque ;
- son code n'a pas été modifié en dehors des mises à jour officielles ;
- les mises à jour ne viennent que du dépôt officiel ;
- ses compétences répondent bien (petits tests sans effet) ;
- son cerveau et son oreille marchent, et à quelle vitesse.
"""
import datetime as dt
import hashlib
import json
import os
import stat
from pathlib import Path

from . import __version__, securite

DEPOT_OFFICIEL = "B2RM/nour"
ICI = Path(__file__).resolve().parent.parent
# petits tests de routage, sans effet : (demande, compétence attendue)
AUTOTESTS = [("quelle heure est-il", "heure"), ("rappelle-moi dans 5 minutes de boire", "rappels"),
             ("c'est quand asr", "prieres"), ("combien font 12 fois 3", "calcul"),
             ("qu'as-tu appris aujourd'hui", "appris")]


def empreintes(ici: Path = ICI) -> dict:
    fichiers = sorted(p for p in (ici / "nour").rglob("*") if p.suffix in {".py", ".html"} and p.is_file())
    return {str(f.relative_to(ici)): hashlib.sha256(f.read_bytes()).hexdigest() for f in fichiers}


def ecrire_empreintes(ici: Path = ICI) -> None:
    (ici / ".empreintes.json").write_text(json.dumps(empreintes(ici), indent=0))


def code_modifie(ici: Path = ICI) -> list[str]:
    """Fichiers de code changés depuis la dernière mise à jour officielle ([] = intact)."""
    if (ici / ".git").exists():
        return []                                   # copie de développement
    f = ici / ".empreintes.json"
    if not f.exists():
        ecrire_empreintes(ici)                      # première fois : on prend la photo
        return []
    avant, maintenant = json.loads(f.read_text()), empreintes(ici)
    return sorted(k for k in set(avant) | set(maintenant) if avant.get(k) != maintenant.get(k))


def proteger_dossier(dossier: Path) -> int:
    """Dossier et fichiers lisibles par Hilal seul. Renvoie le nombre de corrections."""
    corrige = 0
    for p in [dossier, *dossier.rglob("*")]:
        voulu = 0o700 if p.is_dir() else 0o600
        try:
            if stat.S_IMODE(p.stat().st_mode) != voulu:
                os.chmod(p, voulu)
                corrige += 1
        except OSError:
            pass
    return corrige


def secrets_stockes(dossier: Path) -> list[str]:
    trouves = []
    for f in [dossier / "memoire.json", dossier / "carnet.json", dossier / "carnet.txt",
              *(dossier / "bibliotheque").glob("*.md")]:
        if f.exists() and (genre := securite.sensible(f.read_text(encoding="utf-8", errors="ignore"))):
            trouves.append(f"{f.name} ({genre})")
    return trouves


def autotests(competences) -> list[str]:
    import unicodedata
    rates = []
    for phrase, attendu in AUTOTESTS:
        t = "".join(c for c in unicodedata.normalize("NFD", phrase) if unicodedata.category(c) != "Mn")
        trouve = next((c.__name__.split(".")[-1] for c in competences if c.MOTIF.search(t)), None)
        if trouve != attendu:
            rates.append(f"« {phrase} » → {trouve or 'personne'} (attendu : {attendu})")
    return rates


def erreurs_recentes(dossier: Path, heures: int = 24) -> list[str]:
    f = dossier / "journal.log"
    if not f.exists():
        return []
    limite = f"{dt.datetime.now() - dt.timedelta(hours=heures):%Y-%m-%d %H:%M:%S}"
    lignes = f.read_text(encoding="utf-8", errors="ignore").splitlines()[-400:]
    return [l for l in lignes if "| erreur |" in l and l[:19] >= limite][-6:]


def bilan(routeur, url_ecran: str = "", ici: Path = ICI) -> list[dict]:
    """Liste de contrôles : {ok, titre, detail}. securite=True pour ceux qui doivent alerter Hilal."""
    r = routeur.r
    dossier = Path(r["dossier"])
    res = []

    def ajoute(ok, titre, detail="", securite_=False):
        res.append({"ok": bool(ok), "titre": titre, "detail": detail, "securite": securite_})

    ajoute(not url_ecran or url_ecran.startswith("http://127.0.0.1"), "Écran visible depuis ce Mac seulement",
           url_ecran, True)
    n = proteger_dossier(dossier)
    ajoute(True, "Dossier privé (~/.nour)", f"{n} droit(s) corrigé(s)" if n else "", True)
    s = secrets_stockes(dossier)
    ajoute(not s, "Aucun mot de passe, carte ou IBAN stocké", ", ".join(s), True)
    m = code_modifie(ici)
    ajoute(not m, "Code intact depuis la dernière mise à jour", ", ".join(m[:5]), True)
    depot = r.get("depot_maj", "")
    ajoute(depot in ("", DEPOT_OFFICIEL), "Mises à jour seulement depuis le dépôt officiel", depot, True)
    rates = autotests(routeur.competences)
    ajoute(not rates, f"Compétences testées ({len(AUTOTESTS)} tests, {len(routeur.competences)} compétences)",
           " ; ".join(rates))
    v = getattr(routeur.cerveau, "vitesse", None)
    ajoute(v is None or v >= 8, "Vitesse du cerveau",
           (f"{v} mots/s ({r.get('modele_local')})" if v else "pas encore mesurée") +
           (" : lent, dis « cerveau rapide »" if v and v < 8 else ""))
    o = getattr(routeur, "oreille", None)
    if o:
        ajoute(True, "Oreille", f"bruit de la pièce {o.bruit:.4f}, seuil de voix {o.seuil:.4f}")
    e = erreurs_recentes(dossier)
    ajoute(not e, "Pas d'erreur ces dernières 24 h", "\n".join(e))
    return res


def rapport(controles: list[dict]) -> str:
    lignes = [f"Bilan de santé de Nour v{__version__} ({dt.datetime.now():%d/%m/%Y %H:%M})"]
    for c in controles:
        lignes.append(("✓ " if c["ok"] else "✗ ") + c["titre"] + (f" : {c['detail']}" if c["detail"] else ""))
    return "\n".join(lignes)


def alertes(controles: list[dict]) -> list[str]:
    return [c["titre"] + (f" : {c['detail']}" if c["detail"] else "") for c in controles
            if c["securite"] and not c["ok"]]


