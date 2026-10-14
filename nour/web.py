"""Petits accès internet en lecture seule (services gratuits, sans compte, sans clé)."""
import requests

_LIEUX: dict = {}


def get(ctx):
    return getattr(ctx, "get", None) or requests.get


def json_de(ctx, url, **params):
    r = get(ctx)(url, params=params, timeout=10)
    r.raise_for_status()
    return r.json()


def lieu(ctx) -> dict:
    """Coordonnées de la ville réglée (Open-Meteo, gratuit)."""
    ville = ctx.r["ville"]
    if ville not in _LIEUX:
        d = json_de(ctx, "https://geocoding-api.open-meteo.com/v1/search", name=ville, count=1, language="fr")
        res = d["results"][0]
        _LIEUX[ville] = {"lat": res["latitude"], "lon": res["longitude"], "nom": res["name"]}
    return _LIEUX[ville]
