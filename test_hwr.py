import unittest
from hwr_manager import HWRManager
from modules.config import Config

class TestHWRManager(unittest.TestCase):
    def test_instantiation(self):
        # Wir können EasyOCR deaktivieren für den Test, um keine Zeit zu verlieren
        conf = Config()
        conf.ENABLE_EASYOCR = False
        manager = HWRManager()
        self.assertFalse(manager.use_tesseract) # Da wir im Test vielleicht kein Tesseract haben
        self.assertIsNone(manager.reader)

    def test_safe_check_failure_handling(self):
        # Testet ob der Manager überlebt, wenn der Safe-Check False liefert
        HWRManager._easyocr_available = False
        manager = HWRManager()
        self.assertIsNone(manager.reader)

if __name__ == "__main__":
    unittest.main()
