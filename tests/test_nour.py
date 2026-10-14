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


RSS = b"""<?xml version='1.0'?><rss><channel><item><title>Titre un</title></item>
<item><title>Titre deux</title></item></channel></rss>"""


class FausseReponse:
    def __init__(self, url=""):
        self.url = url
        self.content = RSS

    def raise_for_status(self):
        pass

    def json(self):
        u = self.url
        if "geocoding" in u:
            return {"results": [{"latitude": 49.26, "longitude": 2.47, "name": "Creil"}]}
        if "open-meteo.com/v1/forecast" in u:
            return {"current": {"temperature_2m": 14.2, "weather_code": 3, "wind_speed_10m": 10},
                    "daily": {"weather_code": [61, 0], "temperature_2m_max": [16, 18],
                              "temperature_2m_min": [9, 8], "precipitation_probability_max": [80, 10]}}
        if "frankfurter" in u:
            return {"rates": {"USD": 108.5}}
        if "gToH" in u:
            return {"data": {"hijri": {"day": "12", "month": {"en": "Rabi al-Thani"}, "year": "1448"}}}
        if "w/api.php" in u:
            return ["x", ["Ibn Khaldoun"], [], []]
        if "rest_v1" in u:
            return {"type": "standard", "extract": "Ibn Khaldoun est un historien. Il est né à Tunis. Il est mort au Caire."}
        return {"data": {"timings": {"Fajr": "06:30", "Dhuhr": "13:45", "Asr": "16:40",
                                     "Maghrib": "19:05", "Isha": "20:30"}}}


@pytest.fixture
def r(tmp_path):
    reglages = config.charger(tmp_path)
    dits, ouverts = [], []
    cerveau = FauxCerveau()
    rt = Routeur(reglages, dits.append, cerveau=cerveau, ouvrir=ouverts.append,
                 get=lambda url, *a, **k: FausseReponse(url))
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
    assert "Je ne trouve ni site ni application" in r.traiter("ouvre casino")
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
    assert "rappel" in rep and "bouton Compétences" in rep and len(rep) < 400


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


def test_memoire_retient_et_va_au_cerveau(r):
    assert "Je m'en souviendrai : je n'aime pas le café" in r.traiter("Souviens-toi que je n'aime pas le café")
    assert "café" in r.traiter("Qu'est-ce que tu sais sur moi ?")
    assert "je n'aime pas le café" in r.memoire.pour_le_cerveau()
    assert "oublié" in r.traiter("oublie café")
    assert r.memoire.faits() == []


def test_memoire_refuse_les_secrets(r):
    assert r.traiter("souviens-toi que mon mot de passe est abc") == securite.REFUS
    assert r.memoire.faits() == []


def test_meteo(r):
    rep = r.traiter("Quel temps fait-il ?")
    assert "14 degrés" in rep and "parapluie" in rep
    assert "Demain" in r.traiter("quel temps demain")


def test_minuteur(r):
    assert r.traiter("minuteur de 1 seconde") == "Minuteur de 1 seconde lancé."
    time.sleep(1.3)
    assert r.dits[-1] == "Rappel : le minuteur de 1 seconde est terminé."


@pytest.mark.parametrize("q,attendu", [("combien font 12 fois 7", "Ça fait 84."),
                                       ("calcule 15 % de 80", "Ça fait 12."),
                                       ("combien font 10 divisé par 4", "Ça fait 2,5.")])
def test_calcul(r, q, attendu):
    assert r.traiter(q) == attendu


def test_calcul_non_numerique_va_au_cerveau(r):
    assert r.traiter("combien font les impôts en France") == "réponse du cerveau"


def test_devises(r):
    assert r.traiter("100 euros en dollars") == "100 euros font environ 108,50 dollars au taux du jour."


def test_hijri_et_qibla(r):
    assert "1448 de l'hégire" in r.traiter("on est quelle date hijri ?")
    rep = r.traiter("c'est où la qibla")
    assert "degrés" in rep and "sud-est" in rep


def test_infos(r):
    assert r.traiter("donne-moi les infos") == "Les titres de franceinfo : Titre un ... Titre deux."


def test_wikipedia(r):
    rep = r.traiter("Qui était Ibn Khaldoun ?")
    assert rep == "Ibn Khaldoun est un historien. Il est né à Tunis. (Wikipédia)"


def test_ouvrir_application(r):
    ouvertes = []
    r.apps, r.ouvrir_app = {"calendrier": "Calendrier", "safari": "Safari"}, ouvertes.append
    assert r.traiter("ouvre Safari") == "J'ouvre Safari."
    assert ouvertes == ["Safari"]


def test_recherche(r):
    assert "YouTube" in r.traiter("cherche recette de couscous sur youtube")
    assert r.ouverts[-1].endswith("recette+de+couscous")


def test_presse_papiers(r):
    r.presse_papiers = lambda: "Un long texte."
    assert r.traiter("lis ce que j'ai copié") == "Un long texte."
    assert r.traiter("résume ce que j'ai copié") == "réponse du cerveau"
    r.presse_papiers = lambda: "mon mot de passe est x"
    assert r.traiter("résume ce que j'ai copié") == securite.REFUS


def test_briefing(r):
    rep = r.traiter("Salam")
    assert rep.startswith("Wa alaykoum salam Hilal.") and "degrés" in rep


