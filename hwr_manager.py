import numpy as np
from PyQt5.QtGui import QImage
import logging

class HWRManager:
    def __init__(self, languages=['de', 'en']):
        self.reader = None
        self.use_tesseract = False
        self.logger = logging.getLogger("HWRManager")

        try:
            import easyocr
            self.reader = easyocr.Reader(languages)
            self.logger.info("EasyOCR initialisiert.")
        except Exception as e:
            self.logger.warning(f"EasyOCR konnte nicht initialisiert werden: {e}")
            try:
                import pytesseract
                # Teste ob Tesseract installiert ist
                pytesseract.get_tesseract_version()
                self.use_tesseract = True
                self.logger.info("Pytesseract als Fallback initialisiert.")
            except Exception as te:
                self.logger.error(f"Pytesseract konnte ebenfalls nicht initialisiert werden: {te}")

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
