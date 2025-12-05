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


# 初始化日志对象（确保全局已定义，若未定义可补充：LOG = logging.getLogger(__name__)）
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
        """
        【PyQt 表格模型必需重写方法】返回表格的总行数（筛选后的数据行数）
        作用：QTableView 会调用此方法获取表格行数，从而渲染对应数量的行
        
        :param parent: PyQt 模型规范要求的父索引参数，用于树形模型（如 QTreeView）的父子节点计数；
                       表格模型（QTableView）中无父子节点，该参数恒为 QModelIndex()（空索引/None）
        :type parent: QModelIndex | None
        :return: 表格的总行数，即底层 DataFrame 的行数
        :rtype: int
        :note:
            1. self._data.shape[0] 是 pandas DataFrame 获取行数的高效方式（O(1) 时间复杂度）；
            2. 若需返回「筛选后/过滤后」的行数，需先更新 self._data 为筛选后的 DataFrame；
            3. 空 DataFrame 时返回 0，QTableView 会显示空表格，无异常。
        """
        # 核心逻辑：返回 DataFrame 的行数（shape[0] 等价于 len(self._data)，但性能更优）
        # shape 返回元组 (行数, 列数)，shape[0] 取行数，shape[1] 取列数
        return self._data.shape[0]

    def appendRow(self, arowdata):
        """
        核心方法：向表格模型中新增一行数据，并通知视图刷新
        适配PyQt模型规范：通过beginResetModel/endResetModel触发视图重新渲染，保证数据同步
        
        :param arowdata: 待新增的行数据，支持两种格式（兼容设计）：
                         1. 字典（推荐）：key为列名，value为对应列的值（如{"ISBN":"978xxx", "书名":"Python编程"}）
                         2. 列表/元组：按列顺序匹配的值（需与_data的列顺序完全一致）
        :type arowdata: dict | list | tuple
        :raises KeyError: 若字典的key与_data的列名不匹配时触发
        :raises ValueError: 若数据类型与列的 dtype 不兼容时触发
        """
        try:
            # ===================== PyQt模型刷新通知 =====================
            # 通知视图：模型数据即将重置（必须配对begin/end，否则视图不刷新）
            # 作用：暂停视图更新，避免多次触发刷新，提升性能；结束后视图重新读取模型数据
            self.beginResetModel()

            # ===================== DataFrame追加数据 =====================
            # self._data.shape[0]：获取当前DataFrame的行数（作为新行的索引）
            # loc赋值：按索引追加一行，自动对齐列名（字典格式）或按列顺序填充（列表/元组）
            # 示例：若当前有5行，新行索引为5，直接赋值实现追加
            self._data.loc[self._data.shape[0]] = arowdata

        except KeyError as e:
            # 列名不匹配时的异常提示（便于调试）
            raise KeyError(f"新增行失败：列名不匹配 - {e}，当前模型列名：{list(self._data.columns)}")
        except ValueError as e:
            # 数据类型不兼容时的异常提示
            raise ValueError(f"新增行失败：数据类型不兼容 - {e}")
        finally:
            # ===================== 结束模型刷新通知 =====================
            # 必须调用，通知视图：模型数据已重置，立即刷新展示新数据
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
    继承关系：
    - QMainWindow：PyQt6主窗口基类，提供菜单栏、状态栏、中心窗口等核心结构
    - Ui_mainWindow：Qt Designer生成的UI类，包含主窗口所有控件（表格、按钮、输入框等）
    核心职责：
    1. 初始化主窗口UI并固定尺寸，避免用户随意调整导致布局错乱
    2. 创建初始空数据模型，绑定到图书列表表格（tv_booklist）
    3. 配置表格视图的布局规则（列宽自适应/可手动调整）、上下文菜单策略
    4. 初始化全局状态变量（批量刷新计数、进度前缀、版本号），设置状态栏初始显示
    """

    def __init__(self, parent=None):
        """
        构造函数：初始化图书管理系统主窗口
        
        @param parent: 父窗口对象（默认None，主窗口无父窗口）
        @type parent: QWidget | None
        """
        # ===================== 1. 父类初始化 & 窗口基础配置 =====================
        # 调用父类构造函数，初始化QMainWindow和Ui_mainWindow的控件        
        super().__init__(parent)
        # 加载UI界面（由Ui_mainWindow提供的setupUi方法，初始化所有控件）
        self.setupUi(self)
        # 固定窗口大小：禁止用户拉伸/缩小窗口，保证布局稳定性（适配UI设计尺寸）
        self.setFixedSize(self.width(), self.height())

        # ===================== 2. 创建初始空数据模型（DataFrame） =====================
        # 定义初始空数据的字段结构（与表格列一一对应）
        data = {
            'ISBN': [],      # 图书唯一标识
            '书名': [],      # 图书名称
            '作者': [],      # 作者（含译者）
            '出版': [],      # 出版社
            '价格': [],      # 价格（清洗后）
            '评分': [],      # 豆瓣平均分
            '人数': [],      # 豆瓣评价人数
            '分类': [],      # 自定义分类（如“计划”“已读”）
            '书柜': []       # 书柜位置（如“A区1层”）
        }
        # 创建空DataFrame，强制所有字段为字符串类型（避免后续数据类型异常）
        df = pd.DataFrame(data=data, dtype=object)
        # 索引从1开始（适配用户对“第1行”的直观认知，而非编程默认的0起始）
        df.index = df.index + 1  # 调整 qtableview 序号


        # ===================== 3. 初始化表格模型并绑定到表格视图 =====================
        # 实例化自定义表格模型（TableModel），适配PyQt6的QTableView，支持DataFrame数据源
        self.model = TableModel(df)
        # 将模型绑定到图书列表表格（tv_booklist），初始化表头和空数据
        self.tv_booklist.setModel(self.model)  # 填充 Qtableview 表头
        # 显示表格的垂直表头（行号列），便于用户查看行序号
        self.tv_booklist.verticalHeader().setVisible(True)

        # ===================== 4. 注释掉的历史代码（保留供参考） =====================
        # 旧逻辑：使用QStandardItemModel（已替换为自定义TableModel，适配DataFrame）        
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


        # ===================== 5. 表格列宽布局配置（混合自适应+手动调整） =====================
        # 全局列宽策略：默认所有列自适应拉伸（填充窗口宽度）
        self.tv_booklist.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch)
        # 单独配置关键列为“可手动调整”（用户可按需拉伸/缩小）：
        # 列1（书名）：支持手动调整宽度（避免长书名被挤压）        
        self.tv_booklist.horizontalHeader().setSectionResizeMode(
            1, QtWidgets.QHeaderView.ResizeMode.Interactive)
        # 列2（作者）：支持手动调整宽度
        self.tv_booklist.horizontalHeader().setSectionResizeMode(
            2, QtWidgets.QHeaderView.ResizeMode.Interactive)
        # 列3（出版社）：支持手动调整宽度
        self.tv_booklist.horizontalHeader().setSectionResizeMode(
            3, QtWidgets.QHeaderView.ResizeMode.Interactive)
        
        # ===================== 6. 上下文菜单配置 =====================
        # 设置表格的上下文菜单策略为“自定义”：右键点击表格时触发自定义菜单逻辑
        # 替代默认的系统菜单，实现右键删除、导出等自定义功能
        self.tv_booklist.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu)  # 对象的上下文菜单的策略
        

        # ===================== 7. 初始化全局状态变量 =====================
        self.number = 0          # 批量刷新计数（记录已刷新的图书数量）
        self.barstr = ''         # 批量刷新进度前缀（如“信息更新:100/”）
        self.appver = '   ver-1.0.2'  # 软件版本号（用于状态栏显示）

        # ===================== 8. 初始化状态栏显示 =====================
        # 状态栏默认显示软件版本号，给用户版本反馈
        self.statusBar.showMessage(self.appver)

    # ===================== 按钮槽函数 =====================
    @pyqtSlot()
    def on_pb_load_clicked(self):
        """
        槽函数：响应“加载CSV”按钮点击事件，加载本地CSV格式的图书数据到表格
        核心逻辑：
        1. 打开文件选择对话框，筛选CSV格式文件（兼容所有文件兜底）
        2. 读取CSV文件并做数据预处理：
           - 强制所有字段为字符串类型（避免ISBN/评分等字段类型异常）
           - 填充空值为空字符串（避免表格显示NaN）
           - 索引从1开始（符合用户直观的行号认知）
        3. 初始化表格模型并绑定到图书列表表格，展示加载的数据
        4. 记录加载的文件路径，更新状态栏显示总记录数+软件版本
        注：核心优化点是数据类型和空值处理，避免CSV加载后表格显示异常
        """
        # ===================== 1. 打开文件选择对话框，选择CSV文件 =====================
        # 参数说明：
        # - self：父窗口对象，用于关联对话框
        # - "选择存储文件"：对话框标题
        # - "."：默认打开路径（当前工作目录）
        # - "*.csv;;All Files(*)"：文件类型过滤（优先显示CSV，兜底显示所有文件）
        # 返回值：csvNamepath=选中的CSV文件路径，csvType=选中的文件类型（如"*.csv"）
        csvNamepath, csvType = QFileDialog.getOpenFileName(
            self, "选择存储文件", ".", "*.csv;;All Files(*)")
        # ===================== 2. 校验是否选中有效文件（空路径则跳过处理） =====================
        if csvNamepath != "":
            # ===================== 3. 读取CSV文件并进行数据预处理 =====================
            # 读取CSV：
            # - dtype='object'：强制所有字段为字符串类型（关键！避免ISBN前导零丢失、数字字段被识别为数值型）
            # - 默认UTF-8编码（适配大多数CSV文件，若有乱码可补充encoding='gbk'等）
            df = pd.read_csv(csvNamepath, dtype='object')  # 数据全部转换为字符串型
            # 注释掉的历史逻辑：手动插入评分/人数列（已由CSV文件自带字段替代）
            # df.insert(loc=5, column='评分', value=0)
            # df.insert(loc=6, column='人数', value=0)
            # 索引重置：将pandas默认的0起始索引改为1起始（符合用户对“第1行”的直观认知）
            df = df.dropna(axis=0, subset=["ISBN"])
            df.index = df.index + 1
            # 空值填充：将DataFrame中的NaN/空值替换为空字符串（避免表格显示“NaN”，提升UI体验）
            df.fillna('', inplace=True)

            # ===================== 4. 初始化表格模型并绑定到表格视图 =====================
            # 实例化自定义表格模型（TableModel），传入预处理后的DataFrame
            self.model = TableModel(df)
            # 将模型绑定到图书列表表格（tv_booklist），完成数据展示
            self.tv_booklist.setModel(self.model)  # 填充csv数据
            
            # ===================== 5. 记录文件路径 & 更新状态栏反馈 =====================
            # 将加载的CSV文件路径填充到输入框（le_booklist），便于用户查看当前加载的文件
            self.le_booklist.setText(csvNamepath)
            # 注释掉的历史逻辑：旧表格控件绑定（已替换为tv_booklist）
            # self.table.setModel(self.model)
            
            # 获取表格模型的总行数（加载的记录数）
            rowscount = self.model.rowCount()
            # 状态栏显示：总记录数 + 软件版本信息（self.appver为版本号字符串）
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
        
        try:
            csvNamepath, csvType = QFileDialog.getSaveFileName(
                self, "保存存储文件", "E:\\minipan\\Seafile\\资料", "*.csv;;All Files(*)")
            if csvNamepath != "":
                df = self.model._data
                df.to_csv(csvNamepath, index=False)
                
        except PermissionError as e:
            QtWidgets.QMessageBox.warning(
                self,                # 父窗口（主窗口）
                "错误",              # 提示框标题
                f"文件写入失败：\n{str(e)} \n\n\n请检查文件是否被其他程序占用或以管理员身份运行本程序！",    # 提示内容
                QtWidgets.QMessageBox.StandardButton.Ok  # 确认按钮
            )
                
    @pyqtSlot()
    def on_pb_scan_clicked(self):
        """
        槽函数：响应“扫描条形码”按钮点击事件
        核心逻辑：
        1. 打开文件选择对话框，选择本地条形码图片（支持png/jpg格式）
        2. 解决OpenCV中文路径读取问题：通过np.fromfile+cv.imdecode读取图片
        3. 图像处理优化：灰度化→二值化，增强条形码对比度，提升识别率
        4. 条形码解码：使用pyzbar识别图片中的条形码数据（ISBN）
        5. 结果填充：将识别到的ISBN填充到ISBN输入框（le_isbn_pic）
        注：核心优化点是中文路径兼容和图像预处理，解决条形码识别成功率低的问题
        """
        # ===================== 1. 打开文件选择对话框，选择条形码图片 =====================
        # 参数说明：
        # - self：父窗口对象
        # - "选择条形码图片"：对话框标题
        # - "."：默认打开路径（当前目录）
        # - "*.png;;*.jpg;;All Files(*)"：文件类型过滤（仅显示png/jpg/所有文件）
        # 返回值：picNamepath=选中文件的路径，picType=选中的文件类型
        picNamepath, picType = QFileDialog.getOpenFileName(
            self, "选择条形码图片", ".", "*.png;;*.jpg;;All Files(*)")
        
        # ===================== 2. 校验是否选中图片（空路径则不处理） =====================
        if picNamepath != "":
            # image = cv.imread(img_path)
            # ===================== 3. 读取图片（兼容中文路径） =====================
            # 问题：cv.imread不支持中文路径，会返回None
            # 解决方案：np.fromfile读取文件字节→cv.imdecode解码为图像
            # cv.IMREAD_COLOR：以彩色模式读取（忽略透明度）
            image = cv.imdecode(np.fromfile(picNamepath, dtype=np.uint8),
                                cv.IMREAD_COLOR)

            # ===================== 4. 图像预处理（提升条形码识别率） =====================
            # 步骤1：灰度化（将彩色图转为灰度图，减少颜色干扰）
            gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)

            # 步骤2：二值化（将灰度图转为黑白二值图，增强条形码边缘对比度）
            # - 第一步：OTSU自动计算最优阈值（返回值binary为计算出的阈值）
            binary, _ = cv.threshold(gray, 0, 255, cv.THRESH_OTSU)
            # - 第二步：用OTSU阈值执行二值化，mat为二值化后的图像
            binary, mat = cv.threshold(gray, binary, 255, cv.THRESH_BINARY)

            # ===================== 5. 条形码解码 =====================
            # pyzbar.decode：识别图像中的条形码，返回条形码对象列表（支持EAN13等ISBN格式）
            barcode = pyzbar.decode(mat)
            # ===================== 6. 提取ISBN并填充输入框 =====================
            # 遍历识别到的条形码（通常只有1个）
            for bar in barcode:
                # bar.data：条形码原始二进制数据→解码为UTF-8字符串（即ISBN）
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
        核心方法：调用豆瓣图书API，根据ISBN获取图书完整信息并格式化
        核心逻辑：
        1. 校验ISBN长度有效性（仅处理13/17位ISBN，适配豆瓣API规则）
        2. 配置豆瓣API请求参数（apikey、模拟移动端请求头防反爬）
        3. 发送POST请求获取图书JSON数据（适配豆瓣API的请求方式）
        4. 解析响应数据，清洗/格式化核心字段（作者+译者、价格等）
        5. 计算图书推荐度（兼顾评分和评价人数，处理边界值避免计算异常）
        6. 无效数据处理：返回固定长度的空值列表，保证调用方数据结构统一
        7. 有效数据处理：返回包含14个字段的图书信息列表（13个基础字段+1个推荐度）
    
        @param isbn: 图书ISBN编号（豆瓣API仅支持13/17位有效ISBN）
        @type isbn: str
        @return: 图书信息列表，有效数据时含14个字段，无效时为13个空格的列表
                 字段索引说明（有效数据）：
                 0: ISBN          1: 书名          2: 作者+译者    3: 出版社
                 4: 价格（清洗后） 5: 豆瓣平均分    6: 评价人数    7: 分类（默认"计划"）
                 8: 书柜（默认"未设置"） 9: 封面小图URL  10: 出版日期  11: 完整评分字典
                 12: 豆瓣详情页URL 13: 推荐度（计算值）
        @rtype: list
        """
        # ===================== 1. 初始化返回值 & ISBN有效性校验 =====================
        # 初始化图书信息列表（最终返回）
        bookinfo = []
        # 校验ISBN长度：豆瓣API仅识别13位标准ISBN，17位为特殊格式（如带分隔符），其他长度直接返回空列表
        if len(isbn) != 13 and len(isbn) != 17:
            return bookinfo
        # ===================== 2. 配置豆瓣API请求参数 =====================
        # 豆瓣图书API地址（按ISBN查询的固定路径）
        url = "https://api.douban.com/v2/book/isbn/" + isbn

        # API密钥（apikey）：豆瓣开放平台申请，用于提升API调用限额，避免请求被拦截
        # apikey=0df993c66c0c636e29ecbb5344252a4a
        # apikey=0ac44ae016490db2204ce0a042db2916
        payload = {'apikey': '0ab215a8b1977939201640fa14c66bab'}
        # 请求头：模拟iPhone移动端浏览器，规避豆瓣API的反爬机制（PC端请求易被限制）
        headers = {
            "Referer":
            "https://m.douban.com/tv/american", # 模拟移动端来源页，提升请求合法性
            "User-Agent":
            "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1"
        }

        # {"content-type": "multipart/form-data;","User-Agent": "MicroMessenger/","Referer": "https://servicewechat.com/wx2f9b06c1de1ccfca/91/page-frame.html"}
        
        # ===================== 3. 发送API请求并解析响应 =====================
        # 发送POST请求（豆瓣该API支持POST，相比GET更不易被反爬拦截）
        response = requests.post(url, data=payload, headers=headers)
        
        # 解析JSON响应为字典
        book_dict = json.loads(response.text)

        # ===================== 4. 数据有效性校验 =====================
        # 校验响应数据是否完整（字典长度>5，避免返回空/残缺数据
        if len(book_dict) > 5:
            # ===================== 5. 数据清洗与格式化 =====================
            # 处理作者+译者：作者用/分隔，有译者则追加“译者:XXX”
            author = '/'.join(book_dict['author'])
            if len(book_dict['translator']) > 0:
                author += ' 译者: '
                author += '/'.join(book_dict['translator'])
            # 提取评分信息（包含平均分、评价人数）
            rating = book_dict['rating']
            # 清洗价格：移除CNY/元符号，去除首尾空格（兼容不同格式的价格字符串）
            price = book_dict['price']
            price = price.replace('CNY', '').replace('元', '').strip()

            # ===================== 6. 填充图书信息列表（按固定索引） =====================
            bookinfo.append(isbn)                          # 0: ISBN
            bookinfo.append(book_dict['title'])            # 1: 书名
            bookinfo.append(author)                        # 2: 作者+译者
            bookinfo.append(book_dict['publisher'])        # 3: 出版社
            bookinfo.append(price)                         # 4: 价格（清洗后）
            bookinfo.append(rating['average'])             # 5: 豆瓣平均分
            bookinfo.append(rating['numRaters'])           # 6: 评价人数
            bookinfo.append('计划')                        # 7: 分类（默认值）
            bookinfo.append('未设置')                      # 8: 书柜位置（默认值）
            bookinfo.append(book_dict['images']['small'])  # 9: 封面小图URL（替代原image字段）
            bookinfo.append(book_dict['pubdate'])          # 10: 出版日期
            bookinfo.append(book_dict['rating'])           # 11: 完整评分字典（含平均分/人数）
            bookinfo.append(book_dict['alt'])              # 12: 豆瓣图书详情页URL
    
            # ===================== 7. 计算图书推荐度（自定义公式） =====================
            # 日志记录评分信息（便于调试推荐度计算）
            LOG.info(f"ISBN {isbn} 评分信息：{rating}")
            LOG.info(f"ISBN {isbn} 完整图书信息：{book_dict}")
            
            # 推荐度公式：(平均分 - 2.5) × ln(评价人数 + 1)
            # 设计逻辑：
            # - 减2.5：过滤低分图书（平均分<2.5时推荐度为负）
            # - +1：避免评价人数为0时ln(0)抛出数学异常
            # - round：四舍五入取整
            recommend = round((float(rating['average']) - 2.5) *
                              math.log(float(rating['numRaters']) + 1)) 
            bookinfo.append(str(recommend)) # 13: 推荐度（字符串格式）
        else:
            # ===================== 8. 无效数据处理（返回固定长度空值） =====================
            # 响应数据残缺时，填充13个空格，保证返回列表长度统一，避免调用方索引越界
            # for i in range(13):
            #     bookinfo.append(" ")
            return None
        
        # ===================== 9. 返回格式化后的图书信息 =====================        
        return bookinfo

    @pyqtSlot()
    def on_pb_insert_clicked(self):
        """
        槽函数：响应“插入/更新”按钮点击事件
        核心逻辑：
        1. 从界面输入框/下拉框提取图书信息（ISBN、书名、作者等）
        2. 组装图书信息列表（兼容模型的字段顺序）
        3. 日志记录待插入/更新的信息（便于调试）
        4. 调用表格模型的updateItem方法：
           - 若ISBN已存在：更新对应行的信息
           - 若ISBN不存在：插入新行
        5. 更新状态栏，显示当前表格总记录数+软件版本
        注：分类字段已从文本框改为下拉框，保证分类值规范
        """
        # ===================== 1. 提取界面输入的图书信息 =====================
        isbn = self.le_isbn_pic.text()          # ISBN输入框
        title = self.le_bookname.text()         # 书名输入框
        author = self.le_bookauthor.text()      # 作者输入框
        publisher = self.le_publisher.text()    # 出版社输入框
        price = self.le_price.text()            # 价格输入框

        # 分类字段：从下拉框（cb_bookclass）获取选中文本（替代旧文本框le_bookclass）
        # bookclass = self.le_bookclass.text()  # 注释掉的旧逻辑：文本框输入，易不规范        
        bookclass = self.cb_bookclass.currentText()
        bookshelf = self.le_bookshelf.text() # 书柜位置输入框

        # ===================== 2. 组装图书信息列表（匹配模型字段顺序） =====================
        # 字段顺序：ISBN、书名、作者、出版社、价格、评分、评价人数、分类、书柜
        bookinfo = [
            isbn, title, author, publisher, price, 
            self.star, self.num, # 评分/评价人数（从实例变量获取，由豆瓣API填充）
            bookclass, bookshelf
        ]
        # ===================== 3. 日志记录 & 模型更新 =====================
        LOG.info(f'插入记录 {len(bookinfo)} 项:  {bookinfo}') # 调试用：记录操作数据
        self.model.updateItem(bookinfo) # 核心：插入新行或更新已有ISBN的行
        
        # ===================== 4. 更新状态栏反馈 =====================
        self.statusBar.showMessage(
            "共 " + str(self.model.rowCount()) + " 条记录" + self.appver)

    @pyqtSlot()
    def on_pb_getbookinfo_clicked(self):
        """
        槽函数：响应“获取图书信息”按钮点击事件
        核心逻辑：
        1. 从ISBN输入框提取ISBN，调用豆瓣API获取完整图书信息
        2. 校验API返回数据有效性：
           - 有效：填充界面输入框，设置分类/书柜默认值，更新表格模型
           - 无效：日志警告+弹窗提示ISBN错误
        3. 格式化评分显示（平均分/评价人数），更新状态栏记录数
        注：分类字段适配下拉框，无选中时默认选第0项（如“计划”）
        """
        # ===================== 1. 提取ISBN并调用豆瓣API =====================
        isbn = self.le_isbn_pic.text()   # 提取ISBN并去除首尾空格（避免空/空格干扰）
        bookinfo = self.get_douban_isbn(isbn.strip())  # 调用豆瓣API获取图书信息

        # ===================== 2. 校验API返回数据有效性 =====================
        if len(bookinfo) > 0:
            # ===================== 3. 填充界面输入框（从API返回数据提取） =====================
            self.le_bookname.setText(bookinfo[1])    # 书名
            self.le_bookauthor.setText(bookinfo[2])  # 作者+译者
            self.le_publisher.setText(bookinfo[3])  # 出版社
            self.le_price.setText(bookinfo[4])      # 价格（清洗后）
            
            # 提取并格式化评分/评价人数
            self.star = bookinfo[5]  # 豆瓣平均分（实例变量，供插入/更新使用）
            self.num = bookinfo[6]   # 评价人数（实例变量，供插入/更新使用）
            self.le_average.setText(f"{self.star} / {self.num}")  # 格式化显示
            LOG.info(f"获取评分: 评分:{self.star} 人数:{self.num}")  # 日志记录评分信息

            # ===================== 4. 设置分类/书柜默认值（保证字段非空） =====================
            # 旧逻辑：文本框分类为空时设为“未设”（已替换为下拉框）
            # if len(self.le_bookclass.text().strip()) == 0:
            #     self.le_bookclass.setText("未设")
            #     self.le_bookshelf.setText("未知")
            
            # 新逻辑：下拉框无选中文本时，默认选中第0项（如“计划”），书柜设为“未知”
            if len(self.cb_bookclass.currentText().strip()) == 0:
                self.cb_bookclass.setCurrentIndex(0) # 选中下拉框第0项（默认分类）
                self.le_bookshelf.setText("未知")    # 书柜默认值

            # ===================== 5. 更新表格模型（插入/更新） =====================
            # self.model.appendRow(bookinfo)  # 注释掉的旧逻辑：仅插入新行（无更新逻辑）
            self.model.updateItem(bookinfo)  # 核心：有则更新，无则插入
            # ===================== 6. 更新状态栏反馈 =====================
            self.statusBar.showMessage("共 " + str(self.model.rowCount()) +
                                       " 条记录" + self.appver)
        else:
            # ===================== 7. 无效ISBN处理（日志+弹窗提示） =====================
            LOG.warning("ISBN书号有误:  " + isbn)
            # 弹窗提示用户ISBN错误（模态提示框，强制用户确认）
            QtWidgets.QMessageBox.warning(
                self,                # 父窗口（主窗口）
                "错误",              # 提示框标题
                "ISBN书号有误！",    # 提示内容
                QtWidgets.QMessageBox.StandardButton.Yes  # 确认按钮
            )

    @pyqtSlot(QModelIndex)
    def on_tv_booklist_clicked(self, index):
        """
        单击表格行，填充输入框
        """
        """
        槽函数：响应图书列表表格（tv_booklist）的单击事件
        核心逻辑：
        1. 记录选中行号（日志调试）
        2. 从表格模型中获取选中行的完整图书信息
        3. 将图书信息逐一填充到界面输入框/下拉框，实现“选中行→编辑框回填”
        4. 格式化评分信息（平均分/评价人数），分类下拉框匹配预定义分类索引
        
        @param index: 单击位置的模型索引，包含选中行/列的位置信息
        @type index: QModelIndex
        """
        # ===================== 1. 日志记录：记录选中的行号（便于调试） =====================
        LOG.info('选定行号: ' + str(index.row())) #index.row()  # 获取单击的行索引（从0开始）

        # ===================== 2. 获取选中行的图书信息 =====================
        # 获取表格绑定的数据源模型
        model = self.tv_booklist.model()
        # 从模型中提取选中行的完整图书信息（getItem为自定义方法，返回行数据列表）
        bookinfo = model.getItem(index.row())
        # ===================== 3. 填充基础信息输入框 =====================
        # ISBN输入框（le_isbn_pic）：转为字符串避免类型显示异常
        self.le_isbn_pic.setText(str(bookinfo[0]))
        self.le_bookname.setText(bookinfo[1])
        self.le_bookauthor.setText(bookinfo[2])
        self.le_publisher.setText(bookinfo[3])
        self.le_price.setText(bookinfo[4])
        
        # ===================== 4. 处理评分信息（格式化显示） =====================
        # 提取评分（bookinfo[5]）和评价人数（bookinfo[6]）
        self.star = bookinfo[5]
        self.num = bookinfo[6]
        # 格式化评分显示：“平均分 / 评价人数”（如：8.5 / 10000）
        self.le_average.setText(f"{self.star} / {self.num}")
        # 日志记录评分信息（调试用，便于排查数据显示问题）
        LOG.info(f"获取评分: 评分:{self.star} 人数:{self.num}")
        # self.le_bookclass.setText(bookinfo[5])
        # ===================== 5. 设置图书分类下拉框 =====================
        # 注释掉的旧逻辑：直接填充分类文本（已替换为下拉框索引匹配）
        # self.le_bookclass.setText(bookinfo[5])
        
        # bookinfo[7]为分类文本（如“计划”），通过bclass映射转为下拉框索引
        # bclass字典：键=分类文本，值=下拉框选项索引（如{"计划":1}）
        self.cb_bookclass.setCurrentIndex(bclass[bookinfo[7]])

        # ===================== 6. 填充书柜位置输入框 =====================
        self.le_bookshelf.setText(bookinfo[8])

    def refreshonebookinfo(self, arow):
        """
        核心方法：单本图书信息刷新（多线程批量刷新的回调方法）
        核心逻辑：
        1. 根据传入的ISBN调用豆瓣API，获取最新图书信息
        2. 校验返回数据的有效性（核心字段≥7个），避免无效数据更新
        3. 记录关键图书信息日志（便于调试），更新表格模型中的对应记录
        4. 递增刷新计数，更新状态栏显示当前刷新进度
        注：该方法由多线程的progress信号触发，逐本刷新图书信息，避免UI阻塞
    
        @param arow: 待刷新图书的ISBN（唯一标识），由多线程传递
        @type arow: str
        """
        # ===================== 1. 调用豆瓣API获取单本图书最新信息 =====================
        # get_douban_isbn：自定义方法，传入ISBN返回图书信息列表（含ISBN、书名、作者等）
        bookinfo = self.get_douban_isbn(arow)

        # ===================== 2. 数据有效性校验（避免无效数据更新） =====================
        # 校验返回的图书信息至少包含7个核心字段（ISBN、书名、作者、出版社、价格、评分、评价人数）
        if len(bookinfo) >= 7:
            # 日志记录：拼接前5个核心字段（ISBN、书名、作者、出版社、价格），便于调试
            LOG.info('-'.join(bookinfo[:5]))
            # 更新表格模型中的对应记录（ISBN为唯一标识，存在则更新，不存在则新增）
            self.model.updateItem(bookinfo)
        # ===================== 3. 递增刷新计数，更新进度反馈 =====================
        # self.number：批量刷新的全局计数，每刷新一本+1    
        self.number += 1

        # 更新状态栏：显示当前刷新进度（格式：信息更新:总数量/当前数量）
        # self.barstr：预定义进度前缀（如"信息更新:100/"），拼接当前计数后显示
        self.statusBar.showMessage(self.barstr + str(self.number))

    @pyqtSlot()
    def on_pb_refresh_clicked(self):
        """
        槽函数：响应“批量刷新”按钮点击事件，多线程批量更新表格中所有ISBN的图书信息
        核心设计：
        1. 避免UI线程阻塞：将耗时的API调用放到子线程执行
        2. 生命周期管理：线程/工作对象完成后自动销毁，避免内存泄漏
        3. 状态反馈：禁用刷新按钮防止重复点击，线程结束后恢复按钮并更新状态栏
        4. 进度传递：通过自定义信号逐本刷新图书信息，实时反馈进度
        """
        # ===================== 1. 准备刷新数据 =====================
        # 从表格模型中获取第0列（ISBN列）的所有数据（去重/非空处理由getlist实现）
        # 调用 douban API 接口，根据 isbn编码 更新所有记录
        isbnlist = self.model.getlist(0)
        # 初始化刷新计数（用于进度提示）
        self.number = 0
        # 构建进度提示字符串（格式：信息更新: 总数量/）
        self.barstr = '信息更新:' + str(len(isbnlist)) + '/'

        # ===================== 2. 多线程配置（核心：避免UI阻塞） =====================
        # Step 1: 创建QThread线程对象（管理子线程生命周期）
        self.thread = QThread()
        # Step 2: 创建工作对象（封装批量刷新逻辑，不含UI操作）
        self.worker = RefreshBookinfoList(isbnlist)
        # Step 3: 将工作对象移动到子线程（PyQt6要求：UI相关操作必须在主线程，耗时操作在子线程）
        self.worker.moveToThread(self.thread)

            # ===================== 3. 信号槽绑定（线程/工作对象通信） =====================
            # 线程启动 → 触发工作对象的run方法（开始批量刷新）
        self.thread.started.connect(self.worker.run)  # 通知开始
        
        # 工作对象完成刷新 → 通知线程退出（结束子线程）
        self.worker.finished.connect(self.thread.quit)  # 结束后通知结束
        # 工作对象完成 → 销毁工作对象（释放内存，避免泄漏）
        self.worker.finished.connect(self.worker.deleteLater)  # 完成后删除对象
        # 线程退出 → 销毁线程对象（释放内存）
        self.thread.finished.connect(self.thread.deleteLater)  # 完成后删除对象
        # 工作对象的progress信号 → 绑定到单本图书刷新方法（逐本更新UI）
        self.worker.progress.connect(
            self.refreshonebookinfo)  # 绑定 progress 的信号
        
        # ===================== 4. 启动线程 & 控制UI状态 =====================
        # 启动子线程（触发thread.started信号，进而执行worker.run）
        self.thread.start()
        # 禁用刷新按钮：防止用户重复点击导致多线程冲突
        self.pb_refresh.setEnabled(False)

        # ===================== 5. 线程结束后的回调逻辑 =====================
        # 线程结束 → 恢复刷新按钮可用状态（lambda表达式传递无参回调）
        self.thread.finished.connect(lambda: self.pb_refresh.setEnabled(True))
        # 线程结束 → 更新状态栏提示（显示总记录数+软件版本）
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
        槽函数：响应“重置”按钮点击事件
        核心逻辑：
        1. 清空所有图书信息输入框（作者、书名、书柜、价格、出版社等）
        2. 重置图书分类下拉框为“无选中”状态（替代旧文本框清空逻辑）
        3. 恢复表格模型的筛选状态（显示所有图书记录，取消之前的搜索/筛选）
        4. 更新状态栏，显示当前表格的总记录数 + 软件版本信息
        """
        # ===================== 1. 清空各字段输入框 =====================
        # 清空作者输入框

        self.le_bookauthor.clear()
        # self.le_bookclass.clear()
        # 注释掉的旧逻辑：清空图书分类文本框（已替换为下拉框cb_bookclass）
        # self.le_bookclass.clear()
        # 重置图书分类下拉框为无选中状态（index=-1），而非默认选中第一项
        self.cb_bookclass.setCurrentIndex(-1)
        # self.le_booklist.clear()
        # 注释掉的旧逻辑：清空图书列表相关输入框（该控件已移除/未使用）
        # self.le_booklist.clear()
        # 清空书名输入框
        self.le_bookname.clear()
        # 清空书柜位置输入框
        self.le_bookshelf.clear()
        # self.le_isbn_pic.clear()
        # 注释掉的逻辑：保留ISBN输入框内容（业务需求：重置时不清除ISBN）
        # self.le_isbn_pic.clear()
        # 清空价格输入框
        self.le_price.clear()
        # 清空出版社输入框
        self.le_publisher.clear()
        
        # ===================== 2. 重置表格模型筛选状态 =====================
        # 调用模型的reset方法：恢复所有数据显示，取消之前的搜索/筛选条件
        self.model.reset()
        # ===================== 3. 更新状态栏反馈 =====================
        # 状态栏显示当前表格总记录数 + 软件版本信息（self.appver为版本号字符串）
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
        
        """
        槽函数：响应图书列表表格（tv_booklist）的右键菜单请求事件
        核心逻辑：
        1. 校验表格是否有数据，无数据则不生成菜单
        2. 获取表格中选中的所有单元格索引，去重后得到选中行索引
        3. 提取选中行对应的ISBN列表（ISBN为图书唯一标识）
        4. 生成右键菜单并获取用户选择的操作（如删除）
        5. 若选择“删除”，遍历ISBN列表删除对应记录，更新日志和状态栏
        6. 仅当有有效选中行时才触发菜单逻辑
        
        @param pos: 右键点击的位置（屏幕坐标），用于定位显示右键菜单
        @type pos: QPoint
        """
        # ===================== 1. 校验表格是否有数据 =====================
        # 表格模型行数>0时才处理右键菜单（无数据时不显示菜单）
        if self.model.rowCount() > 0:
            # ===================== 2. 获取选中行索引（去重） =====================
            # 获取所有选中单元格的索引（包含多列，需去重得到行索引）
            indexs = self.tv_booklist.selectedIndexes()
            # 去重：通过集合提取唯一的行索引（避免选中多列时重复处理同一行）
            indexlist = set(index.row() for index in indexs)
            # ===================== 3. 提取选中行的ISBN列表（唯一标识） =====================
            isbnlist = []
            for aindex in indexlist:
                # 从表格模型中获取指定行的完整数据，提取第0列（ISBN）
                isbnlist.append(self.model.getItem(aindex)[0])
            
            # ===================== 4. 日志记录选中信息（便于调试） =====================
            LOG.info(f"选中信息  {len(isbnlist)} 项:   {isbnlist}")
                   
            # ===================== 5. 生成右键菜单并处理用户操作 =====================
            # 仅当有有效ISBN（选中行）时生成右键菜单
            if len(isbnlist) > 0:
                # 生成右键菜单（genLoveMenu为自定义方法，显示菜单并返回用户选择的动作）
                # 注：genLoveMenu内部会根据pos定位菜单，并将选择的动作赋值给self.action
                self.genLoveMenu(pos)
                
                # ===================== 6. 执行删除操作 =====================
                # 若用户选择的动作是“删除”（self.dele为删除动作对象）
                if self.action == self.dele:
                    # 遍历ISBN列表，逐个删除对应图书记录（ISBN为唯一标识）
                    for isbn in isbnlist:
                        self.model.deleteItem(isbn)
                        LOG.info(f"删除信息： {isbn}")
                    # ===================== 7. 更新状态栏（反馈删除结果） =====================
                    # 状态栏显示当前剩余记录数 + 软件版本信息
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
        核心方法：根据ISBN从豆瓣接口获取图书完整信息，刷新图书详情子窗口的内容与布局
        功能包含：
        1. 调用豆瓣API获取图书基础信息
        2. 下载图书封面图片并显示
        3. 构建富文本展示图书核心信息（作者、出版、评分等）
        4. 计算图书推荐度并展示
        5. 自适应调整详情窗口文本框高度，优化显示效果
    
        @param ISBN: 图书唯一标识ISBN13，用于调用豆瓣API获取信息
        @type ISBN: str
        """
        # ===================== 1. 调用豆瓣API获取图书完整信息 =====================
        # get_douban_isbn为已实现的方法，返回包含图书所有字段的列表（索引对应固定字段）
        douban_bookinfo = self.get_douban_isbn(ISBN)
        if not douban_bookinfo: 
            QtWidgets.QMessageBox.warning(
                self,                # 父窗口（主窗口）
                "错误",              # 提示框标题
                "获取信息有误，无法展示图书信息！",    # 提示内容
                QtWidgets.QMessageBox.StandardButton.Ok  # 确认按钮
                )
            return   
        # ===================== 2. 下载图书封面图片（处理反爬限制） =====================
        # 提取封面图片URL（douban_bookinfo[9]为封面小图URL）
        url = douban_bookinfo[9]
        # 构造Referer请求头：豆瓣图片防盗链，需指定来源域名（从封面URL提取域名）
        ref = 'https://' + url.split('/')[2]
        
        # 请求头：模拟浏览器，避免图片请求被拒绝（403 Forbidden）
        header = {
            'User-Agent':
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.79'
        }
        header['Referer'] = ref
        # 发送GET请求下载封面图片数据
        res = requests.get(douban_bookinfo[9], headers=header)
        # 将图片二进制数据转换为QImage（PyQt6可识别的图片格式）
        img = QImage.fromData(res.content)

        # self.CW_bookinfo = BookInfo.BookInfo(parent=self)
        # 将QImage转换为QPixmap，设置到详情窗口的封面标签（lb_bookcover）
        self.CW_bookinfo.lb_bookcover.setPixmap(QPixmap.fromImage(img))

        # ===================== 3. 构建富文本信息，填充到文本框（tb_bookinfo） =====================
        # 清空文本框（可选，若需保留历史可注释）
        # self.CW_bookinfo.tb_bookinfo.clear()
        
        # 标题：白色粗体大号字体（书名）
        self.CW_bookinfo.tb_bookinfo.setText(
            '<b><font color="white" size="5">' + douban_bookinfo[1] +
            '</font></b>')

        # 追加核心信息：作者、出版社、价格、出版日期、ISBN（换行+粗体标签）
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

        # 评分信息：平均分 + 评价人数（douban_bookinfo[11]为评分字典，含average/numRaters）
        self.CW_bookinfo.tb_bookinfo.append(
            '<br><b>评分: </b>' + str(douban_bookinfo[11]['average']) + '分/ ' +
            str(douban_bookinfo[11]['numRaters']) + '人')
        # 豆瓣链接：白色超链接样式（douban_bookinfo[12]为图书详情页URL）
        self.CW_bookinfo.tb_bookinfo.append(
            '<br><b>链接: &emsp;&emsp;&emsp;&emsp;&emsp; </b>[<a style="color: #FFFFFF;" href="' + douban_bookinfo[12] + '"> 豆瓣 </a>]')
        
        # ===================== 4. 计算图书推荐度（自定义公式） =====================
        # 推荐度公式：(豆瓣平均分 - 2.5) × ln(评价人数) → 兼顾评分和评价人数的综合推荐值
        # 注：2.5为基础分（过滤低分图书），ln为自然对数（放大评价人数的权重）
        
        try:
            avg_score = float(douban_bookinfo[11]['average'])  # 豆瓣平均分
            raters_count = float(douban_bookinfo[11]['numRaters'])  # 评价人数
            # 避免对数计算异常（评价人数为0时ln无意义，默认推荐度0）
            if raters_count <= 0:
                recommend_score = 0.0
            else:
                recommend_score = (avg_score - 2.5) * math.log(raters_count)
            # 四舍五入取整，追加到文本框
            self.CW_bookinfo.tb_bookinfo.append(
                '<br><b>推荐: </b>' + str(round(recommend_score))
            )
        except Exception as e:
            # 异常处理：评分/人数格式错误时显示推荐度0
            LOG.warning(f"计算推荐度失败（ISBN：{ISBN}）：{e}")
            self.CW_bookinfo.tb_bookinfo.append('<br><b>推荐: </b>0')
        
        
        
        
        # Recomm = ((float(douban_bookinfo[11]['average'])) - 2.5) * \
        #     math.log(float(douban_bookinfo[11]['numRaters']))
        # self.CW_bookinfo.tb_bookinfo.append(
        #     '<br><b>推荐: </b>' + str(round(Recomm)))

        # r = requests.get(book_dict['image'])
        # im = cv.imdecode(np.frombuffer(r.content, np.uint8), cv.IMREAD_COLOR) # 直接解码网络数据
        # cv.imshow('im', im)
        # cv.waitKey(0)
        # self.CW_bookinfo.tb_bookinfo.append('<a href="https://www.douban.com">douban</a>')

        # self.Dialog.setWindowTitle("图书信息 - " + douban_bookinfo[1])
        
        # ===================== 5. 日志记录与窗口配置 =====================
        # 日志记录：记录封面信息获取情况（字段数量+完整信息），便于调试
        LOG.info(f'获取封面信息 {len(douban_bookinfo)} 项: {douban_bookinfo}')
        # self.Dialog.setFixedSize(self.Dialog.width(), self.Dialog.height())

        # self.Dialog.show()
        # 设置详情窗口标题：“图书信息 - 书名”
        self.CW_bookinfo.setWindowTitle("图书信息 - " + douban_bookinfo[1])
        self.CW_bookinfo.show()
        
        # ===================== 6. 自适应调整文本框高度（布局适配） =====================
        # 获取文本框当前Y坐标（垂直位置）
        tb_y = self.CW_bookinfo.tb_bookinfo.pos().y()
        
        # 计算文本框所需高度：文档内容高度 + 上下内边距（margin）
        tb_height = self.CW_bookinfo.tb_bookinfo.document().size().height() + \
            self.CW_bookinfo.tb_bookinfo.contentsMargins().top() + \
            self.CW_bookinfo.tb_bookinfo.contentsMargins().bottom()
            
        # 固定文本框高度（四舍五入），避免内容溢出/空白
        self.CW_bookinfo.tb_bookinfo.setFixedHeight(round(tb_height))
        # 调整文本框垂直位置（move_y=0表示不调整，可根据需要修改）
        move_y = 0  # 311-round(tb_height) # 注释为历史调整逻辑，保留供参考
        self.CW_bookinfo.tb_bookinfo.setGeometry(self.CW_bookinfo.tb_bookinfo.pos().x(), # 保持X坐标不变
                                                 tb_y+move_y, # 调整Y坐标
                                                 self.CW_bookinfo.tb_bookinfo.width(), # 保持宽度不变
                                                 self.CW_bookinfo.tb_bookinfo.height()) # 已固定的高度

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
        槽函数：响应“豆瓣搜索”按钮点击事件，打开豆瓣图书搜索子窗口
        核心逻辑：
        1. 实例化豆瓣搜索子窗口并关联父窗口
        2. 绑定子窗口的图书信息信号到当前窗口的处理方法
        3. 自动填充主窗口的书名关键词到子窗口搜索框（关键词长度≥2时）
        4. 设置子窗口为模态（阻塞父窗口操作）并显示
        """
        # ---------------- 注释掉的旧实现（保留供参考） ----------------
        # 旧方式：手动初始化UI文件构建对话框（已替换为直接实例化BookSearch类）
        # self.Dialog = QtWidgets.QDialog()
        # self.CW_booksearch = Ui_Dialog_S()
        # self.CW_booksearch.setupUi(self.Dialog)
        # self.Dialog.setModal(True)
        # self.Dialog.setFixedSize(self.Dialog.width(), self.Dialog.height())
        # self.Dialog.show()
    
        # 1. 实例化豆瓣搜索子窗口，指定当前窗口为父窗口（用于信号传递、窗口层级管理）
        bs = BookSearch.BookSearch(self)
        # 2. 绑定子窗口的自定义信号（bookinfoSignal）到当前窗口的信号处理方法（getDialogSignal）
        #    作用：子窗口选中图书后，将图书信息传递到当前窗口的getDialogSignal方法处理
        bs.bookinfoSignal.connect(self.getDialogSignal)
        # 3. 自动填充搜索关键词：获取主窗口书名输入框的内容并去除首尾空格
        search = self.le_bookname.text().strip()
        # 仅当关键词长度≥2时填充到子窗口搜索框（避免空/过短关键词无效搜索）
        if len(search) >= 2:
            bs.le_search_douban.setText(search)
            # 4. 设置子窗口为模态窗口：
        #    - 模态窗口会阻塞父窗口的所有操作，直到子窗口关闭
        #    - 保证用户先完成搜索操作，再返回主窗口
        bs.setModal(True)
        # 5. 显示豆瓣搜索子窗口
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
