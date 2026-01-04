# -*- coding: utf-8 -*-

"""
Module: BookSearch.py
功能：实现豆瓣图书搜索对话框，支持关键词搜索豆瓣图书API、展示搜索结果表格、双击选中图书并发送信息到父窗口
依赖：
    - PyQt6（UI组件、信号槽、表格模型）
    - requests（HTTP请求调用豆瓣API）
    - pandas/numpy（数据处理）
"""

# PyQt6核心模块：槽函数装饰器、模型索引、自定义信号

from PyQt6.QtCore import pyqtSlot, QModelIndex, pyqtSignal
# PyQt6UI组件：应用程序、对话框
from PyQt6.QtWidgets import QApplication, QDialog, QMessageBox

# 导入UI界面文件（由Qt Designer生成，定义搜索对话框的控件）
from Ui_BooSearch import Ui_Dialog
# 系统模块：程序入口、命令行参数
import sys
# HTTP请求模块：调用豆瓣API
import requests
# PyQt6表格模型：标准项模型（用于构建搜索结果表格）
from PyQt6.QtGui import QStandardItemModel, QStandardItem
# 数据处理模块：DataFrame、数组操作
import pandas as pd
import numpy as np
from doubanapi import DouBanApi


class BookSearch(QDialog, Ui_Dialog):
    """
    豆瓣图书搜索对话框类
    继承关系：
    - QDialog：PyQt6对话框基类，提供对话框基础交互
    - Ui_Dialog_S：UI文件生成的界面类，包含搜索框、按钮、表格视图等控件
    核心功能：
    1. 调用豆瓣图书搜索API，根据关键词获取图书列表
    2. 清洗、整理图书数据并展示在表格中
    3. 双击表格行触发自定义信号，将选中图书信息传递给父窗口
    """
    # 定义自定义信号：用于向父窗口传递选中的图书信息（参数为列表类型）
    # 信号触发时机：双击表格中的图书行时
    bookinfoSignal = pyqtSignal(list) #创建自定义信号，在不同的页面或组件之间传递信息和信号。

    def __init__(self, parent=None):
        """
        构造函数：初始化图书搜索对话框

        @param parent: 父窗口对象（通常为主程序窗口），用于关联对话框与父窗口的信号交互
        @type parent: QWidget | None (可选，默认None)
        """
        # 调用父类构造函数初始化对话框
        super().__init__(parent)
        # 加载UI界面（初始化对话框的控件：搜索框、按钮、表格视图等）
        self.setupUi(self)
        self.setFixedSize(self.width(), self.height())

    @pyqtSlot()
    def on_pb_search_douban_clicked(self):
        """
        槽函数：响应“豆瓣搜索”按钮（pb_search_douban）的点击事件
        核心逻辑：
        1. 获取搜索框中的关键词
        2. 调用豆瓣图书搜索API，传递关键词和请求头（模拟移动端避免反爬）
        3. 清洗、整理API返回的图书数据（补全作者/译者、处理价格、过滤无效ISBN）
        4. 将整理后的数据填充到表格模型，绑定到表格视图展示
        """
        # 豆瓣图书搜索API地址（公开接口）
        url = "https://api.douban.com/v2/book/search"
        # 获取搜索框中用户输入的关键词
        search_str = self.le_search_douban.text().strip()
        douban_api = DouBanApi()
        
        # 跳过空关键词搜索
        if not search_str:
            QMessageBox.warning(
                self,                # 父窗口（主窗口）
                "警告",              # 提示框标题
                "搜索关键字不能为空！",    # 提示内容
                QMessageBox.StandardButton.Ok  # 确认按钮
            )  
            
            return
        # API请求参数：q=搜索关键词，apikey=豆瓣开放平台密钥（示例密钥，建议替换为自己的）
        self.search_result = douban_api.search_bookinfo_by_name(search_str.strip())
        
        # params = {
        #     'q': search_str,
        #     'apikey': '0ac44ae016490db2204ce0a042db2916'}
        
        # # 请求头：模拟iPhone移动端浏览器，避免豆瓣API反爬限制
        # headers = {
        #     "Referer":
        #     "https://m.douban.com/tv/american", # 来源页，模拟正常访问
        #     "User-Agent":
        #     "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1"
        # }
            
        # # 发送GET请求调用豆瓣API
        # response = requests.get(url, params=params, headers=headers)
        
        # # 解析API返回的JSON数据，提取图书列表
        # booklist = response.json()['books']
        # # 初始化清洗后的图书信息列表（存储最终要展示/传递的数据）
        # self.books = []
        # # 遍历每本图书，清洗和整理数据
        # for book_dict in booklist:
        #     # 单本图书的信息列表（按字段顺序整理）
        #     bookinfo = []
        #     # 过滤无效数据（字段过少的图书）
        #     if len(book_dict) > 5:
        #         # print('==='*30)
        #         # print(book_dict)
        #         # 过滤无ISBN13的图书（ISBN13是唯一标识，必须存在）
        #         if ('isbn13' not in book_dict):
        #             continue
        #         # 1. 处理作者+译者：作者用/分隔，有译者则追加“译者:XXX”
        #         author = '/'.join(book_dict['author'])  # 作者列表转字符串
        #         if len(book_dict['translator']) > 0:
        #             author += ' 译者: '
        #             author += '/'.join(book_dict['translator'])  # 存在译者时
        #          # 2. 处理评分、价格等字段
        #         rating = book_dict['rating']  # 评分信息（包含平均分、评价人数）
        #         price = book_dict['price'] # 价格（可能为空）
        #         # 清洗价格：移除CNY/元符号，去除首尾空格
        #         price = price.replace('CNY', '').replace('元', '').strip()
        #         # 3. 按顺序填充核心字段（与表格列对应）
        #         bookinfo.append(book_dict['isbn13'])          # 0: ISBN13
        #         bookinfo.append(book_dict['title'])           # 1: 书名
        #         bookinfo.append(author)                       # 2: 作者+译者
        #         bookinfo.append(book_dict['publisher'])       # 3: 出版社
        #         bookinfo.append(price)                        # 4: 价格（清洗后）
        #         bookinfo.append(rating['average'])            # 5: 豆瓣平均分
        #         bookinfo.append(rating['numRaters'])          # 6: 评价人数
        #         bookinfo.append('计划')                       # 7: 分类（默认“计划”）
        #         bookinfo.append('未设置')                     # 8: 书柜位置（默认“未设置”）
        #         # 补充扩展字段（不展示在表格，但用于传递给父窗口）
        #         bookinfo.append(book_dict['images']['small']) # 9: 图书封面小图URL
        #         bookinfo.append(book_dict['pubdate'])         # 10: 出版日期
        #         bookinfo.append(book_dict['rating'])          # 11: 完整评分信息
        #         bookinfo.append(book_dict['alt'])             # 12: 豆瓣图书详情页URL

        #         # 将单本图书信息加入总列表
        #         self.books.append(bookinfo)

        # # ========== 构建搜索结果表格 ==========
        # # 1. 提取前9个核心字段（对应表格列），转换为DataFrame（方便批量处理）
        # # np.array(self.books)[:, 0:9]：取所有行的0-8列（前9个字段）
        # df = pd.DataFrame(np.array(self.books)[:, 0:9])
        
        df = pd.DataFrame(np.array(self.search_result)[:, 0:9])
        # 2. 创建标准项表格模型（行数=DataFrame行数，列数=DataFrame列数）
        self.table_model = QStandardItemModel(df.shape[0], df.shape[1])
        # 3. 设置表格表头（与核心字段对应）
        self.table_model.setHorizontalHeaderLabels(
            ['ISBN', '书名', '作者', '出版', '价格', '评分', '人数', '分类', '书柜'])

        # 4. 遍历DataFrame，将数据填充到表格模型
        for i, row in df.iterrows():
            for j in range(df.shape[1]):
                self.table_model.setItem(i, j, QStandardItem(str(row[j])))

         # 5. 将表格模型绑定到表格视图控件，展示数据
        self.tv_booksearch.setModel(self.table_model)

         # 强制刷新表格视图（确保数据显示）
        self.tv_booksearch.show()

    @pyqtSlot(QModelIndex)
    def on_tv_booksearch_doubleClicked(self, index):
        """
        槽函数：响应搜索结果表格（tv_booksearch）的双击事件
        核心逻辑：获取双击行的图书信息，发射自定义信号传递给父窗口，关闭对话框

        @param index: 双击位置的模型索引（包含行/列信息）
        @type index: QModelIndex
        """
        # 获取双击行的索引，提取对应的图书信息
        bookinfo = self.search_result[index.row()]
        # 调试用：打印选中的图书信息（可删除）
        print("选中的图书信息：", bookinfo)
        # 发射自定义信号，将图书信息传递给父窗口
        self.bookinfoSignal.emit(bookinfo)
        # 关闭搜索对话框
        self.close()

    # def show(self):
    #     app = QApplication(sys.argv)
    #     dl = BookSearch()

    #     dl.show()
    #     sys.exit(app.exec())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dl = BookSearch()

    dl.show()
    sys.exit(app.exec())
