# -*- coding: utf-8 -*-

"""
Module implementing Txt2epub.
"""
import logging
import os
import sys


from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtWidgets import QApplication, QFileDialog, QMessageBox
from PyQt6.QtGui import QPixmap

from Ui_Txt2epub import Ui_MainWindow

from Conver2epub import Conver2epub

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
        cover2 = Conver2epub('从前有座灵剑山.txt', '从前有座灵剑山.epub')
        cover2.conver()
        QMessageBox(QMessageBox.Icon.Information, '信息', '转换完成',
                    QMessageBox.StandardButton.Ok).exec()
    @pyqtSlot()
    def on_pb_epub_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        raise NotImplementedError

    @pyqtSlot()
    def on_pb_reset_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        raise NotImplementedError

    @pyqtSlot()
    def on_pb_txt_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        txtpath, txtType = QFileDialog.getOpenFileName(
            self, "选择源文件", "\.", "*.txt;;All Files(*)")
        if txtpath != "":
            self.le_txt.setText(txtpath)

            dirname, filename = os.path.split(txtpath)
            file_name, extension = os.path.splitext(os.path.basename(txtpath))
            self.le_epub.setText(os.path.join(dirname, file_name) + '.epub')
            self.le_title.setText(file_name)

    @pyqtSlot()
    def on_pb_cover_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        coverpath, coverType = QFileDialog.getOpenFileName(
            self, "选择封面图片", "\.", "*.jpg;;All Files(*)")

        if coverpath != "":
            cover = QPixmap(coverpath)
            self.lb_image.setPixmap(cover)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    txt2epub = Txt2epub()
    txt2epub.show()
    sys.exit(app.exec())
