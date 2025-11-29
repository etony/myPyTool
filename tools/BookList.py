# -*- coding: utf-8 -*-
"""
图书信息管理
功能：基于PyQt6实现图书信息的录入、查询、更新、保存/加载，支持条形码扫描、豆瓣API自动填充、CSV导入导出
作者：未知
版本：1.0
依赖：PyQt6, pandas, opencv-python, pyzbar, requests, qdarkstyle, numpy
"""

import json
import logging
import os
import sys
import time
import math

import cv2 as cv
import numpy as np
import pandas as pd
import pyzbar.pyzbar as pyzbar

import requests
from PyQt6 import QtCore, QtWidgets  # , QtGui
from PyQt6.QtCore import pyqtSignal, pyqtSlot, QModelIndex, QObject, QPoint, Qt, QThread, QVariant
from PyQt6.QtGui import QIcon, QImage, QPixmap
from PyQt6.QtWidgets import QApplication, QFileDialog, QMainWindow, QMenu

from Ui_BookList import Ui_mainWindow
import BookSearch
import BookInfo

import qdarkstyle


# 配置日志（记录程序运行信息/错误）
LOG = logging.getLogger(os.path.basename(sys.argv[0]))
logging.basicConfig(
    datefmt='%Y-%m-%d %H:%M:%S',
    format="%(asctime)s - %(levelname)s - 进程:%(process)d - %(filename)s - %(name)s - 行:%(lineno)d - 模块:%(module)s - %(message)s",
    level=logging.INFO)
# logging.basicConfig(
#     filename='application.log',
#     level=logging.WARNING,
#     format='[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s',
#     datefmt='%H:%M:%S'
# )
# ===================== 全局常量定义 =====================
# 图书分类映射（键：分类名称，值：索引）
bclass = {'默认': 0, '默认分类': 0, '计划': 1, '已读': 2}
# 表格列名（与数据字典字段一一对应）
bcol = ['ISBN', '书名', '作者', '出版', '价格', '评分', '人数', '分类', '书柜']
# 初始数据字典（用于构建空DataFrame）
bdict = {
    'ISBN': [],
    '书名': [],
    '作者': [],
    '出版': [],
    '价格': [],
    '评分': [],
    '人数': [],
    '分类': [],
    '书柜': []
}

bshow = dict(filter(lambda x: x[0] in bcol, bdict.items()))
bshow = {k: v for k, v in bdict.items() if k in bcol}
# 978(EAN图书代码)-7(地区代码:7-中国)-(出版社代码)-(书序码)-(校验码)
# 978-7-208-12815-6
# 校验码 = 每个数交替乘以1和3，然后把它们的乘积加起来。从左至右奇数位置乘以1；偶数位置乘以3。 把和数除以10，然后求余数，最后求10与余数的差。
# ISBN：978-7-5442-6527-0
# 计算差值：10-(（9*1+7*3+8*1+7*3+5*1+4*3+4*1+2*3+6*1+5*3+2*1+7*3) %10)= 10
# 检验码：0


