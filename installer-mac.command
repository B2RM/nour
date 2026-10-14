#!/bin/bash
# Installation de Nour sur Mac (gratuit, tout reste sur ton Mac).
cd "$(dirname "$0")"
echo
echo "Installation de Nour, ton assistant vocal."
echo "10 à 20 minutes la première fois (téléchargement du cerveau, ~5 Go)."
echo
erreur() { echo; echo "Quelque chose a bloqué. Fais une capture de cette fenêtre et envoie-la à Claude."; read -p "Entrée pour fermer"; exit 1; }

if ! python3 -c "import sys; assert sys.version_info >= (3, 10)" 2>/dev/null; then
  echo "[1/4] Python 3.10+ manquant. Installe-le depuis https://www.python.org/downloads/macos/ puis relance ce fichier."
  open "https://www.python.org/downloads/macos/"; read -p "Entrée pour fermer"; exit 1
fi
echo "[1/4] Python : OK"

if [ ! -d "/Applications/Ollama.app" ] && ! command -v ollama >/dev/null; then
  echo "[2/4] Installation du cerveau local Ollama..."
  curl -fL -o /tmp/Ollama-darwin.zip https://ollama.com/download/Ollama-darwin.zip || erreur
  unzip -q -o /tmp/Ollama-darwin.zip -d /Applications || erreur
fi
open -a Ollama 2>/dev/null; sleep 5
OLLAMA=$(command -v ollama || echo /Applications/Ollama.app/Contents/Resources/ollama)
echo "[2/4] Ollama : OK"

echo "[3/4] Installation des modules (oreille, voix)..."
python3 -m pip install --user -q -r requirements.txt || erreur

echo "[4/4] Téléchargement du cerveau (qwen2.5:7b)..."
"$OLLAMA" pull qwen2.5:7b || erreur

ICI="$(pwd)"
LANCEUR="#!/bin/bash
cd \"$ICI\"
open -a Ollama 2>/dev/null
python3 -m nour"
printf '%s\n' "$LANCEUR" > "$ICI/Lancer-Nour.command" && chmod +x "$ICI/Lancer-Nour.command"
if { printf "%s\n" "$LANCEUR" > "$HOME/Desktop/Nour.command"; } 2>/dev/null && chmod +x "$HOME/Desktop/Nour.command"; then
  OU="sur ton bureau (« Nour »)"
else
  OU="dans ce dossier (« Lancer-Nour »)"
fi
echo
echo "C'est prêt. Double-clique $OU, puis dis : « Nour, quelle heure est-il ? »"
echo "La première fois, le Mac demande l'accès au micro : clique sur Autoriser."
read -p "Entrée pour fermer"
