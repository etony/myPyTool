# -*- coding: utf-8 -*-

"""
Module implementing BookInfo.
"""

from PyQt6.QtCore import pyqtSlot, QUrl
from PyQt6.QtWidgets import QApplication, QDialog

from Ui_BookInfo import Ui_Dialog

import sys
# from PyQt6 import QtCore, QtWidgets  # , QtGui


class BookInfo(QDialog, Ui_Dialog):
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

    @pyqtSlot(QUrl)
    def on_tb_bookinfo_anchorClicked(self, p0):
        """
        Slot documentation goes here.

        @param p0 DESCRIPTION
        @type QUrl
        """
        # TODO: not implemented yet
        raise NotImplementedError


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dl = BookInfo()

    dl.show()
    # # apply_stylesheet(app, theme='dark_blue.xml')
    # blmain = QtWidgets.QDialog()
    # li =

    # # # 浅色样式
    # # app.setStyleSheet(qdarkstyle.load_stylesheet(qdarkstyle.LightPalette))
    # # # 深色样式
    # # app.setStyleSheet(qdarkstyle.load_stylesheet(qdarkstyle.DarkPalette))

    # # app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))

    # blmain.show()
    # sys.exit(app.exec())

    # app = QApplication(sys.argv)
    # dialog = CustomDialog()

    # Dialog = QtWidgets.QDialog()
    # CW_bookinfo = Ui_Dialog()
    # CW_bookinfo.tb_bookinfo.setText('<a href="https://www.example.com">点击打开链接</a>')
    # CW_bookinfo.setupUi(Dialog)
    # Dialog.show()

    sys.exit(app.exec())
