#!/bin/bash

# Ermittle das Verzeichnis, in dem dieses Skript liegt (egal von wo es aufgerufen wird)
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

echo "Starte Bot aus dem Verzeichnis: $DIR"
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

# Kiosk-Settings für X11 (Viel stabiler für die Qt-Tastatur)
export DISPLAY=:0
export QT_QPA_PLATFORM=xcb  # Zwingt X11-Modus
export QT_IM_MODULE=qtvirtualkeyboard

# Bildschirmschoner deaktivieren
xset s off 2>/dev/null
xset -dpms 2>/dev/null
xset s noblank 2>/dev/null

# Window Manager für X11 starten (Hält Fensterordnung ein)
matchbox-window-manager -use_titlebar no &

# Desktop-Elemente killen für sauberen Kiosk
killall wf-panel-pi 2>/dev/null

# damit der Bildschirm an bleibt

killall swayidle 2>/dev/null


/usr/bin/python3 "$DIR/main.py"