class TableModel(QtCore.QAbstractTableModel):
    """
    自定义表格数据模型，继承QAbstractTableModel，适配Pandas DataFrame
    实现数据的增删改查、筛选、导出等核心操作
    """

    def __init__(self, data):
        """
        初始化模型
        :param data: 初始数据（DataFrame），默认空DataFrame
        :param parent: 父组件
        """
        super(TableModel, self).__init__()
        # 原始数据（未筛选）
        self._data = data
        # 筛选后的数据（用于UI显示）
        self.backdata = data

    def data(self, index, role):
        """
        返回指定单元格的数据（UI显示用）
        :param index: 单元格索引（行/列）
        :param role: 数据角色（默认显示文本）
        :return: 单元格数据（字符串/数字）
        """
        if role == Qt.ItemDataRole.DisplayRole:
            # 获取筛选后数据的指定单元格值
            value = self._data.iloc[index.row(), index.column()]
            # 处理空值显示
            return str(value) if not pd.isna(value) else ""

    def rowCount(self, parent=None):  # index):
        """返回表格行数（筛选后）"""
        return self._data.shape[0]

    def appendRow(self, arowdata):
        """
        新增一行数据
        :param arowdata: 行数据字典（key为列名）
        """
        self.beginResetModel()
        # 转换为DataFrame并追加到原始数据
        self._data.loc[self._data.shape[0]] = arowdata
        self.endResetModel()

    def updateData(self, data):
        """
        替换整个表格数据
        :param new_data: 新的DataFrame数据
        """
        self.beginResetModel()
        self._data = data
        self.endResetModel()

    def updateItem(self, row):
        """
        根据ISBN更新数据（存在则更新，不存在则新增）
        :param isbn: 图书ISBN（唯一标识）
        :param row_data: 待更新的行数据字典
        """
        isbnlist = self._data.iloc[:, 0].unique()
        LOG.info(f'更新记录 {len(row)} 项:  {row}')
        if row[0] in isbnlist:
            self.beginResetModel()
            # self._data[self._data.iloc[:, 0] == row[0]] = row
            if len(row) == 9:
                self._data.loc[
                    self._data.iloc[:, 0] == row[0],
                    ['书名', '作者', '出版', '价格', '评分', '人数', '分类', '书柜']] = [
                        row[1], row[2], row[3], row[4], row[5], row[6], row[7],
                        row[8]
                ]
            else:
                self._data.loc[self._data.iloc[:, 0] == row[0],
                               ['书名', '作者', '出版', '价格', '评分', '人数']] = [
                                   row[1], row[2], row[3], row[4], row[5],
                                   row[6]
                ]
            self.endResetModel()
        else:
            self.beginResetModel()
            self._data.loc[self._data.shape[0] + 1] = row[0:9]
            self.endResetModel()

    def columnCount(self, parent=None):  # index):
        """返回表格列数"""
        return self._data.shape[1]

    def headerData(self, section, orientation, role):
        """
        设置表头显示
        :param section: 列/行索引
        :param orientation: 方向（水平/垂直）
        :param role: 数据角色
        :return: 表头文本
        """
        # section is the index of the column/row.
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return str(self._data.columns[section])

            if orientation == Qt.Orientation.Vertical:
                return str(self._data.index[section])

    def clear(self):
        """
        清空记录
        """
        self._data.drop(self._data.index, inplace=True)

    def dataexport(self):
        """
        导出当前所有原始数据（未筛选）
        """
        return self._data

    def getItem(self, index):
        """ 
        返回一条记录
        """
        df = self._data.iloc[index]
        LOG.info(df.values.tolist())
        return df.values.tolist()

    def getlist(self, index):
        """ 
        返回图书列表
        """
        collist = self._data.iloc[:, index].unique()
        return collist

    def deleteItem(self, isbn):
        """
        删除指定行数据
        :param rows: 待删除行的索引列表（基于筛选后数据）
        """
        self.beginResetModel()
        # 筛选后数据的行 → 原始数据的行索引
        self._data.drop(self._data[self._data.iloc[:, 0] == isbn].index,
                        inplace=True)
        self.endResetModel()

    def search(self, search):
        """
        根据关键词筛选数据（支持多字段模糊匹配）
        :param keyword: 搜索关键词
        """
        self.beginResetModel()
        # 多字段模糊匹配（ISBN/书名/作者/出版/分类）
        self._data = self._data[
            self._data['ISBN'].astype(str).str.contains(search)
            | self._data['书名'].astype(str).str.contains(search)
            | self._data['作者'].astype(str).str.contains(search)
            | self._data['出版'].astype(str).str.contains(search)
            | self._data['分类'].astype(str).str.contains(search)]

        self.endResetModel()

    def reset(self):
        """
        重置筛选状态，显示全部数据
        """
        self.beginResetModel()

        self._data = self.backdata

        self.endResetModel()

# ===================== 多线程批量刷新类 =====================


