# -*- coding: utf-8 -*-
# D:\work\GIT\Python-Study\TXT2EPUB\clickablelabel.py
from PyQt6.QtWidgets import QLabel
from PyQt6 import QtCore
class ClickableLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)

    def mousePressEvent(self, event):
        self.clicked.emit()

    clicked = QtCore.pyqtSignal()
