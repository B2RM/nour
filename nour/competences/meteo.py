import re

from .. import web

ORDRE = 25
DESCRIPTION = "te donner la météo, par exemple : quel temps fait-il demain"
MOTIF = re.compile(r"(meteo|quel temps|il fait (?:quel temps|combien|chaud|froid)|va-t-il pleuvoir|il va pleuvoir|temperature dehors|parapluie)")
CODES = {0: "ciel dégagé", 1: "plutôt dégagé", 2: "partiellement nuageux", 3: "couvert", 45: "brouillard",
         48: "brouillard givrant", 51: "bruine légère", 53: "bruine", 55: "forte bruine", 61: "pluie faible",
         63: "pluie", 65: "forte pluie", 71: "neige faible", 73: "neige", 75: "forte neige", 80: "averses",
         81: "averses", 82: "fortes averses", 95: "orage", 96: "orage avec grêle", 99: "orage avec grêle"}


def agir(m, brut, ctx):
    try:
        l = web.lieu(ctx)
        d = web.json_de(ctx, "https://api.open-meteo.com/v1/forecast", latitude=l["lat"], longitude=l["lon"],
                        current="temperature_2m,weather_code,wind_speed_10m", timezone="auto", forecast_days=2,
                        daily="weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max")
    except Exception:
        return "Je n'arrive pas à avoir la météo pour le moment."
    jour = 1 if "demain" in m.string else 0
    dd = d["daily"]
    ciel = CODES.get(dd["weather_code"][jour], "temps variable")
    pluie = dd["precipitation_probability_max"][jour]
    tmin, tmax = round(dd["temperature_2m_min"][jour]), round(dd["temperature_2m_max"][jour])
    if jour == 0:
        c = d["current"]
        debut = f"À {l['nom']}, il fait {round(c['temperature_2m'])} degrés, {CODES.get(c['weather_code'], 'temps variable')}."
        suite = f" Aujourd'hui entre {tmin} et {tmax} degrés"
    else:
        debut = f"Demain à {l['nom']} : {ciel}."
        suite = f" Entre {tmin} et {tmax} degrés"
    conseil = ", prends un parapluie." if pluie and pluie >= 50 else "."
    return f"{debut}{suite}, {pluie} % de risque de pluie{conseil}"
