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

# --- VIRTUAL ENVIRONMENT ---
# Auf dem Raspberry Pi ist PyQt5 via pip problematisch (fehlendes qmake für Build).
# Daher nutzen wir System-Pakete (sudo apt install python3-pyqt5) und --system-site-packages.
if [ ! -d "$DIR/.venv" ]; then
    echo "Erstelle virtuelle Umgebung (.venv)..."
    /usr/bin/python3 -m venv --system-site-packages "$DIR/.venv"
fi

# Sicherstellen, dass PyQt5 verfügbar ist (entweder in venv oder via System-Pakete)
if ! "$DIR/.venv/bin/python3" -c "import PyQt5" &>/dev/null; then
    echo "PyQt5 nicht gefunden. Prüfe System-Installation..."
    if ! dpkg -l python3-pyqt5 tesseract-ocr tesseract-ocr-deu &>/dev/null; then
        echo "Installiere System-Pakete (PyQt5, Tesseract) via apt..."
        sudo apt update && sudo apt install -y python3-pyqt5 tesseract-ocr tesseract-ocr-deu
    fi
    # Falls die venv bereits existierte, aber ohne System-Pakete, muss sie neu erstellt werden
    echo "Re-initialisiere venv mit --system-site-packages..."
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

"$DIR/.venv/bin/python3" "$DIR/main.py"