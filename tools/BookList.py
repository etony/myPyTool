# -*- coding: utf-8 -*-

"""
Module implementing BLmainWindow.
"""

from PyQt6.QtCore import pyqtSlot, Qt, QModelIndex
from PyQt6.QtWidgets import QMainWindow, QApplication, QFileDialog

from Ui_BookList import Ui_mainWindow
from PyQt6 import QtGui,  QtCore, QtWidgets

import pandas as pd

import numpy as np
import cv2 as cv
import pyzbar.pyzbar as pyzbar

import requests
import logging
import sys
import os
import json


LOG = logging.getLogger(os.path.basename(sys.argv[0]))
logging.basicConfig(datefmt='%Y-%m-%d %H:%M:%S', format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    level=logging.INFO)

# 978(EAN图书代码)-7(地区代码:7-中国)-(出版社代码)-(书序码)-(校验码)
# 978-7-208-12815-6
# 校验码 = 每个数交替乘以1和3，然后把它们的乘积加起来。从左至右奇数位置乘以1；偶数位置乘以3。 把和数除以10，然后求余数，最后求10与余数的差。
# ISBN：978-7-5442-6527-0
# 计算差值：10-(（9*1+7*3+8*1+7*3+5*1+4*3+4*1+2*3+6*1+5*3+2*1+7*3) %10)= 10
# 检验码：0
class TableModel(QtCore.QAbstractTableModel):

    def __init__(self, data):
        super(TableModel, self).__init__()
        self._data = data

    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole:
            value = self._data.iloc[index.row(), index.column()]
            return str(value)

    def rowCount(self, parent=None):  # index):
        return self._data.shape[0]

    def appendRow(self, arowdata):
        self.beginResetModel()
        self._data.loc[self._data.shape[0]] = arowdata
        self.endResetModel()

    def updateData(self, data):

        self.beginResetModel()
        self._data = data
        self.endResetModel()

    def updateItem(self, row):
        isbnlist = self._data.iloc[:, 0].unique()
        if row[0] in isbnlist:
            self.beginResetModel()
            self._data[self._data.iloc[:, 0] == row[0]] = row
            self.endResetModel()
        else:
            self.beginResetModel()
            self._data.loc[self._data.shape[0]] = row
            self.endResetModel()

    def columnCount(self, parent=None):  # index):
        return self._data.shape[1]

    def headerData(self, section, orientation, role):
        # section is the index of the column/row.
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return str(self._data.columns[section])

            if orientation == Qt.Orientation.Vertical:
                return str(self._data.index[section])

    def clear(self):
        self._data.drop(self._data.index, inplace=True)

    def dataexport(self):
        return self._data

    def getItem(self, index):
        df = self._data.iloc[index]
        return df.values.tolist()


