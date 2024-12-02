from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QIcon, QColor
from PyQt5.QtWidgets import QToolButton


########################################
#
########################################
class ColorButton(QToolButton):

    ########################################
    #
    ########################################
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColor(QColor(Qt.black))

    ########################################
    #
    ########################################
    def color(self):
        return self._color

    ########################################
    #
    ########################################
    def setColor(self, color):
        self._color = color
        pm = QPixmap(16, 16)
        pm.fill(self._color)
        self.setIcon(QIcon(pm))
