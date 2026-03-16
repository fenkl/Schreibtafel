#!/bin/bash

# Ermittle das Verzeichnis, in dem dieses Skript liegt (egal von wo es aufgerufen wird)
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

echo "Starte Skript aus dem Verzeichnis: $DIR"
cd "$DIR" || exit 1


wait_for_connection() {
    local target="$1"
    local description="$2"

    echo "Prüfe $description ($target)..."
    # -c1: 1 Paket, -W2: 2 Sekunden Timeout pro Versuch, -4: IPv4
    until ping -c1 -W2 -4 "$target" &>/dev/null; do
        echo "Warte auf $description..."
        sleep 2
    done
    echo "$description OK!"
}
wait_for_connection "google.com" "Netzwerkverbindung"
wait_for_connection "github.com" "Github-Verbindung"


# Pull the latest changes from git repository
git pull
echo "git pull durchgeführt"

# --- SYSTEM DEPENDENCIES (PyQt5, Tesseract) ---
echo "Prüfe System-Abhängigkeiten..."
MISSING_PKGS=""
for pkg in python3-pyqt5 tesseract-ocr tesseract-ocr-deu; do
    if ! dpkg -l "$pkg" 2>/dev/null | grep -q "^ii"; then
        MISSING_PKGS="$MISSING_PKGS $pkg"
    fi
done

if [ -n "$MISSING_PKGS" ]; then
    echo "Installiere fehlende System-Pakete:$MISSING_PKGS..."
    sudo apt update && sudo apt install -y $MISSING_PKGS
fi

# --- VIRTUAL ENVIRONMENT ---
if [ ! -d "$DIR/.venv" ]; then
    echo "Erstelle virtuelle Umgebung (.venv)..."
    /usr/bin/python3 -m venv --system-site-packages "$DIR/.venv"
fi

# Sicherstellen, dass die venv Zugriff auf System-PyQt5 hat
if ! "$DIR/.venv/bin/python3" -c "import PyQt5" &>/dev/null; then
    echo "PyQt5 in venv nicht verfügbar. Re-initialisiere mit --system-site-packages..."
    rm -rf "$DIR/.venv"
    /usr/bin/python3 -m venv --system-site-packages "$DIR/.venv"
fi

echo "Installiere/Aktualisiere Requirements..."
"$DIR/.venv/bin/pip" install -r "$DIR/requirements.txt"


# --- BILDSCHIRM AUFWECKEN ---
# wlopm braucht diese Info, um den Wayland-Monitor zu finden
export WAYLAND_DISPLAY=wayland-0
export XDG_RUNTIME_DIR=/run/user/$(id -u)

# 1. Wächter beenden (verhindert erneutes Blanking)
killall swayidle 2>/dev/null

# 2. Hardware-Ebene: Monitor einschalten
wlopm --on \* 2>/dev/null

# 3. Software-Ebene (X11/xcb): DPMS aufwecken
export DISPLAY=:0
export QT_QPA_PLATFORM=xcb
export QT_IM_MODULE=qtvirtualkeyboard

xset dpms force on 2>/dev/null
xset s off -dpms 2>/dev/null

# --- SYSTEM-CLEANUP & START ---
# Desktop-Panel beenden (für echtes Kiosk-Feeling)
killall wf-panel-pi 2>/dev/null

# Window Manager für X11 (Hält die Tastatur im Vordergrund)
matchbox-window-manager -use_titlebar no &

# --- PI OPTIMIERUNGEN ---
# Verhindert "Illegal instruction" (SIGILL) bei einigen Torch/Numpy Versionen auf ARM
export OPENBLAS_CORETYPE=ARMV8

# --- MODUS-AUSWAHL ---
APP="main.py"
ARGS=""

if [ "$1" == "schultafel" ]; then
    echo "Schultafel-Modus erkannt!"
    APP="tafel_main.py"
    ARGS="schultafel"
fi

"$DIR/.venv/bin/python3" "$DIR/$APP" $ARGS