# -*- coding: utf-8 -*-

"""
Module implementing BLmainWindow.
"""

from PyQt6.QtCore import pyqtSlot, Qt
from PyQt6.QtWidgets import QMainWindow, QApplication, QFileDialog

from Ui_BookList import Ui_mainWindow
from PyQt6 import QtGui,  QtCore

import pandas as pd



from PIL import Image

import numpy as np

import cv2 as cv

import pyzbar.pyzbar as pyzbar



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
    
    def appendRow(self, x):
        print(self._data.shape[0])
        self._data.loc[self._data.shape[0]]=x
        print(self._data.shape[0])
        return self._data
        
    def columnCount(self, parent=None):#index):
        return self._data.shape[1]

    def headerData(self, section, orientation, role):
        # section is the index of the column/row.
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return str(self._data.columns[section])

            if orientation == Qt.Orientation.Vertical:
                return str(self._data.index[section])

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
        
        self.model = QtGui.QStandardItemModel()
        self.model.setHorizontalHeaderLabels(
            ['ISBN', '书名', '作者', '出版社', '价格', '分类', '书柜']) 

        self.tv_booklist.setModel(self.model)

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
        raise NotImplementedError

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
            
            data =['xxxxxx', '西线无战事', '作者: [德] 雷马克 翻译:朱雯', '上海人民出版社', '45.00', '计划', '未设置']

            dd = map(lambda x: QtGui.QStandardItem(x), data)
            
            self.model.appendRow(data)
            self.tv_booklist.setModel(self.model)
            #self.model.insertRow(self.model.rowCount(),data)

            #self.tv_booklist.setModel(self.model)



if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)

    blmain = BLmainWindow()
    blmain.show()
    sys.exit(app.exec())
