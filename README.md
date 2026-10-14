# Nour — assistant vocal de Hilal (v0.6)

Notre propre code. Plan et règles : ../plan.md

## Ce qu'il sait faire (v0.6)
- **Plus fiable, plus vif** : l'oreille règle seule son seuil sur le bruit de la pièce et reconnaît mieux « Nour » ;
  mode conversation (8 s après une réponse, pas besoin de redire « Nour ») ; une erreur ne rend plus Nour sourd ;
  l'équipe dit « Je m'en occupe » tout de suite ; Ollama gardé chargé 6 h avec des réglages fixes (plus de
  rechargement caché) et ouvert tout seul s'il est fermé ; « cerveau rapide » / « cerveau normal ».
- **Santé et sécurité** (nour/sante.py) : au démarrage puis toutes les 3 h, Nour vérifie son écran (local
  seulement, protection DNS rebinding), son dossier privé, l'absence de secrets stockés, que son code n'a pas été
  modifié hors mise à jour officielle (empreintes), que les mises à jour viennent seulement de B2RM/nour, et
  teste ses compétences. Bouton « Santé » + « bilan de santé » à la voix.
- **Expert grâce à une bibliothèque** (nour/savoir/) : leçons des grands entrepreneurs (Bezos, Walton, Buffett,
  Jobs…), marketing (Ogilvy, Schwartz, Godin, Cialdini honnête), commerce, gagner sa vie halal, et
  **preuves religieuses** (Coran et hadiths avec références exactes). Le manager religion ne cite que des
  références présentes dans les fiches ; le directeur vérifie gratuitement qu'aucune référence n'est inventée.
- **Apprend tout seul chaque jour** (nour/apprendre.py) : un verset du Coran (dans l'ordre, avec sa référence)
  et 3 leçons (commerce, marketing, histoire du commerce en islam) rangées dans ~/.nour/bibliotheque.
  Sans cerveau (léger), seulement quand Nour est libre, bibliothèque plafonnée à 20 Mo. Il vérifie aussi
  les nouvelles fiches sur GitHub toutes les 3 h. « Qu'as-tu appris aujourd'hui ? »
- **Écran** : s'ouvre tout seul dans le navigateur (orbe animée, conversation, Compétences, Mémoire, Mes erreurs).
- **Équipe** : pour les vraies tâches (« écris… », « prépare… », « aide-moi à… »), un directeur confie le travail
  au bon manager (rédaction, business, marketing, religion, organisation, savoir), vérifie d'abord gratuitement, puis en 20 mots,
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
    python -m pytest tests     (65 tests, OK le 14/10/2026)

## Installation sur le PC
Windows : double-clic sur `installer-windows.bat` (Python, Ollama, modules, cerveau, raccourci « Nour » sur le bureau). Mac : double-clic sur `installer-mac.command` (Python requis, installe Ollama, modules, cerveau, raccourci « Nour » sur le bureau). Voix : `say` (Thomas, française).

À la main :
1. Python 3.11+ ; `pip install -r requirements.txt`
2. Cerveau local : installer Ollama, puis `ollama pull qwen2.5:7b`
3. `python -m nour`

## Non vérifié
- Voix et micro : pas de micro ici, à essayer sur le PC de Hilal.
- API des horaires de prière (Aladhan) : bloquée depuis notre serveur, testée avec de fausses données.
- Sources de l'apprentissage (Wikipédia, api.alquran.cloud) : bloquées depuis notre serveur, testées avec de fausses données.
