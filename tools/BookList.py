# -*- coding: utf-8 -*-

"""
Module implementing BLmainWindow.
"""

from PyQt6.QtCore import pyqtSlot, Qt
from PyQt6.QtWidgets import QMainWindow, QApplication, QFileDialog

from Ui_BookList import Ui_mainWindow
from PyQt6 import QtGui,  QtCore

import pandas as pd


class TableModel(QtCore.QAbstractTableModel):

    def __init__(self, data):
        super(TableModel, self).__init__()
        self._data = data

    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole:
            value = self._data.iloc[index.row(), index.column()]
            return str(value)

    def rowCount(self, index):
        return self._data.shape[0]

    def columnCount(self, index):
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
        raise NotImplementedError


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)

    blmain = BLmainWindow()
    blmain.show()
    sys.exit(app.exec())
