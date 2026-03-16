#!/bin/bash
# Skript zum manuellen Aufwecken des Displays (Schreibtafel)

# Wayland Umgebungsvariablen
export WAYLAND_DISPLAY=wayland-0
export XDG_RUNTIME_DIR=/run/user/$(id -u)

echo "Wecke Display auf..."

# 1. Hardware-Ebene: Monitor einschalten (Wayland)
wlopm --on \* 2>/dev/null

# 2. Software-Ebene: DPMS aufwecken (X11/xcb)
export DISPLAY=:0
xset dpms force on 2>/dev/null
xset s off -dpms 2>/dev/null

echo "Display wurde aktiviert."
