import os
import signal  # Wichtig für STRG+C
import socket
import sys
from PyQt5.QtGui import QCursor
from PyQt5.QtCore import Qt, QTimer, QPoint, QDateTime
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QLineEdit, QPushButton, QListWidget, QListWidgetItem, QLabel)

from style import STYLESHEET
from task_manager import TaskManager
from modules.config import Config # Import der neuen Config-Klasse
import subprocess
# --- INSTALLATIONSHINWEISE (Stand: März 2026, X11-Modus) ---
# sudo apt install qtvirtualkeyboard-plugin qml-module-qtquick2 qml-module-qtquick-window2 \
# qml-module-qtquick-layouts qml-module-qt-labs-folderlistmodel qml-module-qtquick-controls2 \
# hunspell-de-de matchbox-window-manager

# WICHTIG: Alles auf X11 (xcb) setzen für stabile Tastatur
os.environ["QT_IM_MODULE"] = "qtvirtualkeyboard"
os.environ["QT_QPA_PLATFORM"] = "xcb"


# --- Spezial-Liste für Wischgesten ---
class SwipeListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.start_pos = None
        self.swipe_threshold = 150  # Pixel, die gewischt werden müssen

    def mousePressEvent(self, event):
        self.start_pos = event.pos()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self.start_pos:
            end_pos = event.pos()
            diff_x = end_pos.x() - self.start_pos.x()
            diff_y = abs(end_pos.y() - self.start_pos.y())

            # Wenn horizontal gewischt wurde (X weit, Y wenig)
            if abs(diff_x) > self.swipe_threshold and diff_y < 50:
                item = self.itemAt(self.start_pos)
                if item:
                    self.takeItem(self.row(item))
                    # Signalisiere der Haupt-App, dass gespeichert werden muss
                    if hasattr(self.parent(), 'save_current_tasks'):
                        self.parent().save_current_tasks()

        self.start_pos = None
        super().mouseReleaseEvent(event)