class BLmainWindow(QMainWindow, Ui_mainWindow):
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
        data = {'ISBN': [], '书名': [], '作者': [],
                '出版社': [], '价格': [], '分类': [], '书柜': []}

        df = pd.DataFrame(data=data)
        df.index = df.index + 1

        self.model = TableModel(df)
        self.tv_booklist.setModel(self.model)
        # self.model = QtGui.QStandardItemModel()
        # self.model.setHorizontalHeaderLabels(
        #     ['ISBN', '书名', '作者', '出版社', '价格', '分类', '书柜'])
        # self.tv_booklist.setModel(self.model)
        # self.tv_booklist.setSortingEnabled(True)

    @pyqtSlot()
    def on_pb_load_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        csvNamepath, csvType = QFileDialog.getOpenFileName(
            self, "选择存储文件", "E:\\minipan\\Seafile\\资料", "*.csv;;All Files(*)")

        if csvNamepath != "":
            df = pd.read_csv(csvNamepath, dtype='object')

            self.model = TableModel(df)

            self.tv_booklist.setModel(self.model)
            self.le_booklist.setText(csvNamepath)
            # self.table.setModel(self.model)

    @pyqtSlot()
    def on_pb_save_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        # isbn = self.le_isbn_pic.text()
        # bookinfo = self.get_douban_isbn(isbn)
        # self.model.appendRow(bookinfo)

        csvNamepath, csvType = QFileDialog.getSaveFileName(
            self, "保存存储文件", "E:\\minipan\\Seafile\\资料", "*.csv;;All Files(*)")
        if csvNamepath != "":
            df = self.model._data
            df.to_csv(csvNamepath, index=False)

    @pyqtSlot()
    def on_pb_scan_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        picNamepath, picType = QFileDialog.getOpenFileName(
            self, "选择条形码图片", "E:\\minipan\\Seafile\\资料", "*.png;;*.jpg;;All Files(*)")

        if picNamepath != "":
            # image = cv.imread(img_path)
            image = cv.imdecode(np.fromfile(
                picNamepath, dtype=np.uint8), cv.IMREAD_COLOR)

            gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)

            binary, _ = cv.threshold(gray, 0, 255, cv.THRESH_OTSU)
            binary, mat = cv.threshold(gray, binary, 255, cv.THRESH_BINARY)

            barcode = pyzbar.decode(mat)
            for bar in barcode:
                self.le_isbn_pic.setText(bar.data.decode("utf-8"))

            # data =['xxxxxx', '西线无战事', '作者: [德] 雷马克 翻译:朱雯', '上海人民出版社', '45.00', '计划', '未设置']

            # dd = map(lambda x: QtGui.QStandardItem(x), data)

            # data = get_douban_isbn()
            # # self.model.clear()

            # self.model.appendRow(data)

            # self.tv_booklist.setModel()

            # self.model.insertRow(self.model.rowCount(),data)

            # self.tv_booklist.setModel(self.model)

    def get_douban_isbn(self, isbn):
        bookinfo = []
        if len(isbn) != 13 and len(isbn) != 17:
            return bookinfo
        url = "https://api.douban.com/v2/book/isbn/" + isbn

        # apikey=0df993c66c0c636e29ecbb5344252a4a
        # apikey=0ac44ae016490db2204ce0a042db2916
        payload = {'apikey': '0ab215a8b1977939201640fa14c66bab'}
        headers = {"Referer": "https://m.douban.com/tv/american",
                   "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1"}

        # {"content-type": "multipart/form-data;","User-Agent": "MicroMessenger/","Referer": "https://servicewechat.com/wx2f9b06c1de1ccfca/91/page-frame.html"}

        response = requests.post(url, data=payload, headers=headers)

        book_dict = json.loads(response.text)
        if len(book_dict) > 5:
            author = '/'.join(book_dict['author'])
            if len(book_dict['translator']) > 0:
                author += ' 译者: '
                author += '/'.join(book_dict['translator'])

            bookinfo.append(isbn)
            bookinfo.append(book_dict['title'])
            bookinfo.append(author)
            bookinfo.append(book_dict['publisher'])
            bookinfo.append(book_dict['price'])
            bookinfo.append('计划')
            bookinfo.append('未设置')

        return bookinfo

    @pyqtSlot()
    def on_pb_insert_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        isbn = self.le_isbn_pic.text()
        title = self.le_bookname.text()
        author = self.le_bookauthor.text()
        publisher = self.le_publisher.text()
        price = self.le_price.text()
        bookclass = self.le_bookclass.text()
        bookshelf = self.le_bookshelf.text()

        bookinfo = [isbn, title, author,
                    publisher, price, bookclass, bookshelf]
        LOG.info(bookinfo)
        self.model.updateItem(bookinfo)

    @pyqtSlot()
    def on_pb_getbookinfo_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        isbn = self.le_isbn_pic.text()
        bookinfo = self.get_douban_isbn(isbn)
        if len(bookinfo) > 0:
            self.le_bookname.setText(bookinfo[1])
            self.le_bookauthor.setText(bookinfo[2])
            self.le_publisher.setText(bookinfo[3])
            self.le_price.setText(bookinfo[4])
            self.le_bookclass.setText(bookinfo[5])
            self.le_bookshelf.setText(bookinfo[6])

            self.model.appendRow(bookinfo)
        else:
            LOG.warn("ISBN书号有误:  " + isbn)
            QtWidgets.QMessageBox.warning(
                self, "错误", "ISBN书号有误！", QtWidgets.QMessageBox.StandardButton.Yes)

    @pyqtSlot(QModelIndex)
    def on_tv_booklist_clicked(self, index):
        """
        Slot documentation goes here.

        @param index DESCRIPTION
        @type QModelIndex
        """
        # TODO: not implemented yet
        LOG.info('选定行号: ' + str(index.row()))

        model = self.tv_booklist.model()
        bookinfo = model.getItem(index.row())

        self.le_isbn_pic.setText(str(bookinfo[0]))
        self.le_bookname.setText(bookinfo[1])
        self.le_bookauthor.setText(bookinfo[2])
        self.le_publisher.setText(bookinfo[3])
        self.le_price.setText(bookinfo[4])
        self.le_bookclass.setText(bookinfo[5])
        self.le_bookshelf.setText(bookinfo[6])


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    blmain = BLmainWindow()
    blmain.show()
    sys.exit(app.exec())
