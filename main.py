import sys
import os
import signal  # Wichtig für STRG+C
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QLineEdit, QPushButton, QListWidget, QListWidgetItem, QLabel)
from PyQt5.QtCore import Qt, QTimer
from task_manager import TaskManager
from style import STYLESHEET
import socket
# --- NEU: Aktiviere die integrierte, moderne Qt-Bildschirmtastatur! ---
# Wichtig: Muss vor der Erstellung der QApplication passieren
# apt install qtvirtualkeyboard-plugin
# apt install qml-module-qtquick2 qml-module-qtquick-window2 qml-module-qtquick-layouts qml-module-qt-labs-folderlistmodel qml-module-qtquick-controls2
# apt install hunspell-de-de
os.environ["QT_IM_MODULE"] = "qtvirtualkeyboard"

class TodoApp(QWidget):
    def __init__(self):
        super().__init__()
        self.task_manager = TaskManager()
        self.init_ui()
        self.load_initial_tasks()

        # Timer für WLAN-Check (alle 10 Sekunden)
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_wifi_status)
        self.status_timer.start(10000)
        self.update_wifi_status()  # Sofortiger Check beim Start


    def init_ui(self):
        self.setWindowTitle('Pi Schreibtafel')
        self.showFullScreen()  # Kiosk-Modus

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 10, 20, 20)
        main_layout.setSpacing(10)

        # --- Mini Status-Leiste ganz oben ---
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Prüfe WLAN...")
        self.status_label.setObjectName("statusLabel")
        status_layout.addStretch()  # Schiebt die Anzeige nach rechts
        status_layout.addWidget(self.status_label)
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

        # --- Listenbereich ---
        self.task_list = QListWidget()
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

    def update_wifi_status(self):
        try:
            # Versucht eine Verbindung zu Googles DNS-Server aufzubauen (Port 53)
            socket.setdefaulttimeout(2)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
            self.status_label.setText("● WLAN Online")
            self.status_label.setStyleSheet("color: #a6e3a1;")  # Sanftes Grün
        except Exception:
            self.status_label.setText("○ Offline")
            self.status_label.setStyleSheet("color: #f38ba8;")  # Sanftes Rot

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
        self.task_list.addItem(item)

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