class TodoApp(QWidget):
    def __init__(self):
        super().__init__()
        self.conf = Config()
        self.log = self.conf.get_logger()
        self.log.info("App startet...")

        self.task_manager = TaskManager()
        self.display_on = True
        self.init_ui()
        self.load_initial_tasks()

        # Timer für WLAN & Uhrzeit (jede Sekunde)
        # jetz als Zentraler Timer (1 Sekunde)
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.tick)
        self.status_timer.start(1000)
        self.tick()




    def init_ui(self):
        self.setWindowTitle('Pi Schreibtafel')
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.showFullScreen()
        self.setCursor(QCursor(Qt.CursorShape.BlankCursor))

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 10, 20, 20)
        main_layout.setSpacing(10)

        # --- Mini Status-Leiste ganz oben ---
        status_layout = QHBoxLayout()

        # Uhrzeit Label
        self.time_label = QLabel()
        self.time_label.setObjectName("timeLabel")

        self.status_label = QLabel("Prüfe WLAN...")
        self.status_label.setObjectName("statusLabel")

        status_layout.addWidget(self.time_label)  # links
        status_layout.addStretch()  # Schiebt die Anzeige nach rechts
        status_layout.addWidget(self.status_label) # rechts
        main_layout.addLayout(status_layout)

        # --- Eingabebereich ---
        input_layout = QHBoxLayout()

        # Wir können wieder das ganz normale QLineEdit nutzen!
        # Die Qt-Engine erkennt automatisch, dass es ein Touch-Screen ist
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Neues To-Do antippen...")
        self.input_field.setMinimumHeight(60)

        self.add_btn = QPushButton("Hinzufügen")
        self.add_btn.setMinimumHeight(60)
        self.add_btn.clicked.connect(self.add_task)

        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.add_btn)

        # --- Wir nutzen hier die Swipe-Liste ---
        self.task_list = SwipeListWidget(self)
        self.task_list.setFocusPolicy(Qt.NoFocus)
        self.task_list.itemChanged.connect(self.save_current_tasks)

        # --- Drag & Drop (Sortierfunktion) ---
        # 1. Erlaubt das Anfassen und Verschieben der Items
        self.task_list.setDragDropMode(QListWidget.InternalMove)

        # 2. Speichert die neue Reihenfolge auf der SD-Karte, wenn ein Item losgelassen wird
        self.task_list.model().rowsMoved.connect(self.save_current_tasks)

        # --- Löschen-Button ---
        self.del_btn = QPushButton("Erledigtes aufräumen")
        self.del_btn.setObjectName("deleteBtn")
        self.del_btn.setMinimumHeight(60)
        self.del_btn.clicked.connect(self.remove_completed_tasks)

        # Alles zusammenbauen
        main_layout.addLayout(input_layout)
        main_layout.addWidget(self.task_list)
        main_layout.addWidget(self.del_btn)

        self.setLayout(main_layout)

    def tick(self):
        """Wird jede Sekunde aufgerufen."""
        now = QDateTime.currentDateTime()
        self.time_label.setText(now.toString("hh:mm"))

        # 1. update_status_bar-Check alle 30 Sek
        if now.time().second() % 30 == 0:
            self.update_status_bar()

        # 2. Display-Power-Check jede Minute
        if now.time().second() == 0:
            self.check_display_power(now.time())

    def check_display_power(self, current_time):
        """Prüft, ob der Monitor an oder aus sein sollte."""
        hour = current_time.hour()

        # Logik: An zwischen WAKE_HOUR und SLEEP_HOUR
        should_be_on = self.conf.WAKE_HOUR <= hour < self.conf.SLEEP_HOUR

        if should_be_on != self.display_on:
            self.display_on = should_be_on
            state = "on" if self.display_on else "off"
            self.log.info(f"Schalte Display {state.upper()} (Stunde: {hour})")

            # Hardware-Befehl via wlopm (Wayland-Ebene)
            try:
                env = {"WAYLAND_DISPLAY": "wayland-0", "XDG_RUNTIME_DIR": "/run/user/1000"}
                subprocess.run(["wlopm", f"--{state}", "*"], env=env)
            except Exception as e:
                self.log.error(f"Fehler bei wlopm: {e}")

    def update_status_bar(self):
        # 1. Uhrzeit aktualisieren
        current_time = QDateTime.currentDateTime().toString("hh:mm")  # oder "hh:mm:ss"
        self.time_label.setText(current_time)

        # 2. WLAN alle 10 Durchläufe (10 Sek) prüfen, um CPU zu sparen
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

    def load_initial_tasks(self):
        self.task_list.blockSignals(True)
        tasks = self.task_manager.load_tasks()
        for task_text, is_done in tasks:
            self.create_list_item(task_text, is_done)
        self.task_list.blockSignals(False)

    def create_list_item(self, text, is_done=False):
        item = QListWidgetItem(text)
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
        item.setCheckState(Qt.Checked if is_done else Qt.Unchecked)
        self.task_list.insertItem(0, item)

    def add_task(self):
        text = self.input_field.text().strip()
        if text:
            self.create_list_item(text)
            self.input_field.clear()
            self.save_current_tasks()
            # Sehr wichtig: Fokus vom Textfeld nehmen, damit die Tastatur sich wieder einklappt!
            self.input_field.clearFocus()

    def remove_completed_tasks(self):
        for i in range(self.task_list.count() - 1, -1, -1):
            item = self.task_list.item(i)
            if item.checkState() == Qt.Checked:
                self.task_list.takeItem(i)
        self.save_current_tasks()

    def save_current_tasks(self):
        tasks = []
        for i in range(self.task_list.count()):
            item = self.task_list.item(i)
            tasks.append((item.text(), item.checkState() == Qt.Checked))
        self.task_manager.save_tasks(tasks)

if __name__ == '__main__':
    # Erlaubt das Beenden per STRG+C im Terminal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    window = TodoApp()
    window.show()
    sys.exit(app.exec_())