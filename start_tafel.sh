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


# Bildschirm freigeben
export DISPLAY=:0

# Versuchen, Bildschirmschoner abzustellen (Fehlermeldungen werden ignoriert, falls du auf Wayland bist)
xset s off 2>/dev/null
xset -dpms 2>/dev/null
xset s noblank 2>/dev/null

# Mauszeiger nach 0.1 Sekunden Inaktivität verstecken
unclutter -idle 0.1 -root &

# App starten (nutzt jetzt den dynamischen Pfad)
/usr/bin/python3 "$DIR/main.py"
