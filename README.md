# Nour — assistant vocal de Hilal (v0.1)

Notre propre code. Plan et règles : ../plan.md

## Ce qu'il sait faire (v0.4)
- **Écran** : s'ouvre tout seul dans le navigateur (orbe animée, conversation, Compétences, Mémoire, Mes erreurs).
- **Équipe** : pour les vraies tâches (« écris… », « prépare… », « aide-moi à… »), un directeur confie le travail
  au bon manager (rédaction, business, organisation, savoir), vérifie d'abord gratuitement, puis en 20 mots,
  et ne fait recommencer qu'une fois au maximum. Voir nour/equipe.py.
- **Mémoire** : « souviens-toi que… », « qu'est-ce que tu sais sur moi ? », « oublie… ».
- **S'améliorer** : « c'est faux » note l'erreur ; bouton « Mes erreurs » → copier pour Claude.
- **Compétences** (nour/competences/, un fichier chacune) : point du jour, rappels, minuteur, carnet, météo,
  prières, qibla, date de l'hégire, sites et applications, recherche web, son du Mac, presse-papiers
  (lire, résumer, traduire), calculs, devises, actualités, Wikipédia, heure.
- **Rapide** : réponse dite phrase par phrase, cerveau gardé en mémoire, oreille « base ».
- Refuse mots de passe, codes, cartes, IBAN. Ne paie, n'envoie, n'installe rien.

## Tester sans micro
    python -m nour --ecran     (écran seul)
    python -m nour --texte     (Terminal)

## Tests
    python -m pytest tests     (45 tests, OK le 14/10/2026)

## Installation sur le PC
Windows : double-clic sur `installer-windows.bat` (Python, Ollama, modules, cerveau, raccourci « Nour » sur le bureau). Mac : double-clic sur `installer-mac.command` (Python requis, installe Ollama, modules, cerveau, raccourci « Nour » sur le bureau). Voix : `say` (Thomas, française).

À la main :
1. Python 3.11+ ; `pip install -r requirements.txt`
2. Cerveau local : installer Ollama, puis `ollama pull qwen2.5:7b`
3. `python -m nour`

## Non vérifié
- Voix et micro : pas de micro ici, à essayer sur le PC de Hilal.
- API des horaires de prière (Aladhan) : bloquée depuis notre serveur, testée avec de fausses données.