def test_cest_faux_note_l_erreur(r):
    import json
    r.traiter("Explique-moi le SaaS")
    assert "noté" in r.traiter("C'est faux")
    erreurs = json.loads((r.r["dossier"] / "a-ameliorer.json").read_text())
    assert erreurs[0]["demande"] == "Explique-moi le SaaS"
    assert "1 erreur" in r.traiter("qu'est-ce que tu dois améliorer ?")


def test_competence_qui_plante_ne_casse_pas_nour(r):
    def boum(*a, **k):
        raise RuntimeError
    r.get = boum
    assert "pas" in r.traiter("donne-moi les infos")


def test_cerveau_en_flux_phrase_par_phrase(tmp_path, monkeypatch):
    import json
    from nour import cerveau as cv
    lignes = [json.dumps({"message": {"content": c}, "done": False}).encode() for c in
              ["Bonjour Hil", "al. Il fait", " beau ! Bonne", " journée"]] + [json.dumps({"done": True}).encode()]

    class Flux:
        def raise_for_status(self):
            pass

        def iter_lines(self):
            return iter(lignes)
    monkeypatch.setattr(cv.requests, "post", lambda *a, **k: Flux())
    reglages = config.charger(tmp_path)
    dits = []
    texte = cv.Cerveau(reglages).repondre("salut", dits.append)
    assert dits == ["Bonjour Hilal.", "Il fait beau !", "Bonne journée"]
    assert texte == "Bonjour Hilal. Il fait beau ! Bonne journée"


def test_pas_de_mise_a_jour_dans_une_copie_de_dev(tmp_path):
    from nour import maj
    (tmp_path / ".git").mkdir()
    assert maj.verifier("B2RM/nour", tmp_path, get=lambda *a, **k: 1 / 0) is None


class CerveauEquipe:
    """Faux cerveau : répond selon le rôle (manager ou directeur)."""
    def __init__(self, avis=("OUI",), travaux=None):
        self.avis, self.travaux, self.appels = list(avis), list(travaux or []), []

    def repondre(self, q, au_fil=None):
        return "réponse directe"

    def appeler(self, systeme, messages, max_mots=200, au_fil=None):
        self.appels.append(systeme.split(".")[0])
        if systeme.startswith("Tu es le directeur"):
            return self.avis.pop(0)
        return self.travaux.pop(0) if self.travaux else "Voici un bon texte complet et clair pour toi."


def _routeur_equipe(tmp_path, cerveau):
    rt = Routeur(config.charger(tmp_path), lambda t: None, cerveau=cerveau)
    traces = []
    rt.suivi = traces.append
    return rt, traces


def test_equipe_choisit_le_bon_manager():
    from nour.equipe import choisir_manager
    assert choisir_manager("écris un mail à un client") == "redaction"
    assert choisir_manager("aide-moi à fixer le prix de mon produit") == "business"
    assert choisir_manager("fais-moi un planning pour la semaine") == "organisation"
    assert choisir_manager("aide-moi avec la photosynthèse") == "savoir"


def test_equipe_travail_valide_du_premier_coup(tmp_path):
    c = CerveauEquipe(avis=["OUI"])
    rt, traces = _routeur_equipe(tmp_path, c)
    rep = rt.traiter("Écris un message pour remercier un client")
    assert rep == "Voici un bon texte complet et clair pour toi."
    assert traces == ["Directeur → Manager rédaction", "Directeur : vérifié ✓"]
    assert len(c.appels) == 2                      # 1 travail + 1 vérification courte


def test_controle_gratuit_evite_un_appel(tmp_path):
    c = CerveauEquipe(avis=[], travaux=["ok", "Voici une version corrigée, complète et en français."])
    rt, traces = _routeur_equipe(tmp_path, c)
    rep = rt.traiter("Rédige une annonce pour ma boutique")
    assert rep == "Voici une version corrigée, complète et en français."
    assert "à reprendre" in traces[1]
    assert not any(a.startswith("Tu es le directeur") for a in c.appels)   # aucun jeton dépensé pour vérifier


def test_directeur_refuse_puis_une_seule_reprise(tmp_path):
    c = CerveauEquipe(avis=["NON : ne parle pas du prix"],
                      travaux=["Un premier texte assez long mais hors sujet.", "Un second texte qui parle bien du prix."])
    rt, traces = _routeur_equipe(tmp_path, c)
    rep = rt.traiter("Aide-moi à fixer le prix de mon produit")
    assert rep == "Un second texte qui parle bien du prix."
    assert len(c.appels) == 3                      # travail + vérif + reprise (pas de boucle infinie)


def test_promesse_interdite_bloquee():
    from nour.equipe import controle_gratuit
    assert controle_gratuit("Avec cette méthode vous aurez un revenu garanti chaque mois.")
    assert controle_gratuit("This is the answer and you will like it for sure with this.")
    assert controle_gratuit("Voici un plan clair en trois étapes pour ta semaine.") is None


def test_sous_taches(tmp_path):
    c = CerveauEquipe(avis=["OUI", "OUI"], travaux=["Premier travail bien complet.", "Second travail bien complet."])
    rt, traces = _routeur_equipe(tmp_path, c)
    rep = rt.traiter("Écris un post Instagram pour la boutique et aussi fais un planning de publication")
    assert rep == "Premier travail bien complet.\n\nSecond travail bien complet."
    assert traces[0] == "Directeur : 2 sous-tâches"


def test_question_simple_ne_derange_pas_l_equipe(tmp_path):
    c = CerveauEquipe()
    rt, _ = _routeur_equipe(tmp_path, c)
    assert rt.traiter("Tu aimes le thé ?") == "réponse directe"
    assert c.appels == []
