STYLESHEET = """
QWidget {
    background-color: #1e1e2e; /* Dunkler Hintergrund */
    color: #cdd6f4;            /* Heller Text */
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 20px;           /* Große Schrift für 5 Zoll */
}

QLineEdit {
    background-color: #313244;
    border: 2px solid #45475a;
    border-radius: 10px;
    padding: 10px;
}

QLineEdit:focus {
    border: 2px solid #89b4fa; /* Blauer Rahmen bei Eingabe */
}

QPushButton {
    background-color: #89b4fa; /* Blaues Accent */
    color: #1e1e2e;
    border: none;
    border-radius: 10px;
    padding: 10px 20px;
    font-weight: bold;
}

QPushButton:pressed {
    background-color: #74c7ec;
}

QPushButton#deleteBtn {
    background-color: #f38ba8; /* Roter Button für Löschen */
    color: #1e1e2e;
}

QPushButton#deleteBtn:pressed {
    background-color: #eba0ac;
}

QListWidget {
    background-color: #181825;
    border: 2px solid #313244;
    border-radius: 10px;
    padding: 10px;
    outline: none; /* Entfernt den hässlichen gestrichelten Rahmen bei Klick */
}

QListWidget::item {
    padding: 15px;
    border-bottom: 1px solid #313244;
}

QListWidget::item:selected {
    background-color: #313244;
    border-radius: 5px;
}

/* Große Checkboxen für Touch */
QListWidget::indicator {
    width: 30px;
    height: 30px;
    border: 2px solid #89b4fa;
    border-radius: 5px;
}

QListWidget::indicator:checked {
    background-color: #89b4fa;
}

QLabel#statusLabel {
    font-size: 14px;
    color: #a6adc8;
    padding: 5px;
    background-color: transparent;
}
"""