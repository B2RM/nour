import ast
import operator
import re

ORDRE = 60
DESCRIPTION = "faire un calcul, par exemple : combien font 15 % de 80"
MOTIF = re.compile(r"^(?:combien (?:font|fait|ca fait)|calcule|ca fait combien) (.+)")
_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.Pow: operator.pow, ast.USub: operator.neg}
_MOTS = [(r"(\d+(?:[.,]\d+)?)\s*(?:%|pour ?cent) de (\d+(?:[.,]\d+)?)", r"(\1/100*\2)"),
         (r"au carre", "**2"), (r"puissance", "**"), (r"divise par|sur", "/"), (r"fois|x|×", "*"),
         (r"plus", "+"), (r"moins", "-"), (r"virgule", "."), (r"(\d),(\d)", r"\1.\2")]


def _eval(n):
    if isinstance(n, ast.Expression):
        return _eval(n.body)
    if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
        return n.value
    if isinstance(n, ast.BinOp) and type(n.op) in _OPS:
        return _OPS[type(n.op)](_eval(n.left), _eval(n.right))
    if isinstance(n, ast.UnaryOp) and type(n.op) in _OPS:
        return _OPS[type(n.op)](_eval(n.operand))
    raise ValueError


def calculer(expr: str):
    e = expr.strip(" ?.")
    for motif, rempl in _MOTS:
        e = re.sub(motif, rempl, e)
    if not re.fullmatch(r"[\d\s.+\-*/()]+", e):
        return None
    try:
        return _eval(ast.parse(e, mode="eval"))
    except Exception:
        return None


def agir(m, brut, ctx):
    r = calculer(m.group(1))
    if r is None:
        return None   # pas un calcul simple : le cerveau prend le relais
    texte = f"{r:,.2f}".rstrip("0").rstrip(".").replace(",", " ").replace(".", ",")
    return f"Ça fait {texte}."
