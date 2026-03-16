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
from drawing_widget import DrawingWidget
from hwr_manager import HWRManager
import subprocess
# --- INSTALLATIONSHINWEISE (Stand: März 2026, X11-Modus) ---
# sudo apt install qtvirtualkeyboard-plugin qml-module-qtquick2 qml-module-qtquick-window2 \
# qml-module-qtquick-layouts qml-module-qt-labs-folderlistmodel qml-module-qtquick-controls2 \
# hunspell-de-de matchbox-window-manager

# WICHTIG: Alles auf X11 (xcb) setzen für stabile Tastatur (nur auf Linux/Pi sinnvoll)
if sys.platform.startswith("linux"):
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
        self.hwr_manager = HWRManager()
        self.display_on = True
        self.manual_override = False
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

        # --- Eingabebereich (Tafel) ---
        input_container = QVBoxLayout()

        self.drawing_widget = DrawingWidget()
        self.drawing_widget.setMinimumHeight(200)
        self.drawing_widget.setObjectName("drawingBoard")

        btn_layout = QHBoxLayout()

        self.clear_btn = QPushButton("Tafel löschen")
        self.clear_btn.setMinimumHeight(60)
        self.clear_btn.clicked.connect(self.drawing_widget.clear)

        self.add_btn = QPushButton("Hinzufügen")
        self.add_btn.setMinimumHeight(60)
        self.add_btn.clicked.connect(self.add_task)

        btn_layout.addWidget(self.clear_btn)
        btn_layout.addWidget(self.add_btn)

        input_container.addWidget(self.drawing_widget)
        input_container.addLayout(btn_layout)

        # --- Wir nutzen hier die Swipe-Liste ---
        self.task_list = SwipeListWidget(self)
        self.task_list.setFocusPolicy(Qt.NoFocus)
        self.task_list.itemChanged.connect(self.save_current_tasks)

        # --- Drag & Drop (Sortierfunktion) ---
        # 1. Erlaubt das Anfassen und Verschieben der Items
        self.task_list.setDragDropMode(QListWidget.InternalMove)

        # 2. Speichert die neue Reihenfolge auf der SD-Karte, wenn ein Item losgelassen wird
        self.task_list.model().rowsMoved.connect(self.save_current_tasks)

        # --- Untere Buttons ---
        bottom_layout = QHBoxLayout()

        self.del_btn = QPushButton("Aufräumen")
        self.del_btn.setObjectName("deleteBtn")
        self.del_btn.setMinimumHeight(60)
        self.del_btn.clicked.connect(self.remove_completed_tasks)

        self.off_btn = QPushButton("Monitor Aus")
        self.off_btn.setObjectName("offBtn")
        self.off_btn.setMinimumHeight(60)
        self.off_btn.clicked.connect(self.manual_display_off)

        bottom_layout.addWidget(self.del_btn, 2)
        bottom_layout.addWidget(self.off_btn, 1)

        # Alles zusammenbauen
        main_layout.addLayout(input_container)
        main_layout.addWidget(self.task_list)
        main_layout.addLayout(bottom_layout)

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
        if self.conf.WAKE_HOUR < self.conf.SLEEP_HOUR:
            should_be_on = self.conf.WAKE_HOUR <= hour < self.conf.SLEEP_HOUR
        else:
            should_be_on = hour >= self.conf.WAKE_HOUR or hour < self.conf.SLEEP_HOUR

        # Manuellen Override zurücksetzen, wenn die Automatik sowieso OFF schaltet
        if self.manual_override and not should_be_on:
            self.manual_override = False

        # Wenn Override aktiv ist, überspringen wir das Einschalten
        if self.manual_override:
            return

        if should_be_on != self.display_on:
            self.display_on = should_be_on
            self.set_display_state(self.display_on)

    def manual_display_off(self):
        """Manueller Befehl zum Ausschalten des Monitors."""
        self.log.info("Display manuell ausgeschaltet")
        self.display_on = False
        self.manual_override = True
        self.set_display_state(False)

    def set_display_state(self, on):
        """Führt den Hardware-Befehl aus."""
        state = "on" if on else "off"
        self.log.info(f"Setze Display-Hardware: {state.upper()}")
        try:
            # Nutze os.getuid() für Wayland-Pfad
            uid = 1000
            try: uid = os.getuid()
            except AttributeError: pass
            
            env = {"WAYLAND_DISPLAY": "wayland-0", "XDG_RUNTIME_DIR": f"/run/user/{uid}"}
            subprocess.run(["wlopm", f"--{state}", "*"], env=env)
            
            # Für X11 (DPMS) zusätzlich
            env_x11 = {"DISPLAY": ":0"}
            subprocess.run(["xset", "dpms", "force", state], env=env_x11)
        except Exception as e:
            self.log.error(f"Fehler bei Display-Steuerung: {e}")

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
        img = self.drawing_widget.get_image()
        # Text erkennen via HWRManager
        task_text = self.hwr_manager.recognize_text(img)

        if task_text:
            self.create_list_item(task_text)
            self.drawing_widget.clear()
            self.save_current_tasks()
            self.log.info(f"Aufgabe hinzugefügt: {task_text}")
        else:
            self.log.info("Kein Text erkannt.")

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