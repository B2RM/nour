@echo off
chcp 65001 >nul
title Installation de Nour
echo.
echo  Installation de Nour, ton assistant vocal (gratuit, tout reste sur ton PC).
echo  Cela peut prendre 10 a 20 minutes la premiere fois (telechargement du cerveau, ~5 Go).
echo.
cd /d "%~dp0"

where python >nul 2>nul || (
  echo [1/4] Installation de Python...
  winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements || goto erreur
  echo  Python installe. Ferme cette fenetre et relance installer-windows.bat.
  pause & exit /b
)
echo [1/4] Python : OK

where ollama >nul 2>nul || (
  echo [2/4] Installation du cerveau local Ollama...
  winget install -e --id Ollama.Ollama --accept-package-agreements --accept-source-agreements || goto erreur
  echo  Ollama installe. Ferme cette fenetre et relance installer-windows.bat.
  pause & exit /b
)
echo [2/4] Ollama : OK

echo [3/4] Installation des modules (oreille, voix)...
python -m pip install --user -q -r requirements.txt || goto erreur

echo [4/4] Telechargement du cerveau (qwen2.5:7b)...
ollama pull qwen2.5:7b || goto erreur

echo @echo off> "%USERPROFILE%\Desktop\Nour.bat"
echo cd /d "%~dp0">> "%USERPROFILE%\Desktop\Nour.bat"
echo python -m nour>> "%USERPROFILE%\Desktop\Nour.bat"
echo pause>> "%USERPROFILE%\Desktop\Nour.bat"

echo.
echo  C'est pret. Double-clique sur "Nour" sur ton bureau, puis dis : "Nour, quelle heure est-il ?"
echo  Pour tester au clavier : python -m nour --texte
pause
exit /b

:erreur
echo.
echo  Quelque chose a bloque. Fais une capture de cette fenetre et envoie-la a Claude.
pause
