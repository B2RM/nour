import time
from pathlib import Path

import pytest

from nour import config, securite
from nour.routeur import Routeur


class FauxCerveau:
    def __init__(self):
        self.recu = []

    def repondre(self, q):
        self.recu.append(q)
        return "réponse du cerveau"


class FausseReponse:
    def raise_for_status(self):
        pass

    def json(self):
        return {"data": {"timings": {"Fajr": "06:30", "Dhuhr": "13:45", "Asr": "16:40",
                                     "Maghrib": "19:05", "Isha": "20:30"}}}


@pytest.fixture
def r(tmp_path):
    reglages = config.charger(tmp_path)
    dits, ouverts = [], []
    cerveau = FauxCerveau()
    rt = Routeur(reglages, dits.append, cerveau=cerveau, ouvrir=ouverts.append,
                 get=lambda *a, **k: FausseReponse())
    rt.dits, rt.ouverts, rt.faux = dits, ouverts, cerveau
    return rt


def test_note_et_relire(r):
    assert "C'est noté : appeler Karim demain" in r.traiter("Note que appeler Karim demain")
    assert "appeler Karim demain" in r.traiter("Qu'est-ce que j'ai noté ?")


def test_effacer_carnet(r):
    r.traiter("note acheter du pain")
    r.traiter("vide mon carnet")
    assert r.traiter("mes notes") == "Ton carnet est vide."


def test_rappel_se_declenche(r):
    rep = r.traiter("Rappelle-moi dans 0,01 minutes de boire de l'eau")
    assert "je te rappelle" in rep
    time.sleep(1.2)
    assert r.dits == ["Rappel : boire de l'eau."]


def test_rappel_en_lettres(r):
    assert "je te rappelle" in r.traiter("rappelle-moi dans vingt minutes d'appeler maman")


def test_priere_nommee(r):
    assert r.traiter("C'est quand Asr ?") == "Asr est à 16:40 à Creil."
    assert r.traiter("et maghreb") == "Maghrib est à 19:05 à Creil."


def test_prochaine_priere(r):
    rep = r.traiter("c'est quand la prochaine prière ?")
    assert rep.startswith("La prochaine prière est") or rep.startswith("Isha est passée")


def test_ouvrir_site_autorise(r):
    assert r.traiter("ouvre mon mail") == "J'ouvre mail."
    assert r.traiter("ouvre youtube") == "J'ouvre youtube."
    assert r.ouverts[-1] == "https://www.youtube.com"


def test_site_inconnu_refuse(r):
    n = len(r.ouverts)
    assert "Je ne connais pas" in r.traiter("ouvre casino")
    assert len(r.ouverts) == n


@pytest.mark.parametrize("phrase", [
    "note que mon mot de passe est azerty",
    "retiens ma carte 4970 1012 3456 7890",
    "mon IBAN FR76 3000 6000 0112 3456 7890 189",
])
def test_donnees_sensibles_refusees(r, phrase):
    assert r.traiter(phrase) == securite.REFUS
    assert r.faux.recu == []
    assert r.carnet.relire() == "Ton carnet est vide."


def test_question_generale_va_au_cerveau(r):
    assert r.traiter("Explique-moi ce qu'est un SaaS") == "réponse du cerveau"
    assert r.faux.recu == ["Explique-moi ce qu'est un SaaS"]


def test_heure(r):
    assert r.traiter("Quelle heure est-il ?").startswith("Il est ")


def test_journal_ecrit(r):
    r.traiter("note test")
    assert "note | test" in (Path(r.r["dossier"]) / "journal.log").read_text()


def test_voix_systeme_sans_nom():
    from nour.voix import commande_say
    assert commande_say("systeme", 150, "salut") == ["say", "-r", "150", "salut"]
    assert commande_say("Jacques", 150, "salut") == ["say", "-r", "150", "-v", "Jacques", "salut"]


def test_aide_liste_les_competences(r):
    rep = r.traiter("Qu'est-ce que tu sais faire ?")
    assert "rappel" in rep and "prière" in rep and "carnet" in rep


def _zip_depot(version):
    import io, zipfile
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        z.writestr("nour-abc/nour/__main__.py", "# main")
        z.writestr("nour-abc/nour/competences/nouvelle.py", f"# {version}")
        z.writestr("nour-abc/requirements.txt", "requests\n")
    return b.getvalue()


class _Rep:
    def __init__(self, js=None, content=b""):
        self._js, self.content = js, content

    def raise_for_status(self):
        pass

    def json(self):
        return self._js


def test_mise_a_jour_installe_puis_ne_refait_rien(tmp_path):
    from nour import maj
    (tmp_path / "requirements.txt").write_text("requests\n")
    (tmp_path / "nour").mkdir()
    (tmp_path / "nour" / "vieux.py").write_text("x")
    appels = []

    def get(url, **k):
        appels.append(url)
        return _Rep({"sha": "s1"}) if "api.github.com" in url else _Rep(content=_zip_depot("v2"))

    assert maj.verifier("hilal/nour", tmp_path, get) is not None
    assert (tmp_path / "nour" / "competences" / "nouvelle.py").exists()
    assert not (tmp_path / "nour" / "vieux.py").exists()
    assert maj.verifier("hilal/nour", tmp_path, get) is None   # déjà à jour
    assert sum("codeload" in u for u in appels) == 1


def test_mise_a_jour_sans_depot_ou_hors_ligne(tmp_path):
    from nour import maj
    assert maj.verifier("", tmp_path) is None

    def get(url, **k):
        raise OSError("pas d'internet")
    assert maj.verifier("hilal/nour", tmp_path, get) is None
