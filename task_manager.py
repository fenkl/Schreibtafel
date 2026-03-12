import json
import os

class TaskManager:
    def __init__(self, filename="todos.json"):
        self.filename = filename

    def load_tasks(self):
        # Gibt eine Liste von Tuples zurück: [("Milch kaufen", False), ("Saugen", True)]
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Fehler beim Laden: {e}")
        return []

    def save_tasks(self, tasks):
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(tasks, f, ensure_ascii=False, indent=4)
