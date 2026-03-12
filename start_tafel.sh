#!/bin/bash

# Ermittle das Verzeichnis, in dem dieses Skript liegt (egal von wo es aufgerufen wird)
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Bildschirm freigeben
export DISPLAY=:0

# Versuchen, Bildschirmschoner abzustellen (Fehlermeldungen werden ignoriert, falls du auf Wayland bist)
xset s off 2>/dev/null
xset -dpms 2>/dev/null
xset s noblank 2>/dev/null

# App starten (nutzt jetzt den dynamischen Pfad)
/usr/bin/python3 "$DIR/main.py"
