# -*- coding: utf-8 -*-

"""
Module implementing Txt2epub.
"""
import logging
import os
import sys


from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtWidgets import QApplication

from Ui_Txt2epub import Ui_MainWindow


class Txt2epub(QMainWindow, Ui_MainWindow):
    """
    Class documentation goes here.
    """

    def __init__(self, parent=None):
        """
        Constructor

        @param parent reference to the parent widget (defaults to None)
        @type QWidget (optional)
        """
        super().__init__(parent)
        self.setupUi(self)

    @pyqtSlot()
    def on_pb_convert_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        raise NotImplementedError


if __name__ == "__main__":
    app = QApplication(sys.argv)
    txt2epub = Txt2epub()
    txt2epub.show()
    sys.exit(app.exec())
