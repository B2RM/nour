# Nour — assistant vocal de Hilal (v0.1)

Notre propre code. Plan et règles : ../plan.md

## Ce qu'il sait faire
- « Nour, note que … » / « Nour, qu'est-ce que j'ai noté ? » / « Nour, vide mon carnet »
- « Nour, rappelle-moi dans 20 minutes de … »
- « Nour, c'est quand Asr ? » / « Nour, prochaine prière »
- « Nour, ouvre YouTube » (liste fermée dans ~/.nour/reglages.json)
- « Nour, quelle heure est-il ? »
- Toute autre question → le cerveau (local par défaut).
- Refuse mots de passe, codes, cartes, IBAN. Ne paie, n'envoie, n'installe rien.

## Tester sans micro
    python -m nour --texte

## Tests
    python -m pytest tests     (14 tests, OK le 14/10/2026)

## Installation sur le PC
Windows : double-clic sur `installer-windows.bat` (Python, Ollama, modules, cerveau, raccourci « Nour » sur le bureau). Mac : double-clic sur `installer-mac.command` (Python requis, installe Ollama, modules, cerveau, raccourci « Nour » sur le bureau). Voix : `say` (Thomas, française).

À la main :
1. Python 3.11+ ; `pip install -r requirements.txt`
2. Cerveau local : installer Ollama, puis `ollama pull qwen2.5:7b`
3. `python -m nour`

## Non vérifié
- Voix et micro : pas de micro ici, à essayer sur le PC de Hilal.
- API des horaires de prière (Aladhan) : bloquée depuis notre serveur, testée avec de fausses données.
