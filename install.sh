#!/bin/zsh
# Instala Nube Gate en REAPER (macOS) como enlace: los cambios del repo se ven al volver a insertar el FX.
set -e
DST="$HOME/Library/Application Support/REAPER/Effects/Nube Gate"
cd "$(dirname "$0")"
mkdir -p "$DST"
ln -sf "$PWD/nube_gate.jsfx" "$DST/nube_gate.jsfx"
echo "Listo: en REAPER busca \"Nube Gate\" en el navegador de FX (JS: Nube Gate)."
