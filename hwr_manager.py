import numpy as np
from PyQt5.QtGui import QImage
import logging
import subprocess
import sys
from modules.config import Config

class HWRManager:
    _easyocr_available = None # Cache für die Verfügbarkeit in dieser Session

    def __init__(self, languages=['de', 'en']):
        self.reader = None
        self.use_tesseract = False
        self.conf = Config()
        self.logger = self.conf.get_logger()

        # Prüfe Config
        if not getattr(self.conf, "ENABLE_EASYOCR", True):
            self.logger.info("EasyOCR ist in der Konfiguration deaktiviert.")
            self._init_tesseract()
            return

        # Prüfe Verfügbarkeit einmalig sicher (gegen SIGILL)
        if HWRManager._easyocr_available is None:
            HWRManager._easyocr_available = self._check_easyocr_safe()

        if HWRManager._easyocr_available:
            try:
                import easyocr
                self.reader = easyocr.Reader(languages)
                self.logger.info("EasyOCR initialisiert.")
            except Exception as e:
                self.logger.warning(f"EasyOCR Import fehlgeschlagen trotz positivem Test: {e}")
                self._init_tesseract()
        else:
            self.logger.warning("EasyOCR wird aufgrund von Inkompatibilität (SIGILL) übersprungen.")
            self._init_tesseract()

    def _check_easyocr_safe(self):
        """Versucht easyocr in einem Subprozess zu importieren, um SIGILL im Hauptprozess zu vermeiden."""
        try:
            self.logger.info("Prüfe EasyOCR-Kompatibilität (Subprozess)...")
            proc = subprocess.run(
                [sys.executable, "-c", "import easyocr; print('OK')"],
                capture_output=True,
                text=True,
                timeout=20
            )
            if proc.returncode == 0 and "OK" in proc.stdout:
                return True
            else:
                self.logger.error(f"EasyOCR Test fehlgeschlagen (Returncode {proc.returncode}).")
                return False
        except Exception as e:
            self.logger.error(f"Konnte EasyOCR-Kompatibilität nicht testen: {e}")
            return False

    def _init_tesseract(self):
        try:
            import pytesseract
            # Teste ob Tesseract installiert ist
            pytesseract.get_tesseract_version()
            self.use_tesseract = True
            self.logger.info("Pytesseract als Fallback initialisiert.")
        except Exception as te:
            self.logger.error(f"Pytesseract konnte nicht initialisiert werden: {te}")

    def recognize_text(self, qimage: QImage):
        if not self.reader and not self.use_tesseract:
            self.logger.error("Kein OCR-Engine verfügbar.")
            return ""

        # QImage -> NumPy array
        ptr = qimage.bits()
        ptr.setsize(qimage.height() * qimage.width() * 4)
        arr = np.frombuffer(ptr, np.uint8).reshape((qimage.height(), qimage.width(), 4))
        
        import cv2
        img_rgb = cv2.cvtColor(arr, cv2.COLOR_BGRA2RGB)

        if self.reader:
            try:
                results = self.reader.readtext(img_rgb)
                text = " ".join([res[1] for res in results])
                return text.strip()
            except Exception as e:
                self.logger.error(f"Fehler bei EasyOCR Erkennung: {e}")
        
        if self.use_tesseract:
            try:
                import pytesseract
                text = pytesseract.image_to_string(img_rgb, lang='deu+eng')
                return text.strip()
            except Exception as e:
                self.logger.error(f"Fehler bei Tesseract Erkennung: {e}")

        return ""
