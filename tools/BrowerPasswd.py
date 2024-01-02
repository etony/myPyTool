# -*- coding: utf-8 -*-

"""
Module implementing BrowerPasswd.
"""

from PyQt6.QtCore import pyqtSlot, QModelIndex, QUrl
from PyQt6.QtWidgets import QMainWindow, QApplication, QHeaderView, QAbstractItemView, QFileDialog, QMessageBox
from PyQt6 import QtGui

from Ui_BrowerPasswd import Ui_MainWindow

from bpassword import Bpassword
from getfirefox import FireFoxPasswd
import pandas as pd
import os


class BrowerPasswd(QMainWindow, Ui_MainWindow):
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
        self.pb_export.setEnabled(False)
        self.pb_search.setEnabled(False)
        self.pb_reset.setEnabled(False)
        self.statusbar.showMessage("就绪")

        self.model = QtGui.QStandardItemModel()
        self.model.setHorizontalHeaderLabels(
            ['用户名', '密码', '网址', '创建时间', '最后使用'])
        #self.model = TableModel(bps.get_password())
        self.tv_namepasswd.setModel(self.model)
        # self.tv_namepasswd.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch) #Stretch
        self.tv_namepasswd.setColumnWidth(0, 145)
        self.tv_namepasswd.setColumnWidth(1, 145)
        self.tv_namepasswd.setColumnWidth(2, 290)
        self.tv_namepasswd.setColumnWidth(3, 130)
        self.tv_namepasswd.setColumnWidth(4, 130)
        self.tv_namepasswd.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Interactive)  # Stretch

        self.tv_namepasswd.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)

        # 设置表格样式
        font = self.tv_namepasswd.horizontalHeader().font()  # 获取当前表头的字体
        font.setFamily("微软雅黑")  # 修改字体设置
        self.tv_namepasswd.horizontalHeader().setFont(font)  # 重新设置表头的字体
        # 设置表头不可被点击
        self.tv_namepasswd.horizontalHeader().setSectionsClickable(False)
        self.tv_namepasswd.verticalHeader().setSectionsClickable(False)
        self.tv_namepasswd.horizontalHeader().setStyleSheet(
            "QHeaderView::section{background:#E6E6E6;}")
        self.tv_namepasswd.verticalHeader().setStyleSheet(
            "QHeaderView::section{background:#E6E6E6;}")
        self.tv_namepasswd.setStyleSheet(
            "selection-background-color:#E6E6E6;selection-color:black")
        # https://blog.csdn.net/qq_42250189/article/details/105199339
        self.le_askpass.setVisible(False)

    @pyqtSlot()
    def on_pb_getit_clicked(self):
        """
        Slot documentation goes here.
        """

        self.br = self.cb_brower.currentText().strip('-').strip()

        self.passwds = []
        if self.br == 'Firefox':
            askpass = self.le_askpass.text().strip()
            fps = FireFoxPasswd()
            self.passwds = fps.get_firefox_passwd(askpass)
        else:
            bps = Bpassword()
            # TODO: not implemented yet

            self.passwds = bps.get_password(self.br)

        # if len(self.passwds) == 0:
        #     self.pb_export.setEnabled(False)
        #     self.pb_search.setEnabled(False)
        #     self.pb_reset.setEnabled(False)
        #     return
        self.model.removeRows(0, self.model.rowCount())
        i = 0
        for passwd in self.passwds:
            passw = map(lambda x: QtGui.QStandardItem(x), passwd)
            self.model.insertRow(i, passw)
            i += 1

        if i == 0:
            self.pb_export.setEnabled(False)
            self.pb_search.setEnabled(False)
            self.pb_reset.setEnabled(False)
        else:
            self.pb_export.setEnabled(True)
            self.pb_search.setEnabled(True)
            self.pb_reset.setEnabled(True)

        self.statusbar.showMessage("保存密码:  " + str(i))

        self.tv_namepasswd.resizeColumnsToContents()  # 根据内容自动调整列宽

        # 控制列宽
        if self.tv_namepasswd.columnWidth(2) > 300:
            self.tv_namepasswd.setColumnWidth(2, 280)
        if self.tv_namepasswd.columnWidth(0) > 145:
            self.tv_namepasswd.setColumnWidth(0, 145)
        if self.tv_namepasswd.columnWidth(1) > 130:
            self.tv_namepasswd.setColumnWidth(1, 130)
        self.tv_namepasswd.setColumnWidth(2, 822 - (self.tv_namepasswd.columnWidth(0) + self.tv_namepasswd.columnWidth(
            1) + self.tv_namepasswd.columnWidth(3) + self.tv_namepasswd.columnWidth(4)))

    @pyqtSlot()
    def on_pb_export_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet

        df = pd.DataFrame(self.passwds, columns=[
                          '用户名', '密码', '网址', '创建时间', '更新时间'], dtype=str)

        fpath, ftype = QFileDialog.getSaveFileName(
            self, "保存", os.path.join(os.getcwd(), "brower_password_"+self.br+".csv"), "*.csv")

        if ftype:
            df.to_csv(fpath)
            QMessageBox(QMessageBox.Icon.Information, '信息', '导出成功！',
                        QMessageBox.StandardButton.Ok).exec()
            # reply.setText("保存成功！")
            # reply.setStandardButtons(QMessageBox.StandardButton.Ok)
            # reply.exec()

    @pyqtSlot()
    def on_pb_search_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        search = self.le_search.text().strip()

        if len(search) >= 2:
            self.passwds = list(filter(lambda x: (search in x[0]) or (
                search in x[1]) or (search in x[2]), self.passwds))
            self.model.removeRows(0, self.model.rowCount())
            i = 0
            for passwd in self.passwds:
                passw = map(lambda x: QtGui.QStandardItem(x), passwd)
                self.model.insertRow(i, passw)
                i += 1
            if i == 0:
                self.pb_export.setEnabled(False)

            self.statusbar.showMessage("记录: " + str(i))

    @pyqtSlot()
    def on_pb_reset_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        self.le_search.clear()
        self.pb_export.setEnabled(False)
        self.pb_search.setEnabled(False)
        self.pb_reset.setEnabled(False)
        self.model.removeRows(0, self.model.rowCount())
        self.statusbar.showMessage("就绪")

    @pyqtSlot(QModelIndex)
    def on_tv_namepasswd_doubleClicked(self, index):
        """
        Slot documentation goes here.

        @param index DESCRIPTION
        @type QModelIndex
        """
        # TODO: not implemented yet

        clipboard = QApplication.clipboard()  # 创建剪切板对象
        clipboard.setText(
            self.tv_namepasswd.currentIndex().data())  # 用于向剪切板写入文本

        if self.tv_namepasswd.currentIndex().column() == 2:
            QtGui.QDesktopServices.openUrl(
                QUrl(str(self.tv_namepasswd.currentIndex().data())))

        #self.statusbar.showMessage(str(self.tv_namepasswd.currentIndex().column()) + str(self.tv_namepasswd.currentIndex().data()) )

    @pyqtSlot(int)
    def on_cb_brower_currentIndexChanged(self, index):
        """
        Slot documentation goes here.

        @param index DESCRIPTION
        @type int
        """
        # TODO: not implemented yet
        self.br = self.cb_brower.currentText().strip('-').strip()
        if self.br == 'Firefox':
            self.le_askpass.setVisible(True)
        else:
            self.le_askpass.setVisible(False)


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)

    browerPasswd = BrowerPasswd()
    browerPasswd.show()
    sys.exit(app.exec())
