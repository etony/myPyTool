# -*- coding: utf-8 -*-

"""
Module implementing BLmainWindow.
"""

from PyQt6.QtCore import pyqtSlot, Qt
from PyQt6.QtWidgets import QMainWindow, QApplication, QFileDialog

from Ui_BookList import Ui_mainWindow
from PyQt6 import QtGui,  QtCore, QtWidgets

import pandas as pd

import numpy as np
import cv2 as cv
import pyzbar.pyzbar as pyzbar

import requests
import json

class TableModel(QtCore.QAbstractTableModel):

    def __init__(self, data):
        super(TableModel, self).__init__()
        self._data = data

    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole:
            value = self._data.iloc[index.row(), index.column()]
            return str(value)

    def rowCount(self, parent=None):#index):
        return self._data.shape[0]
    
    def appendRow(self, arowdata):
        self.beginResetModel()
        self._data.loc[self._data.shape[0]]=arowdata
        self.endResetModel()

    def updateData(self, data):

        self.beginResetModel()
        self._data = data
        self.endResetModel()        
        
    def columnCount(self, parent=None):#index):
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
        data = {'ISBN':[], '书名':[], '作者':[], '出版社':[], '价格':[], '分类':[], '书柜':[]}
        
        df = pd.DataFrame(data=data)
        
        self.model = TableModel(df)
        self.tv_booklist.setModel(self.model)
        # self.model = QtGui.QStandardItemModel()
        # self.model.setHorizontalHeaderLabels(
        #     ['ISBN', '书名', '作者', '出版社', '价格', '分类', '书柜']) 

        # self.tv_booklist.setModel(self.model)
        self.tv_booklist.setSortingEnabled(True)
        
     

    @pyqtSlot()
    def on_pb_load_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        csvNamepath, csvType = QFileDialog.getOpenFileName(
            self, "选择存储文件", "E:\\minipan\\Seafile\\资料", "*.csv;;All Files(*)")

        if csvNamepath != "":
            df = pd.read_csv(csvNamepath)
 
            self.model = TableModel(df)
  

            self.tv_booklist.setModel(self.model)
            #self.table.setModel(self.model)
             


    @pyqtSlot()
    def on_pb_save_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        isbn = self.le_isbn_pic.text()
        bookinfo = self.get_douban_isbn(isbn)
        self.model.appendRow(bookinfo) 
        
        print(bookinfo)

    @pyqtSlot()
    def on_pb_scan_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        picNamepath, picType = QFileDialog.getOpenFileName(
            self, "选择条形码图片", "E:\\minipan\\Seafile\\资料", "*.png;;*.jpg;;All Files(*)")

        if picNamepath != "":
            #image = cv.imread(img_path)
            image = cv.imdecode(np.fromfile(picNamepath,dtype=np.uint8), cv.IMREAD_COLOR)
            
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

            #self.model.insertRow(self.model.rowCount(),data)

            #self.tv_booklist.setModel(self.model)



    def get_douban_isbn(self,isbn):
        bookinfo = []
        url = "https://api.douban.com/v2/book/isbn/" + isbn

        payload = {'apikey':'0ab215a8b1977939201640fa14c66bab'}  #apikey=0df993c66c0c636e29ecbb5344252a4a'} #apikey=0ac44ae016490db2204ce0a042db2916
        headers = {"Referer": "https://m.douban.com/tv/american",
                   "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1"}

        #{"content-type": "multipart/form-data;","User-Agent": "MicroMessenger/","Referer": "https://servicewechat.com/wx2f9b06c1de1ccfca/91/page-frame.html"}

        response = requests.post(url, data=payload, headers=headers)

        book_dict = json.loads(response.text)
        
        author = '作者: ' + '/'.join(book_dict['author'])
        if len(book_dict['translator'])>0:
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



if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)

    blmain = BLmainWindow()
    blmain.show()
    sys.exit(app.exec())
