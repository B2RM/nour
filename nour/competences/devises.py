import re

from .. import web

ORDRE = 55
DESCRIPTION = "convertir de l'argent, par exemple : 100 euros en dollars"
_D = {"euro": "EUR", "dollar": "USD", "livre": "GBP", "dirham": "MAD", "dinar": "DZD", "franc suisse": "CHF",
      "yen": "JPY", "riyal": "SAR", "livre turque": "TRY", "lire turque": "TRY", "franc cfa": "XOF"}
_NOMS = "|".join(sorted((re.escape(k) for k in _D), key=len, reverse=True))
MOTIF = re.compile(rf"(\d+(?:[.,]\d+)?) ({_NOMS})s? (?:en|vers) ({_NOMS})s?")


def agir(m, brut, ctx):
    montant = float(m.group(1).replace(",", "."))
    de, vers = _D[m.group(2)], _D[m.group(3)]
    try:
        d = web.json_de(ctx, "https://api.frankfurter.app/latest", amount=montant, **{"from": de, "to": vers})
        val = d["rates"][vers]
    except Exception:
        return "Je n'arrive pas à avoir le taux de change pour le moment (certaines monnaies ne sont pas disponibles)."
    joli = f"{val:,.2f}".replace(",", " ").replace(".", ",")
    return f"{m.group(1)} {m.group(2)}s font environ {joli} {m.group(3)}s au taux du jour."
