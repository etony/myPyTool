# -*- coding: utf-8 -*-

"""
Module implementing Txt2epub.
"""
import logging
import os
import sys
import re
from loguru import logger


from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QMainWindow, QDialog
from PyQt6.QtWidgets import QApplication, QFileDialog, QMessageBox
from PyQt6.QtGui import QPixmap

from Ui_Txt2epub import Ui_MainWindow
from Ui_Dir import Ui_Dialog

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
        self.coverpath = ''
        self.setFixedSize(self.width(), self.height())
        logger.add('日志_{time:YYYY-MM-DD}.log', rotation="1 day",
                   format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {module}.{function} : {message}")
        logger.info('初始化完成.')

    @pyqtSlot()
    @logger.catch()
    def on_pb_convert_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet

        txtfile = self.le_txt.text().strip()
        epubfile = self.le_epub.text().strip()
        title = self.le_title.text().strip()
        author = self.le_author.text().strip()

        conver2 = Conver2epub(txtfile, epubfile)
        if len(title) > 1:
            conver2.set_title(title)
        if len(author) > 1:
            conver2.set_author(author)
        if len(self.coverpath) > 1:
            conver2.set_cover(self.coverpath)
        # conver2 = Conver2epub('从前有座灵剑山.txt', '从前有座灵剑山3.epub')
        conver2.conver()
        logger.info('文件转换完成！')
        reply = QMessageBox(QMessageBox.Icon.Information, '信息', '转换完成,是否打开存储目录？',
                            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.No).exec()
        if reply == QMessageBox.StandardButton.Ok:
            dirname, filename = os.path.split(epubfile)
            print(dirname)
            # os.system("start explorer %s" %dirname)
            os.startfile(dirname)

    @pyqtSlot()
    def on_pb_epub_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        # 前面是地址，后面是文件类型,得到输入地址的文件名和地址txt(*.txt*.xls);;image(*.png)不同类别
        epubpath, type = QFileDialog.getSaveFileName(
            self, "文件保存", "output", 'epub(*.epub)')
        if epubpath != '':
            self.le_epub.setText(epubpath)
            logger.info(f'指定存储路径: {epubpath}')

    @pyqtSlot()
    def on_pb_reset_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        self.le_author.clear()
        self.le_txt.clear()
        self.le_epub.clear()
        self.le_reg.clear()
        self.le_title.clear()
        logger.info('选项重置！')

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
            self.epubpath = os.path.join(dirname, file_name) + '.epub'
            self.title = file_name.strip()
            self.le_epub.setText(self.epubpath)
            self.le_title.setText(self.title)
            self.le_author.setText(self.title)
            logger.info(f'指定转换文件:{txtpath}')

    @pyqtSlot()
    def on_pb_cover_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        self.coverpath, coverType = QFileDialog.getOpenFileName(
            self, "选择封面图片", "\.", "*.jpg;;All Files(*)")

        if self.coverpath != "":
            cover = QPixmap(self.coverpath)
            self.lb_image.setPixmap(cover)
            logger.info(f'指定封面图片:{self.coverpath}')

    @pyqtSlot()
    def on_pb_dir_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        self.Dialog = QDialog()
        self.CW_dir = Ui_Dialog()
        self.CW_dir.setupUi(self.Dialog)
        self.Dialog.setModal(True)

        txtfile = self.le_txt.text().strip()
        epubfile = self.le_epub.text().strip()

        conver2 = Conver2epub(txtfile, epubfile)
        items = conver2.get_dir()

        for i in items:
            self.CW_dir.tb_dir.append(i)
        self.Dialog.setFixedSize(self.Dialog.width(), self.Dialog.height())
        self.Dialog.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    txt2epub = Txt2epub()
    txt2epub.show()
    sys.exit(app.exec())