class RefreshBookinfoList(QObject):  # https://mathpretty.com/13641.html
    """
    多线程批量刷新图书信息类
    避免UI线程阻塞，通过信号传递进度和完成状态
    """
    # 自定义信号：发送待刷新的ISBN
    # 自定义信号：刷新完成
    finished = pyqtSignal()  # 结束的信号
    # 自定义信号对象。参数str就代表这个信号可以传一个字符串
    progress = pyqtSignal(str)

    def __init__(self, isbn):
        """
        初始化刷新线程
        :param isbn_list: 需要刷新的ISBN列表
        """
        super(RefreshBookinfoList, self).__init__()
        self.isbn = isbn

    def run(self):
        # 重写线程执行的run函数
        # 触发自定义信号
        # LOG.info("thread : isbn " + self.isbn)

        for i in self.isbn:
            self.progress.emit(i)   # 发送当前刷新的ISBN
            time.sleep(1)  # 延迟避免API限流
        self.finished.emit()  # 发出结束的信号

# ===================== 多线程类 =====================


class Worker(QObject):  # https://mathpretty.com/13641.html
    finished = pyqtSignal()  # 结束的信号
    progress = pyqtSignal(int)

    def run(self):
        """Long-running task."""
        for i in range(50):

            LOG.info(str(i))
            time.sleep(3)

# ===================== 主窗口类 =====================


