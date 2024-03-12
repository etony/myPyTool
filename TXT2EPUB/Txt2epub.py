# -*- coding: utf-8 -*-

"""
Module implementing Txt2epub.
"""
import os
import sys
import datetime
from loguru import logger
import chardet


from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QMainWindow, QDialog
from PyQt6.QtWidgets import QApplication, QFileDialog, QMessageBox
from PyQt6.QtGui import QPixmap, QImage

from Ui_Txt2epub import Ui_MainWindow
from Ui_Dir import Ui_Dialog

from Conver2epub import Conver2epub, Conver2txt


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
        logger.info('程序加载完成.')

    @pyqtSlot()
    @logger.catch()
    def on_pb_convert_clicked(self):
        """
        Slot documentation goes here.
        """

        txtfile = self.le_txt.text().strip()
        epubfile = self.le_epub.text().strip()
        title = self.le_title.text().strip()
        author = self.le_author.text().strip()
        reg = self.te_reg.toPlainText().strip()

        if os.path.exists(txtfile):
            conver2 = Conver2epub(txtfile, epubfile)
            if len(title) > 1:
                conver2.set_title(title)
            if len(author) > 1:
                conver2.set_author(author)
            if len(self.coverpath) > 1:
                conver2.set_cover(self.coverpath)
            if len(reg) > 5:
                conver2.set_reg(reg)
            if self.cb_encode.currentIndex() != 0:
                encode = self.cb_encode.currentText()
                conver2.set_encode(encode)
                logger.info(
                    f'指定文件编码: {self.cb_encode.currentIndex()}-{encode}')
            # conver2 = Conver2epub('从前有座灵剑山.txt', '从前有座灵剑山3.epub')
            conver2.conver()
            logger.info(f'文件转换完成！   {epubfile}')
            self.statusBar.showMessage("文件转换完成！")
            reply = QMessageBox(QMessageBox.Icon.Information, '信息', '转换完成,是否打开存储目录？',
                                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.No).exec()
            if reply == QMessageBox.StandardButton.Ok:
                dirname, filename = os.path.split(epubfile)
                logger.info(f'打开存贮目录: {dirname}')
                if sys.platform == 'win32':
                    # os.system("start explorer %s" %dirname)
                    os.startfile(dirname)
                elif sys.platform == 'linux':
                    os.system('xdg-open "%s"' % dirname)
        else:
            self.statusBar.showMessage("未指定转换文件！")

    @pyqtSlot()
    def on_pb_epub_clicked(self):
        """
        Slot documentation goes here.
        """
        # 前面是地址，后面是文件类型,得到输入地址的文件名和地址txt(*.txt*.xls);;image(*.png)不同类别

        if len(self.le_txt.text().strip()) > 5 and os.path.exists(self.le_txt.text().strip()):
            output = os.path.join(self.dirname, 'output')
            epubpath, type = QFileDialog.getSaveFileName(
                self, "文件保存", output, 'epub(*.epub)')
            if epubpath != '':
                self.le_epub.setText(epubpath)
                logger.info(f'指定存储路径: {epubpath}')
        else:
            logger.info('未指定转换文件！')
            self.statusBar.showMessage('未指定转换文件！')

    @pyqtSlot()
    def on_pb_reset_clicked(self):
        """
        Slot documentation goes here.
        """
        self.le_author.clear()
        self.le_txt.clear()
        self.le_epub.clear()
        self.te_reg.setPlainText(
            "^\s*([第卷][0123456789一二三四五六七八九十零〇百千两]*[章回部节集卷].*)\s*")
        self.le_title.clear()
        logger.info('选项重置！')

    @pyqtSlot()
    def on_pb_txt_clicked(self):
        """
        Slot documentation goes here.
        """
        txtpath, txtType = QFileDialog.getOpenFileName(
            self, "选择源文件", "\.", "*.txt;;All Files(*)")
        if txtpath != "":
            self.le_txt.setText(txtpath)

            self.dirname, filename = os.path.split(txtpath)
            file_name, extension = os.path.splitext(os.path.basename(txtpath))
            self.epubpath = os.path.join(self.dirname, file_name) + '.epub'
            self.title = file_name.strip()
            self.le_epub.setText(self.epubpath)
            self.le_title.setText(self.title)
            self.le_author.setText(self.title)
            logger.info(f'指定转换文件:{txtpath}')
            self.statusBar.showMessage(f'指定转换文件:{txtpath} ')
            with open(txtpath, mode='rb') as f:
                data = f.read(512)
                fileinfo = chardet.detect(data)
                logger.info(f'文件信息: {fileinfo}')
                if len(fileinfo['language']) < 2:
                    self.statusBar.showMessage(
                        f'指定转换文件:{txtpath} 编码:{chardet.detect(data)["encoding"]}')
                else:
                    self.statusBar.showMessage(
                        f'指定转换文件:{txtpath} 编码:{chardet.detect(data)["encoding"]} 语言:{chardet.detect(data)["language"]} ')
                        

    @pyqtSlot()
    def on_pb_cover_clicked(self):
        """
        Slot documentation goes here.
        """
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
        self.Dialog = QDialog()
        self.CW_dir = Ui_Dialog()
        self.CW_dir.setupUi(self.Dialog)
        self.Dialog.setModal(True)

        txtfile = self.le_txt.text().strip()
        if os.path.exists(txtfile):

            epubfile = self.le_epub.text().strip()
            reg = self.te_reg.toPlainText().strip()

            conver2 = Conver2epub(txtfile, epubfile)
            if len(reg) > 5:
                conver2.set_reg(reg)
            if self.cb_encode.currentIndex() != 0:
                encode = self.cb_encode.currentText()
                conver2.set_encode(encode)
                logger.info(
                    f'指定文件编码: {self.cb_encode.currentIndex()}-{encode}')
            items = conver2.get_dir()

            for i in items:
                self.CW_dir.tb_dir.append(i)
            self.Dialog.setFixedSize(self.Dialog.width(), self.Dialog.height())
            self.Dialog.show()
            self.statusBar.clearMessage()
            logger.info('生成章节目录！')
        else:
            self.statusBar.showMessage("未找到转换文件！")

    @pyqtSlot()
    def on_pb_in_epub_clicked(self):
        """
        Slot documentation goes here.
        """
        in_epubpath, in_epubType = QFileDialog.getOpenFileName(
            self, "选择源文件", "\.", "*.epub;;All Files(*)")
        if in_epubpath != "":
            self.le_in_epub.setText(in_epubpath)

            self.in_dirname, in_filename = os.path.split(in_epubpath)
            in_file_name, in_extension = os.path.splitext(
                os.path.basename(in_epubpath))
            self.out_txtpath = os.path.join(
                self.in_dirname, in_file_name) + '.txt'
            self.le_out_txt.setText(self.out_txtpath)

            logger.info(f'指定转换文件:{in_epubpath}')
            self.statusBar.showMessage(f'指定转换文件:{in_epubpath}')

            conver2txt = Conver2txt(
                self.le_in_epub.text(), self.le_out_txt.text())
            book_info = conver2txt.get_info()
            self.le_book_title.setText(book_info['title'])
            self.le_book_creater.setText(book_info['creator'])
            self.le_book_contrib.setText(book_info['contrib'])

            date = datetime.datetime.fromisoformat(book_info['date'])

            self.le_book_date.setText(date.strftime('%Y-%m-%d %H:%M:%S'))
            self.pb_out_txt.setEnabled(True)

            # logger.info(f'cover type: {type(conver2txt.get_cover())}')

            bookcover = conver2txt.get_cover()
            img = QImage.fromData(bookcover)
            cover = QPixmap.fromImage(img)
            self.lb_cover.setPixmap(cover)
            logger.info(f'提取epub文件信息完毕: {book_info}')

    @pyqtSlot()
    def on_pb_out_txt_clicked(self):
        """
        Slot documentation goes here.
        """
        output = os.path.join(self.in_dirname, 'output')
        out_txtpath, type = QFileDialog.getSaveFileName(
            self, "文件保存", output, 'txt(*.txt)')
        if out_txtpath != '':
            self.le_out_txt.setText(out_txtpath)
            logger.info(f'指定转换文件:{out_txtpath}')

    @pyqtSlot()
    def on_pb_out_conver_clicked(self):
        """
        Slot documentation goes here.
        """
        conver2txt = Conver2txt(self.le_in_epub.text(), self.le_out_txt.text())

        if self.cb_out_code.currentIndex() != 0:
            encode = self.cb_out_code.currentText()
            conver2txt.set_code(encode)
        conver2txt.conver()
        logger.info(f'文件转换完成！  {self.le_out_txt.text()}')
        self.statusBar.showMessage(f"文件转换完成！  {self.le_out_txt.text()}")

    @pyqtSlot()
    def on_pb_out_reset_clicked(self):
        """
        Slot documentation goes here.
        """
        self.le_book_contrib.clear()
        self.le_book_creater.clear()
        self.le_book_date.clear()
        self.le_book_title.clear()
        self.le_in_epub.clear()
        self.le_out_txt.clear()
        self.pb_out_txt.setEnabled(False)
        logger.info('选项重置！')


if __name__ == "__main__":
    app = QApplication(sys.argv)
    txt2epub = Txt2epub()
    txt2epub.show()
    sys.exit(app.exec())
