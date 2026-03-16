from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QPen, QImage, QColor
from PyQt5.QtCore import Qt, QPoint

class DrawingWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.image = QImage(self.size(), QImage.Format_RGB32)
        self.bg_color = QColor("#181825")
        self.image.fill(self.bg_color)
        self.last_point = QPoint()
        self.drawing = False
        self.pen_width = 5
        self.pen_color = Qt.white

    def resizeEvent(self, event):
        if self.width() > self.image.width() or self.height() > self.image.height():
            new_image = QImage(self.size(), QImage.Format_RGB32)
            new_image.fill(self.bg_color)
            painter = QPainter(new_image)
            painter.drawImage(0, 0, self.image)
            self.image = new_image
        super().resizeEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.last_point = event.pos()
            self.drawing = True

    def mouseMoveEvent(self, event):
        if (event.buttons() & Qt.LeftButton) and self.drawing:
            painter = QPainter(self.image)
            painter.setPen(QPen(self.pen_color, self.pen_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.drawLine(self.last_point, event.pos())
            self.last_point = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = False

    def paintEvent(self, event):
        canvas_painter = QPainter(self)
        canvas_painter.drawImage(self.rect(), self.image, self.image.rect())

    def clear(self):
        self.image.fill(self.bg_color)
        self.update()

    def get_image(self):
        return self.image
