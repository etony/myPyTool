# -*- coding: utf-8 -*-

"""
Module implementing BookSearch.
"""

from PyQt6.QtCore import pyqtSlot, QUrl
from PyQt6.QtWidgets import QApplication, QDialog

from Ui_BooSearch import Ui_Dialog_S
import sys
import requests
from PyQt6.QtGui import QStandardItemModel, QStandardItem
import pandas as pd
import numpy as np

class BookSearch(QDialog, Ui_Dialog_S):
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
    def on_pb_search_douban_clicked(self):
        """
        Slot documentation goes here.
        """
        url = "https://api.douban.com/v2/book/search"
        search_str = self.le_search_douban.text()
        params = {
            'q':search_str,
            'apikey':'0ac44ae016490db2204ce0a042db2916'}
        headers = {
            "Referer":
            "https://m.douban.com/tv/american",
            "User-Agent":
            "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1"
        }

        response = requests.get(url, params=params, headers=headers)

        booklist = response.json()['books']
        books = []
        for book_dict in booklist:
            bookinfo = []
            if len(book_dict) > 5:
                author = '/'.join(book_dict['author'])
                if len(book_dict['translator']) > 0:
                    author += ' 译者: '
                    author += '/'.join(book_dict['translator'])
                rating = book_dict['rating']
                price = book_dict['price']
                price = price.replace('CNY', '').replace('元', '').strip()
                bookinfo.append(book_dict['isbn13'])
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
                books.append(bookinfo)
                
                
        # 创建表格模型和表头
        df = pd.DataFrame(np.array(books)[:,0:9])
        print(df)
        table_model = QStandardItemModel(df.shape[0], df.shape[1])
        table_model.setHorizontalHeaderLabels(['ISBN', '书名', '作者', '出版', '价格', '评分', '人数', '分类', '书柜'])
        
        # 用数据填充模型
        for i, row in df.iterrows():
            for j in range(df.shape[1]):
                table_model.setItem(i, j, QStandardItem(str(row[j])))
        
        # 绑定模型到表格视图
        self.tv_booksearch.setModel(table_model)
        
        # 显示表格视图
        self.tv_booksearch.show()                
                
                
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    dl = BookSearch()

    dl.show()
    sys.exit(app.exec())