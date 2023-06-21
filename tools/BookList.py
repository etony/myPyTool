# -*- coding: utf-8 -*-

"""
Module implementing BLmainWindow.
"""

from PyQt6.QtCore import pyqtSlot, Qt, QModelIndex, QThread, pyqtSignal, QObject, QPoint
from PyQt6.QtWidgets import QMainWindow, QApplication, QFileDialog, QMenu
from PyQt6.QtGui import QIcon, QAction, QImage,QPixmap

from Ui_BookList import Ui_mainWindow
from Ui_BookInfo import Ui_Dialog
from PyQt6 import QtCore, QtWidgets  # , QtGui

import pandas as pd

import numpy as np
import cv2 as cv
import pyzbar.pyzbar as pyzbar

import requests
import logging
import sys
import os
import json
import time


LOG = logging.getLogger(os.path.basename(sys.argv[0]))
logging.basicConfig(datefmt='%Y-%m-%d %H:%M:%S', format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    level=logging.INFO)
bclass = {'默认': 0, '默认分类': 0, '计划': 1, '已读': 2}

# 978(EAN图书代码)-7(地区代码:7-中国)-(出版社代码)-(书序码)-(校验码)
# 978-7-208-12815-6
# 校验码 = 每个数交替乘以1和3，然后把它们的乘积加起来。从左至右奇数位置乘以1；偶数位置乘以3。 把和数除以10，然后求余数，最后求10与余数的差。
# ISBN：978-7-5442-6527-0
# 计算差值：10-(（9*1+7*3+8*1+7*3+5*1+4*3+4*1+2*3+6*1+5*3+2*1+7*3) %10)= 10
# 检验码：0


class TableModel(QtCore.QAbstractTableModel):

    def __init__(self, data):
        # 加载 pandas DataFrame 数据
        super(TableModel, self).__init__()
        self._data = data
        self.backdata = data

    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole:
            value = self._data.iloc[index.row(), index.column()]
            return str(value)

    def rowCount(self, parent=None):  # index):
        # 返回记录数
        return self._data.shape[0]

    def appendRow(self, arowdata):
        # 尾部增加一条记录
        self.beginResetModel()
        self._data.loc[self._data.shape[0]] = arowdata
        self.endResetModel()

    def updateData(self, data):
        # 更新所有记录
        self.beginResetModel()
        self._data = data
        self.endResetModel()

    def updateItem(self, row):
        # 根据第一列的值，更新记录，如不存在则在尾部增加一条记录
        isbnlist = self._data.iloc[:, 0].unique()

        if row[0] in isbnlist:
            self.beginResetModel()
            # self._data[self._data.iloc[:, 0] == row[0]] = row
            self._data.loc[self._data.iloc[:, 0] == row[0], [
                '书名', '作者', '出版社', '价格']] = [row[1], row[2], row[3], row[4]]
            self.endResetModel()
        else:
            self.beginResetModel()
            self._data.loc[self._data.shape[0]+1] = row[0:7]
            self.endResetModel()
            LOG.info(row)

    def columnCount(self, parent=None):  # index):
        # 返回数据列数
        return self._data.shape[1]

    def headerData(self, section, orientation, role):
        # section is the index of the column/row.
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return str(self._data.columns[section])

            if orientation == Qt.Orientation.Vertical:
                return str(self._data.index[section])

    def clear(self):
        # 清空记录
        self._data.drop(self._data.index, inplace=True)

    def dataexport(self):
        # 返回所有数据记录
        return self._data

    def getItem(self, index):
        # 返回一条记录
        df = self._data.iloc[index]
        return df.values.tolist()

    def getlist(self, index):
        collist = self._data.iloc[:, index].unique()
        return collist

    def deleteItem(self, isbn):
        self.beginResetModel()
        self._data.drop(
            self._data[self._data.iloc[:, 0] == isbn].index, inplace=True)
        self.endResetModel()

    def search(self, search):
        self.beginResetModel()

        self._data = self._data[self._data['ISBN'].astype(str).str.contains(search) 
                                | self._data['书名'].astype(str).str.contains(search) 
                                | self._data['作者'].astype(str).str.contains(search) 
                                | self._data['出版社'].astype(str).str.contains(search) 
                                | self._data['分类'].astype(str).str.contains(search) ]

        self.endResetModel()

    def reset(self):
        self.beginResetModel()

        self._data = self.backdata

        self.endResetModel()


