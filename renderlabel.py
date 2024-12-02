from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QLabel


########################################
#
########################################
class RenderLabel(QLabel):

    ########################################
    # @constructor
    ########################################
    def __init__ (self, parent=None):
        super().__init__(parent)
        self._width = 0
        self._height = 0
        #self.setAutoFillBackground(True)
        #self.setScaledContents(True)

    ########################################
    #
    ########################################
    def resizeEvent (self, event):
        self._update_margins() # for pixmap only
        super().resizeEvent(event)

    ########################################
    #
    ########################################
    def setPixmap (self, pm=None):
        if pm is None:
            super().setPixmap(QPixmap())
            self._width = 0
            return
        self._width = pm.width()
        self._height = pm.height()
        self._update_margins()
        super().setPixmap(pm)

    ########################################
    #
    ########################################
    def _update_margins(self):
        if self._width <= 0 or self._height <= 0:
            return
        w = self.width()
        h = self.height()
        if w <= 0 or h <= 0:
            return

#        if w * self._height > h * self._width:
#            m = int((w - (self._width * h / self._height)) / 2)
#            self.setContentsMargins(m, 0, m, 0)
#        else:
#            m = int((h - (self._height * w / self._width)) / 2)
#            self.setContentsMargins(0, m, 0, m)

        # just center, never scale
        mx = int((w - self._width) / 2) if w > self._width else 0
        my = int((h- self._height) / 2) if h > self._height else 0
        self.setContentsMargins(mx, my, mx, my)

    ########################################
    #
    ########################################
    def minimumSizeHint(self):
        return QSize(0, 0)
#        return QSize(self._width, self._height)
