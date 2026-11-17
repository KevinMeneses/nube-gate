#!/bin/zsh
# Renderiza los casos en REAPER (pestaña temporal) y verifica la respuesta.
cd "$(dirname "$0")/.."
PY=${NUBE_PY:-python3}   # necesita numpy, scipy y soundfile
[ -f tests/signals/step_high.wav ] || $PY tests/make_signals.py
# la sonda MIDI de las pruebas va junto al plugin (solo en esta máquina)
FXD="$HOME/Library/Application Support/REAPER/Effects/Nube Gate"
mkdir -p "$FXD"; ln -sf "$PWD/tests/midi_probe.jsfx" "$FXD/_prueba_midi.jsfx"
rm -f tests/out/log.txt
/Applications/REAPER.app/Contents/MacOS/REAPER -nonewinst "$PWD/tests/render_cases.lua" >/dev/null 2>&1 &
for i in $(seq 1 180); do grep -q done tests/out/log.txt 2>/dev/null && break; sleep 1; done
grep -q done tests/out/log.txt || { echo "REAPER no terminó (¿diálogo abierto?)"; exit 1; }
grep -i error tests/out/log.txt
$PY tests/check.py
