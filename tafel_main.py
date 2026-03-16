# --- UNTERSCHIED ZU MAIN.PY ---
# tafel_main.py: Fokus auf freies Zeichnen (wie eine echte Schultafel).
#               Keine Handschrifterkennung, kein Aufgaben-Management.
#               Speichert das gesamte Bild als "tafel_content.png".

import os
import signal
import socket
import sys
import subprocess
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel)
from PyQt5.QtGui import (QPainter, QPen, QPixmap, QColor, QCursor, QImage)
from PyQt5.QtCore import Qt, QPoint, QDateTime, QTimer

from style import STYLESHEET
from modules.config import Config

# --- INSTALLATIONSHINWEISE (wie in main.py) ---
os.environ["QT_IM_MODULE"] = "qtvirtualkeyboard"
os.environ["QT_QPA_PLATFORM"] = "xcb"

class TafelWidget(QWidget):
    """Eine interaktive Zeichenfläche (Tafel)."""
    def __init__(self, parent=None):
        super().__init__(parent)
        # Initialisiere mit einer vernünftigen Standardgröße, resizeEvent passt es später an
        self.image = QImage(1024, 768, QImage.Format_ARGB32)
        self.image.fill(Qt.transparent)
        self.drawing = False
        self.last_point = QPoint()
        self.brush_size = 4
        self.brush_color = QColor("#ecf0f1") # Kreideweiß
        
        # Pfad für die Persistenz (Speichert die Tafel als Bild)
        self.save_path = "tafel_content.png"

    def resizeEvent(self, event):
        """Passt das Bild an, wenn die Fenstergröße sich ändert."""
        if self.image.size() != self.size():
            new_image = QImage(self.size(), QImage.Format_ARGB32)
            new_image.fill(Qt.transparent)
            painter = QPainter(new_image)
            painter.drawImage(QPoint(0, 0), self.image)
            painter.end()
            self.image = new_image
            self.load_tafel() # Versuche, das gespeicherte Bild zu laden

    def paintEvent(self, event):
        """Zeichnet das gespeicherte Bild auf das Widget."""
        canvas_painter = QPainter(self)
        canvas_painter.setRenderHint(QPainter.Antialiasing)
        # Zeichne den Tafelhintergrund (Dunkles Schiefergrün)
        canvas_painter.fillRect(self.rect(), QColor("#2d3436"))
        
        # Optional: Ein paar "Kreidereste" simulieren (Subtiles Rauschen/Textur)
        # Für jetzt lassen wir es clean.
        
        # Zeichne die Linien obendrauf
        canvas_painter.drawImage(self.rect(), self.image, self.image.rect())

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = True
            self.last_point = event.pos()

    def mouseMoveEvent(self, event):
        if (event.buttons() & Qt.LeftButton) and self.drawing:
            painter = QPainter(self.image)
            painter.setPen(QPen(self.brush_color, self.brush_size, 
                               Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.drawLine(self.last_point, event.pos())
            self.last_point = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = False
            self.save_tafel()

    def clear_tafel(self):
        """Löscht den Inhalt (Wegwischen)."""
        self.image.fill(Qt.transparent)
        self.save_tafel()
        self.update()

    def save_tafel(self):
        """Speichert den Inhalt als PNG."""
        self.image.save(self.save_path)

    def load_tafel(self):
        """Lädt den gespeicherten Inhalt, falls vorhanden."""
        if os.path.exists(self.save_path):
            loaded_image = QImage(self.save_path)
            if not loaded_image.isNull():
                painter = QPainter(self.image)
                # Skaliere das Bild, falls nötig, oder zeichne es einfach
                painter.drawImage(self.image.rect(), loaded_image, loaded_image.rect())
                painter.end()
                self.update()

# --- UNTERSCHIED ZU MAIN.PY ---
# tafel_main.py: Fokus auf freies Zeichnen (wie eine echte Schultafel).
#               Keine Handschrifterkennung, kein Aufgaben-Management.
#               Speichert das gesamte Bild als "tafel_content.png".

class TafelApp(QWidget):
    def __init__(self):
        super().__init__()
        self.conf = Config()
        self.log = self.conf.get_logger()
        self.log.info("Tafel-App startet...")
        
        self.display_on = True
        self.init_ui()
        
        # Timer für WLAN & Uhrzeit (wie in main.py)
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.tick)
        self.status_timer.start(1000)
        self.tick()

    def init_ui(self):
        self.setWindowTitle('Digitale Tafel')
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setCursor(QCursor(Qt.CursorShape.BlankCursor))

        # Wir nutzen ein Stacked Layout oder überlagern die Widgets,
        # damit die Tafel wirklich "alles" ist.
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Container für die Tafel
        self.tafel_container = QWidget()
        tafel_layout = QVBoxLayout(self.tafel_container)
        tafel_layout.setContentsMargins(0, 0, 0, 0)
        
        self.tafel = TafelWidget(self)
        tafel_layout.addWidget(self.tafel)
        
        # Overlay für Status (Transparent)
        self.overlay = QWidget(self)
        self.overlay.setAttribute(Qt.WA_TransparentForMouseEvents)
        overlay_layout = QHBoxLayout(self.overlay)
        overlay_layout.setContentsMargins(20, 10, 20, 10)
        
        self.time_label = QLabel()
        self.time_label.setObjectName("timeLabel")
        self.time_label.setStyleSheet("background: transparent; color: rgba(236, 240, 241, 150);")
        
        self.status_label = QLabel("Prüfe WLAN...")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setStyleSheet("background: transparent; color: rgba(166, 227, 161, 150);")

        overlay_layout.addWidget(self.time_label)
        overlay_layout.addStretch()
        overlay_layout.addWidget(self.status_label)
        
        # Wegwisch-Button (Schwamm-Optik)
        self.wipe_btn = QPushButton("🧹 Wegwischen")
        self.wipe_btn.setObjectName("deleteBtn")
        self.wipe_btn.setParent(self)
        self.wipe_btn.setMinimumSize(180, 70)
        self.wipe_btn.move(20, self.height() - 90) # Positionieren wir manuell
        self.wipe_btn.clicked.connect(self.tafel.clear_tafel)
        self.wipe_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(243, 139, 168, 180);
                border: 2px solid #f38ba8;
                border-radius: 15px;
                font-size: 18px;
            }
            QPushButton:pressed {
                background-color: #f38ba8;
            }
        """)

        self.main_layout.addWidget(self.tafel_container)
        self.setLayout(self.main_layout)
        
        # Erst ganz am Ende Fullscreen aktivieren, damit alle Widgets da sind
        # wenn das erste resizeEvent feuert.
        self.showFullScreen()

    def resizeEvent(self, event):
        """Sorgt dafür, dass das Overlay und der Button richtig positioniert bleiben."""
        super().resizeEvent(event)
        # Sicherheitsprüfung, falls resizeEvent vor init_ui() fertig gefeuert wird
        if hasattr(self, 'overlay') and self.overlay:
            self.overlay.resize(self.width(), 80)
        if hasattr(self, 'wipe_btn') and self.wipe_btn:
            self.wipe_btn.move(self.width() - 200, self.height() - 90)

    def tick(self):
        now = QDateTime.currentDateTime()
        self.time_label.setText(now.toString("hh:mm"))
        if now.time().second() % 30 == 0:
            self.update_status_bar()
        if now.time().second() == 0:
            self.check_display_power(now.time())

    def check_display_power(self, current_time):
        hour = current_time.hour()
        if self.conf.WAKE_HOUR < self.conf.SLEEP_HOUR:
            should_be_on = self.conf.WAKE_HOUR <= hour < self.conf.SLEEP_HOUR
        else:
            should_be_on = hour >= self.conf.WAKE_HOUR or hour < self.conf.SLEEP_HOUR

        if should_be_on != self.display_on:
            self.display_on = should_be_on
            state = "on" if self.display_on else "off"
            self.log.info(f"Schalte Display {state.upper()} (Stunde: {hour})")
            try:
                env = {"WAYLAND_DISPLAY": "wayland-0", "XDG_RUNTIME_DIR": "/run/user/1000"}
                subprocess.run(["wlopm", f"--{state}", "*"], env=env)
            except Exception as e:
                self.log.error(f"Fehler bei wlopm: {e}")

    def update_status_bar(self):
        if not hasattr(self, '_wifi_count'): self._wifi_count = 0
        self._wifi_count += 1
        if self._wifi_count >= 10:
            self._wifi_count = 0
            try:
                socket.setdefaulttimeout(2)
                socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
                self.status_label.setText("● WLAN Online")
                self.status_label.setStyleSheet("color: #a6e3a1;")
            except Exception:
                self.status_label.setText("○ Offline")
                self.status_label.setStyleSheet("color: #f38ba8;")

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    window = TafelApp()
    window.show()
    sys.exit(app.exec_())