class BLmainWindow(QMainWindow, Ui_mainWindow):
    """
    图书信息管理系统主窗口类
    """

    def __init__(self, parent=None):

        super().__init__(parent)
        self.setupUi(self)
        self.setFixedSize(self.width(), self.height())

        data = {
            'ISBN': [],
            '书名': [],
            '作者': [],
            '出版': [],
            '价格': [],
            '评分': [],
            '人数': [],
            '分类': [],
            '书柜': []
        }

        df = pd.DataFrame(data=data, dtype=object)
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
        self.appver = '   ver-1.0.1'
        self.statusBar.showMessage(self.appver)

    # ===================== 按钮槽函数 =====================
    @pyqtSlot()
    def on_pb_load_clicked(self):
        """
        加载CSV格式的图书数据
        """
        # 打开文件选择对话框
        csvNamepath, csvType = QFileDialog.getOpenFileName(
            self, "选择存储文件", ".", "*.csv;;All Files(*)")

        if csvNamepath != "":
            # 读取CSV文件（UTF-8编码）
            df = pd.read_csv(csvNamepath, dtype='object')  # 数据全部转换为字符串型
            # df.insert(loc=5, column='评分', value=0)
            # df.insert(loc=6, column='人数', value=0)
            df.index = df.index + 1
            df.fillna('', inplace=True)

            self.model = TableModel(df)
            self.tv_booklist.setModel(self.model)  # 填充csv数据
            self.le_booklist.setText(csvNamepath)
            # self.table.setModel(self.model)
            rowscount = self.model.rowCount()
            self.statusBar.showMessage(
                "共 " + str(rowscount) + " 条记录" + self.appver)

    @pyqtSlot()
    def on_pb_save_clicked(self):
        """
        保存图书列表信息
        """
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
        扫描条形码图片，识别ISBN
        """
        picNamepath, picType = QFileDialog.getOpenFileName(
            self, "选择条形码图片", ".", "*.png;;*.jpg;;All Files(*)")

        if picNamepath != "":
            # image = cv.imread(img_path)
            image = cv.imdecode(np.fromfile(picNamepath, dtype=np.uint8),
                                cv.IMREAD_COLOR)

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
        """
        调用豆瓣API获取图书信息
        :param isbn: 图书ISBN
        :return: 图书信息字典（空字典表示失败）
        """
        # 调用豆瓣API获取完整详情（含封面、简介等）
        bookinfo = []
        if len(isbn) != 13 and len(isbn) != 17:
            return bookinfo
        # 豆瓣API地址（公开接口）
        url = "https://api.douban.com/v2/book/isbn/" + isbn

        # apikey=0df993c66c0c636e29ecbb5344252a4a
        # apikey=0ac44ae016490db2204ce0a042db2916
        payload = {'apikey': '0ab215a8b1977939201640fa14c66bab'}
        headers = {
            "Referer":
            "https://m.douban.com/tv/american",
            "User-Agent":
            "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1"
        }

        # {"content-type": "multipart/form-data;","User-Agent": "MicroMessenger/","Referer": "https://servicewechat.com/wx2f9b06c1de1ccfca/91/page-frame.html"}

        response = requests.post(url, data=payload, headers=headers)

        book_dict = json.loads(response.text)

        if len(book_dict) > 5:
            author = '/'.join(book_dict['author'])
            if len(book_dict['translator']) > 0:
                author += ' 译者: '
                author += '/'.join(book_dict['translator'])
            rating = book_dict['rating']
            price = book_dict['price']
            price = price.replace('CNY', '').replace('元', '').strip()
            bookinfo.append(isbn)
            bookinfo.append(book_dict['title'])
            bookinfo.append(author)
            bookinfo.append(book_dict['publisher'])
            bookinfo.append(price)
            bookinfo.append(rating['average'])
            bookinfo.append(rating['numRaters'])
            bookinfo.append('计划')
            bookinfo.append('未设置')
            # bookinfo.append(book_dict['image'])
            bookinfo.append(book_dict['images']['small'])
            bookinfo.append(book_dict['pubdate'])
            bookinfo.append(book_dict['rating'])
            bookinfo.append(book_dict['alt'])
            # bookinfo.append('')
            # bookinfo.append('')
            LOG.info(rating)
            # 计算推荐度

            LOG.info(f'图书详细信息:   {book_dict}')
            recommend = round((float(rating['average']) - 2.5) *
                              math.log(float(rating['numRaters']) + 1))
            bookinfo.append(str(recommend))
        else:
            for i in range(13):
                bookinfo.append(" ")

        return bookinfo

    @pyqtSlot()
    def on_pb_insert_clicked(self):
        """
        插入/更新图书信息到表格
        """
        isbn = self.le_isbn_pic.text()
        title = self.le_bookname.text()
        author = self.le_bookauthor.text()
        publisher = self.le_publisher.text()
        price = self.le_price.text()
        # bookclass = self.le_bookclass.text()
        bookclass = self.cb_bookclass.currentText()
        bookshelf = self.le_bookshelf.text()

        bookinfo = [
            isbn, title, author, publisher, price, self.star, self.num,
            bookclass, bookshelf
        ]
        LOG.info(f'插入记录 {len(bookinfo)} 项:  {bookinfo}')
        self.model.updateItem(bookinfo)

        self.statusBar.showMessage(
            "共 " + str(self.model.rowCount()) + " 条记录" + self.appver)

    @pyqtSlot()
    def on_pb_getbookinfo_clicked(self):
        """
        通过豆瓣接口获取图书信息
        """
        isbn = self.le_isbn_pic.text()
        bookinfo = self.get_douban_isbn(isbn.strip())
        if len(bookinfo) > 0:
            self.le_bookname.setText(bookinfo[1])
            self.le_bookauthor.setText(bookinfo[2])
            self.le_publisher.setText(bookinfo[3])
            self.le_price.setText(bookinfo[4])
            self.star = bookinfo[5]
            self.num = bookinfo[6]
            self.le_average.setText(f"{self.star} / {self.num}")
            LOG.info(f"获取评分: 评分:{self.star} 人数:{self.num}")

            # if len(self.le_bookclass.text().strip()) == 0:
            #     self.le_bookclass.setText("未设")
            #     self.le_bookshelf.setText("未知")
            if len(self.cb_bookclass.currentText().strip()) == 0:
                self.cb_bookclass.setCurrentIndex(0)
                self.le_bookshelf.setText("未知")

            # self.model.appendRow(bookinfo)
            self.model.updateItem(bookinfo)
            self.statusBar.showMessage("共 " + str(self.model.rowCount()) +
                                       " 条记录" + self.appver)
        else:
            LOG.warning("ISBN书号有误:  " + isbn)
            QtWidgets.QMessageBox.warning(
                self, "错误", "ISBN书号有误！",
                QtWidgets.QMessageBox.StandardButton.Yes)

    @pyqtSlot(QModelIndex)
    def on_tv_booklist_clicked(self, index):
        """
        单击表格行，填充输入框
        """
        LOG.info('选定行号: ' + str(index.row()))

        model = self.tv_booklist.model()
        bookinfo = model.getItem(index.row())
        # 填充输入框
        self.le_isbn_pic.setText(str(bookinfo[0]))
        self.le_bookname.setText(bookinfo[1])
        self.le_bookauthor.setText(bookinfo[2])
        self.le_publisher.setText(bookinfo[3])
        self.le_price.setText(bookinfo[4])
        self.star = bookinfo[5]
        self.num = bookinfo[6]
        self.le_average.setText(f"{self.star} / {self.num}")
        LOG.info(f"获取评分: 评分:{self.star} 人数:{self.num}")
        # self.le_bookclass.setText(bookinfo[5])
        self.cb_bookclass.setCurrentIndex(bclass[bookinfo[7]])

        self.le_bookshelf.setText(bookinfo[8])

    def refreshonebookinfo(self, arow):
        """
        更新图书信息

        """
        bookinfo = self.get_douban_isbn(arow)

        if len(bookinfo) >= 7:
            LOG.info('-'.join(bookinfo[:5]))
            self.model.updateItem(bookinfo)
        self.number += 1

        self.statusBar.showMessage(self.barstr + str(self.number))

    @pyqtSlot()
    def on_pb_refresh_clicked(self):
        """
        批量刷新表格中所有ISBN的图书信息
        """
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
            "共 " + str(self.model.rowCount()) + " 条记录" + self.appver))

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
        重置筛选状态，清空输入框
        """
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
        self.statusBar.showMessage(
            "共 " + str(self.model.rowCount()) + " 条记录" + self.appver)

    def genLoveMenu(self, pos):
        """
        自定义右键菜单，添加删除选项
        """
        menu = QMenu(self)
        ico_del = QIcon('delete.png')
        self.dele = menu.addAction(ico_del, u"删除")
        self.action = menu.exec(self.tv_booklist.mapToGlobal(pos))

    @pyqtSlot(QPoint)
    def on_tv_booklist_customContextMenuRequested(self, pos):

        # indexlist = self.tv_booklist.selectedIndexes()
        # inlist = set( ind.row() for ind in indexlist)
        # print(inlist)

        # ######### 删除当前行 ########################
        # if self.model.rowCount() > 0:
        #     indexs = self.tv_booklist.selectedIndexes()
        #     if len(indexs) > 0:
        #         index = indexs[0].row()
        #         self.genLoveMenu(pos)
        #         if self.action == self.dele:
        #             # self.model.deleteItem(self.tv_booklist.currentIndex().row())

        #             bookinfo = self.model.getItem(index)
        #             self.model.deleteItem(bookinfo[0])

        # ################## 多选删除 ##############
        if self.model.rowCount() > 0:
            indexs = self.tv_booklist.selectedIndexes()
            indexlist = set(index.row() for index in indexs)
            isbnlist = []
            for aindex in indexlist:
                isbnlist.append(self.model.getItem(aindex)[0])
            LOG.info(f"选中信息  {len(isbnlist)} 项:   {isbnlist}")
            if len(isbnlist) > 0:
                self.genLoveMenu(pos)
                if self.action == self.dele:
                    for isbn in isbnlist:
                        self.model.deleteItem(isbn)
                        LOG.info(f"删除信息： {isbn}")
                    self.statusBar.showMessage("共 " +
                                               str(self.model.rowCount()) +
                                               " 条记录" + self.appver)

    @pyqtSlot()
    def on_pb_search_clicked(self):
        """
        根据关键词筛选图书数据
        """

        search = self.le_bookname.text().strip()
        self.model.search(search)
        self.statusBar.showMessage(
            "共 " + str(self.model.rowCount()) + " 条记录" + self.appver)

    @pyqtSlot(QModelIndex)
    def on_tv_booklist_doubleClicked(self, index):
        """
        双击表格行，显示图书详情
        """
        # self.Dialog = QtWidgets.QDialog()
        # self.CW_bookinfo = Ui_Dialog()
        # self.CW_bookinfo.setupUi(self.Dialog)
        # self.Dialog.setModal(True)
        indx = index.row()
        bookinfo = self.model.getItem(indx)
        isbn_list = self.get_column_data(0)

        self.CW_bookinfo = BookInfo.BookInfo(
            parent=self, isbn_list=isbn_list, indx=indx)
        # self.CW_bookinfo.setModal(True)

        # self.Dialog.setWindowModality(Qt.ApplicationModal)
        # 在PyQt6中，QtCore.Qt.ApplicationModal属性已经被移除，
        # 可以使用QApplication.setModal()方法来设置模态窗口。该方法接受一个布尔值作为参数，True表示应用程序进入模态状态，False表示退出模态状态。

        self.refreshBookInfo(str(bookinfo[0]))

        # douban_bookinfo = self.get_douban_isbn(str(bookinfo[0]))
        # url = douban_bookinfo[9]
        # ref = 'https://' + url.split('/')[2]

        # header = {
        #     'User-Agent':
        #     'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.79'
        # }
        # header['Referer'] = ref
        # res = requests.get(douban_bookinfo[9], headers=header)
        # img = QImage.fromData(res.content)

        # self.CW_bookinfo.lb_bookcover.setPixmap(QPixmap.fromImage(img))

        # self.CW_bookinfo.tb_bookinfo.setText(
        #     '<b><font color="white" size="5">' + douban_bookinfo[1] +
        #     '</font></b>')

        # self.CW_bookinfo.tb_bookinfo.append('<br><b>作者: </b>' +
        #                                     douban_bookinfo[2])
        # self.CW_bookinfo.tb_bookinfo.append('<br><b>出版: </b>' +
        #                                     douban_bookinfo[3])
        # self.CW_bookinfo.tb_bookinfo.append('<br><b>价格: </b>' +
        #                                     douban_bookinfo[4])
        # self.CW_bookinfo.tb_bookinfo.append('<br><b>日期: </b>' +
        #                                     douban_bookinfo[10])
        # self.CW_bookinfo.tb_bookinfo.append('<br><b>ISBN: </b>' +
        #                                     douban_bookinfo[0])

        # self.CW_bookinfo.tb_bookinfo.append(
        #     '<br><b>评分: </b>' + str(douban_bookinfo[11]['average']) + '分/ ' +
        #     str(douban_bookinfo[11]['numRaters']) + '人')
        # self.CW_bookinfo.tb_bookinfo.append(
        #     '<br><b>链接: &emsp;&emsp;&emsp;&emsp;&emsp; </b>[<a style="color: #FFFFFF;" href="' + douban_bookinfo[12] + '"> 豆瓣 </a>]')

        # Recomm = ((float(douban_bookinfo[11]['average'])) - 2.5) * \
        #     math.log(float(douban_bookinfo[11]['numRaters']))
        # self.CW_bookinfo.tb_bookinfo.append(
        #     '<br><b>推荐: </b>' + str(round(Recomm)))
        # self.CW_bookinfo.lb_next.setText('<a href="https://www.baidu.com/">>>')

        # # r = requests.get(book_dict['image'])
        # # im = cv.imdecode(np.frombuffer(r.content, np.uint8), cv.IMREAD_COLOR) # 直接解码网络数据
        # # cv.imshow('im', im)
        # # cv.waitKey(0)
        # # self.CW_bookinfo.tb_bookinfo.append('<a href="https://www.douban.com">douban</a>')

        # # self.Dialog.setWindowTitle("图书信息 - " + douban_bookinfo[1])

        # LOG.info(f'获取封面信息 {len(douban_bookinfo)} 项: {douban_bookinfo}')
        # # self.Dialog.setFixedSize(self.Dialog.width(), self.Dialog.height())

        # # self.Dialog.show()

        # self.CW_bookinfo.setWindowTitle("图书信息 - " + douban_bookinfo[1])
        # self.CW_bookinfo.show()
        # tb_y = self.CW_bookinfo.tb_bookinfo.pos().y()

        # tb_height = self.CW_bookinfo.tb_bookinfo.document().size().height() + \
        #     self.CW_bookinfo.tb_bookinfo.contentsMargins().top() + \
        #     self.CW_bookinfo.tb_bookinfo.contentsMargins().bottom()
        # self.CW_bookinfo.tb_bookinfo.setFixedHeight(round(tb_height))
        # move_y = 311-round(tb_height)
        # self.CW_bookinfo.tb_bookinfo.setGeometry(self.CW_bookinfo.tb_bookinfo.pos().x(),
        #                                          tb_y+move_y, self.CW_bookinfo.tb_bookinfo.width(),
        #                                          self.CW_bookinfo.tb_bookinfo.height())

    def refreshBookInfo(self, ISBN):
        """
        根据ISBN，通过豆瓣接口获取图书相信信息，并刷新图书详细信息子窗口
        """

        douban_bookinfo = self.get_douban_isbn(ISBN)
        url = douban_bookinfo[9]
        ref = 'https://' + url.split('/')[2]

        header = {
            'User-Agent':
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.79'
        }
        header['Referer'] = ref
        res = requests.get(douban_bookinfo[9], headers=header)
        img = QImage.fromData(res.content)

        # self.CW_bookinfo = BookInfo.BookInfo(parent=self)
        self.CW_bookinfo.lb_bookcover.setPixmap(QPixmap.fromImage(img))

        self.CW_bookinfo.tb_bookinfo.setText(
            '<b><font color="white" size="5">' + douban_bookinfo[1] +
            '</font></b>')

        self.CW_bookinfo.tb_bookinfo.append('<br><b>作者: </b>' +
                                            douban_bookinfo[2])
        self.CW_bookinfo.tb_bookinfo.append('<br><b>出版: </b>' +
                                            douban_bookinfo[3])
        self.CW_bookinfo.tb_bookinfo.append('<br><b>价格: </b>' +
                                            douban_bookinfo[4])
        self.CW_bookinfo.tb_bookinfo.append('<br><b>日期: </b>' +
                                            douban_bookinfo[10])
        self.CW_bookinfo.tb_bookinfo.append('<br><b>ISBN: </b>' +
                                            douban_bookinfo[0])

        self.CW_bookinfo.tb_bookinfo.append(
            '<br><b>评分: </b>' + str(douban_bookinfo[11]['average']) + '分/ ' +
            str(douban_bookinfo[11]['numRaters']) + '人')
        self.CW_bookinfo.tb_bookinfo.append(
            '<br><b>链接: &emsp;&emsp;&emsp;&emsp;&emsp; </b>[<a style="color: #FFFFFF;" href="' + douban_bookinfo[12] + '"> 豆瓣 </a>]')

        Recomm = ((float(douban_bookinfo[11]['average'])) - 2.5) * \
            math.log(float(douban_bookinfo[11]['numRaters']))
        self.CW_bookinfo.tb_bookinfo.append(
            '<br><b>推荐: </b>' + str(round(Recomm)))

        # r = requests.get(book_dict['image'])
        # im = cv.imdecode(np.frombuffer(r.content, np.uint8), cv.IMREAD_COLOR) # 直接解码网络数据
        # cv.imshow('im', im)
        # cv.waitKey(0)
        # self.CW_bookinfo.tb_bookinfo.append('<a href="https://www.douban.com">douban</a>')

        # self.Dialog.setWindowTitle("图书信息 - " + douban_bookinfo[1])

        LOG.info(f'获取封面信息 {len(douban_bookinfo)} 项: {douban_bookinfo}')
        # self.Dialog.setFixedSize(self.Dialog.width(), self.Dialog.height())

        # self.Dialog.show()

        self.CW_bookinfo.setWindowTitle("图书信息 - " + douban_bookinfo[1])
        self.CW_bookinfo.show()
        tb_y = self.CW_bookinfo.tb_bookinfo.pos().y()

        tb_height = self.CW_bookinfo.tb_bookinfo.document().size().height() + \
            self.CW_bookinfo.tb_bookinfo.contentsMargins().top() + \
            self.CW_bookinfo.tb_bookinfo.contentsMargins().bottom()
        self.CW_bookinfo.tb_bookinfo.setFixedHeight(round(tb_height))
        move_y = 0  # 311-round(tb_height)
        self.CW_bookinfo.tb_bookinfo.setGeometry(self.CW_bookinfo.tb_bookinfo.pos().x(),
                                                 tb_y+move_y, self.CW_bookinfo.tb_bookinfo.width(),
                                                 self.CW_bookinfo.tb_bookinfo.height())

    def get_column_data(self, column_index):
        """
        核心方法：获取模型指定列的所有数据
        :param column_index: 目标列索引（从0开始）
        :return: 列数据列表
        """
        # 步骤1：校验列索引是否合法
        if column_index < 0 or column_index >= self.model.columnCount():
            return []

        # 步骤2：初始化列数据列表
        column_data = []

        # 步骤3：遍历所有行，提取对应列的数据
        row_count = self.model.rowCount()
        for row in range(row_count):
            # 创建当前行+目标列的索引
            index = self.model.index(row, column_index)
            # 获取「显示角色」的数据（可改为 EditRole 等）
            data = self.model.data(index, Qt.ItemDataRole.DisplayRole)
            # 过滤空值（可选）
            if data is not None and data != QVariant():
                column_data.append(data)

        return column_data

    @pyqtSlot()
    def on_pb_search_douban_clicked(self):
        """
        打开豆瓣搜索子窗口
        """
        # self.Dialog = QtWidgets.QDialog()
        # self.CW_booksearch = Ui_Dialog_S()
        # self.CW_booksearch.setupUi(self.Dialog)
        # self.Dialog.setModal(True)
        # self.Dialog.setFixedSize(self.Dialog.width(), self.Dialog.height())
        # self.Dialog.show()
        bs = BookSearch.BookSearch(self)
        bs.bookinfoSignal.connect(self.getDialogSignal)
        search = self.le_bookname.text().strip()
        if len(search) >= 2:
            bs.le_search_douban.setText(search)
        bs.setModal(True)
        bs.show()

    def getDialogSignal(self, connect):
        """
        更新状态栏图书总记录数
        """
        LOG.info(f'获取图书信息: {connect}')
        self.model.updateItem(connect)
        self.statusBar.showMessage(
            "共 " + str(self.model.rowCount()) + " 条记录" + self.appver)

    @pyqtSlot()
    def on_pb_template_clicked(self):
        """
        导出空表格模板（仅含列名），方便用户按格式填写数据。
        """
        csvNamepath, csvType = QFileDialog.getSaveFileName(
            self, "导出模板", "模板", "*.csv;;All Files(*)")
        if csvNamepath != "":
            df = self.model._data
            df.head(0).to_csv(csvNamepath, index=False)


if __name__ == "__main__":
    # 创建应用程序
    app = QApplication(sys.argv)
    # apply_stylesheet(app, theme='dark_blue.xml')

    # 设置暗黑主题
    app.setStyleSheet(qdarkstyle.load_stylesheet())  # 默认样式：暗黑样式
    # 创建主窗口
    blmain = BLmainWindow()
    # # 浅色样式
    # app.setStyleSheet(qdarkstyle.load_stylesheet(qdarkstyle.LightPalette))
    # # 深色样式
    # app.setStyleSheet(qdarkstyle.load_stylesheet(qdarkstyle.DarkPalette))

    # app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
    blmain.setWindowTitle("图书信息管理")
    blmain.show()
    # 运行应用
    sys.exit(app.exec())
