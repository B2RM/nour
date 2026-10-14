import datetime as dt
import re

from .. import web

ORDRE = 32
DESCRIPTION = "te donner la date de l'hégire"
MOTIF = re.compile(r"(hijri|hegire|hegirien|date islamique|calendrier islamique|quel mois islamique)")


def agir(m, brut, ctx):
    try:
        d = web.json_de(ctx, f"https://api.aladhan.com/v1/gToH/{dt.date.today():%d-%m-%Y}")["data"]["hijri"]
    except Exception:
        return "Je n'arrive pas à avoir la date de l'hégire pour le moment."
    return (f"Nous sommes le {int(d['day'])} {d['month']['en']} {d['year']} de l'hégire, selon le calcul. "
            "La date peut varier d'un jour selon l'observation de la lune.")