class RefreshBookinfoList(QObject):  # https://mathpretty.com/13641.html
    # 自定义信号对象。参数str就代表这个信号可以传一个字符串
    finished = pyqtSignal()  # 结束的信号
    progress = pyqtSignal(str)

    def __init__(self, isbn):
        # 初始化函数
        super(RefreshBookinfoList, self).__init__()
        self.isbn = isbn

    def run(self):
        # 重写线程执行的run函数
        # 触发自定义信号
        # LOG.info("thread : isbn " + self.isbn)

        for i in self.isbn:
            self.progress.emit(i)
            time.sleep(1)
        self.finished.emit()  # 发出结束的信号


class Worker(QObject):  # https://mathpretty.com/13641.html
    finished = pyqtSignal()  # 结束的信号
    progress = pyqtSignal(int)

    def run(self):
        """Long-running task."""
        for i in range(50):

            print(str(i))
            time.sleep(3)


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
        self.setFixedSize(self.width(), self.height())

        data = {'ISBN': [], '书名': [], '作者': [],
                '出版社': [], '价格': [], '分类': [], '书柜': []}

        df = pd.DataFrame(data=data)
        df.index = df.index + 1  # 调整 qtableview 序号

        self.model = TableModel(df)
        self.tv_booklist.setModel(self.model)  # 填充 Qtableview 表头
        self.tv_booklist.verticalHeader().setVisible(True)
        # self.model = QtGui.QStandardItemModel()
        # self.model.setHorizontalHeaderLabels(
        #     ['ISBN', '书名', '作者', '出版社', '价格', '分类', '书柜'])
        # self.tv_booklist.setModel(self.model)
        # self.tv_booklist.setSortingEnabled(True)
        # self.tv_booklist.setColumnWidth(0, 100)
        # self.tv_booklist.setColumnWidth(1, 150)
        # self.tv_booklist.setColumnWidth(2, 110)
        # # self.tv_booklist.setColumnWidth(3, 100)
        # self.tv_booklist.setColumnWidth(4, 60)
        # self.tv_booklist.setColumnWidth(5, 80)
        # self.tv_booklist.setColumnWidth(6, 60)
        # self.tv_booklist.horizontalHeader().setSectionResizeMode(1,QtWidgets.QHeaderView.ResizeMode.Stretch)

        self.tv_booklist.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.tv_booklist.horizontalHeader().setSectionResizeMode(
            1, QtWidgets.QHeaderView.ResizeMode.Interactive)
        self.tv_booklist.horizontalHeader().setSectionResizeMode(
            2, QtWidgets.QHeaderView.ResizeMode.Interactive)
        self.tv_booklist.horizontalHeader().setSectionResizeMode(
            3, QtWidgets.QHeaderView.ResizeMode.Interactive)
        self.tv_booklist.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu)  # 对象的上下文菜单的策略
        self.number = 0
        self.barstr = ''

    @pyqtSlot()
    def on_pb_load_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        csvNamepath, csvType = QFileDialog.getOpenFileName(
            self, "选择存储文件", "\.", "*.csv;;All Files(*)")

        if csvNamepath != "":
            df = pd.read_csv(csvNamepath, dtype='object')  # 数据全部转换为字符串型
            df.index = df.index + 1

            self.model = TableModel(df)
            self.tv_booklist.setModel(self.model)  # 填充csv数据
            self.le_booklist.setText(csvNamepath)
            # self.table.setModel(self.model)
            rowscount = self.model.rowCount()
            self.statusBar.showMessage("共 " + str(rowscount) + " 条记录")

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
        # 通过 douban api 获取ISBN信息
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

            price = book_dict['price']
            price = price.replace('CNY', '').replace('元', '').strip()
            bookinfo.append(isbn)
            bookinfo.append(book_dict['title'])
            bookinfo.append(author)
            bookinfo.append(book_dict['publisher'])
            bookinfo.append(price)
            bookinfo.append('计划')
            bookinfo.append('未设置')
            bookinfo.append(book_dict['image'])
            bookinfo.append(book_dict['pubdate'])
            bookinfo.append(book_dict['rating'])
            # bookinfo.append('')
            # bookinfo.append('')

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
        # bookclass = self.le_bookclass.text()
        bookclass = self.cb_bookclass.currentText()
        bookshelf = self.le_bookshelf.text()

        bookinfo = [isbn, title, author,
                    publisher, price, bookclass, bookshelf]
        LOG.info(bookinfo)
        self.model.updateItem(bookinfo)
        
        self.statusBar.showMessage("共 " + str(self.model.rowCount()) + " 条记录")        

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

            # if len(self.le_bookclass.text().strip()) == 0:
            #     self.le_bookclass.setText("未设")
            #     self.le_bookshelf.setText("未知")
            if len(self.cb_bookclass.currentText().strip()) == 0:
                self.cb_bookclass.setCurrentIndex(0)
                self.le_bookshelf.setText("未知")

            # self.model.appendRow(bookinfo)
            self.model.updateItem(bookinfo)
            self.statusBar.showMessage("共 " + str(self.model.rowCount()) + " 条记录") 
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
        # self.le_bookclass.setText(bookinfo[5])
        self.cb_bookclass.setCurrentIndex(bclass[bookinfo[5]])

        self.le_bookshelf.setText(bookinfo[6])

    def refreshonebookinfo(self, arow):

        bookinfo = self.get_douban_isbn(arow)
        
        if len(bookinfo) >= 7:
            LOG.info('-'.join(bookinfo[:5]))
            self.model.updateItem(bookinfo)
        self.number += 1

        self.statusBar.showMessage(self.barstr + str(self.number))

    @pyqtSlot()
    def on_pb_refresh_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        # 调用 douban API 接口，根据 isbn编码 更新所有记录
        isbnlist = self.model.getlist(0)
        self.number = 0
        self.barstr = '信息更新:' + str(len(isbnlist)) + '/'

        # 多线程刷新图书信息   开始

        self.thread = QThread()
        # Step 3: Create a worker object
        self.worker = RefreshBookinfoList(isbnlist)
        # Step 4: Move worker to the thread
        self.worker.moveToThread(self.thread)
        # Step 5: Connect signals and slots
        self.thread.started.connect(self.worker.run)  # 通知开始
        self.worker.finished.connect(self.thread.quit)  # 结束后通知结束
        self.worker.finished.connect(self.worker.deleteLater)  # 完成后删除对象
        self.thread.finished.connect(self.thread.deleteLater)  # 完成后删除对象
        self.worker.progress.connect(
            self.refreshonebookinfo)  # 绑定 progress 的信号
        self.thread.start()
        self.pb_refresh.setEnabled(False)

        self.thread.finished.connect(lambda: self.pb_refresh.setEnabled(True))
        self.thread.finished.connect(lambda: self.statusBar.showMessage(
            "共 " + str(self.model.rowCount()) + " 条记录"))

        # 多线程刷新图书信息    结束

        # 单线程刷新图书信息
        # for isbn in isbnlist:
        #     bookinfo = self.get_douban_isbn(isbn)
        #     if len(bookinfo) == 7:
        #         LOG.info(str(i) + ': ' + '-'.join(bookinfo[:5]))
        #         self.model.updateItem(bookinfo)
        #     i += 1
        #     time.sleep(0.5)

    @pyqtSlot()
    def on_pb_reset_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        self.le_bookauthor.clear()
        # self.le_bookclass.clear()
        self.cb_bookclass.setCurrentIndex(-1)
        # self.le_booklist.clear()
        self.le_bookname.clear()
        self.le_bookshelf.clear()
        # self.le_isbn_pic.clear()
        self.le_price.clear()
        self.le_publisher.clear()
        self.model.reset()
        self.statusBar.showMessage("共 " + str(self.model.rowCount()) + " 条记录") 

    def genLoveMenu(self, pos):
        menu = QMenu(self)
        ico_del = QIcon('delete.png')
        self.dele = menu.addAction(ico_del, u"删除")
        self.action = menu.exec(self.tv_booklist.mapToGlobal(pos))

    @pyqtSlot(QPoint)
    def on_tv_booklist_customContextMenuRequested(self, pos):

        # indexlist = self.tv_booklist.selectedIndexes()
        # inlist = set( ind.row() for ind in indexlist)
        # print(inlist)

        ########## 删除当前行 ########################
        # if self.model.rowCount() > 0:
        #     indexs = self.tv_booklist.selectedIndexes()
        #     if len(indexs) > 0:
        #         index = indexs[0].row()
        #         self.genLoveMenu(pos)
        #         if self.action == self.dele:
        #             # self.model.deleteItem(self.tv_booklist.currentIndex().row())

        #             bookinfo = self.model.getItem(index)
        #             self.model.deleteItem(bookinfo[0])

        ################### 多选删除 ##############
        if self.model.rowCount() > 0:
            indexs = self.tv_booklist.selectedIndexes()
            indexlist = set(index.row() for index in indexs)
            isbnlist = []
            for aindex in indexlist:
                isbnlist.append(self.model.getItem(aindex)[0])
            LOG.info(f"选中信息:   {isbnlist}")
            if len(isbnlist) > 0:
                self.genLoveMenu(pos)
                if self.action == self.dele:
                    for isbn in isbnlist:
                        self.model.deleteItem(isbn)
                        LOG.info(f"删除信息： {isbn}")
                    self.statusBar.showMessage("共 " + str(self.model.rowCount()) + " 条记录") 

    @pyqtSlot()
    def on_pb_search_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        search = self.le_bookname.text().strip()
        self.model.search(search)
        self.statusBar.showMessage("共 " + str(self.model.rowCount()) + " 条记录") 

    @pyqtSlot(QModelIndex)
    def on_tv_booklist_doubleClicked(self, index):
        """
        Slot documentation goes here.

        @param index DESCRIPTION
        @type QModelIndex
        """
        # TODO: not implemented yet
        self.Dialog = QtWidgets.QDialog()
        self.CW_bookinfo = Ui_Dialog()
        self.CW_bookinfo.setupUi(self.Dialog)
        self.Dialog.setModal(True)

        # self.Dialog.setWindowModality(Qt.ApplicationModal)
        # 在PyQt6中，QtCore.Qt.ApplicationModal属性已经被移除， 
        # 可以使用QApplication.setModal()方法来设置模态窗口。该方法接受一个布尔值作为参数，True表示应用程序进入模态状态，False表示退出模态状态。
        bookinfo = self.model.getItem(index.row())
        
        douban_bookinfo = self.get_douban_isbn(str(bookinfo[0]))
        res = requests.get(douban_bookinfo[7])
        img = QImage.fromData(res.content)
        self.CW_bookinfo.lb_bookcover.setPixmap(QPixmap.fromImage(img))
        
        self.CW_bookinfo.tb_bookinfo.setText('<b><font color="black" size="5">'+ douban_bookinfo[1] + '</font></b>' ) 
        
        self.CW_bookinfo.tb_bookinfo.append('<br><b>作者: </b>'+ douban_bookinfo[2]) 
        self.CW_bookinfo.tb_bookinfo.append('<br><b>出版社: </b>'+ douban_bookinfo[3]) 
        self.CW_bookinfo.tb_bookinfo.append('<br><b>价格: </b>'+ douban_bookinfo[4])         
        self.CW_bookinfo.tb_bookinfo.append('<br><b>日期: </b>'+ douban_bookinfo[8]) 
        self.CW_bookinfo.tb_bookinfo.append('<br><b>ISBN: </b>'+ douban_bookinfo[0]) 
        
        self.CW_bookinfo.tb_bookinfo.append('<br><b>评分: </b>'+ str(douban_bookinfo[9]['average']) +'分/ ' + str(douban_bookinfo[9]['numRaters']) + '人') 
        # r = requests.get(book_dict['image'])
        # im = cv.imdecode(np.frombuffer(r.content, np.uint8), cv.IMREAD_COLOR) # 直接解码网络数据
        # cv.imshow('im', im)
        # cv.waitKey(0)
        self.Dialog.setWindowTitle("图书信息 - " +  douban_bookinfo[1] )
        LOG.info(douban_bookinfo)
        self.Dialog.show()
        


if __name__ == "__main__":
    app = QApplication(sys.argv)
    blmain = BLmainWindow()
    blmain.show()
    sys.exit(app.exec())
