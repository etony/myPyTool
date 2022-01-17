# -*- coding: utf-8 -*-
"""
Created on Fri Jan 14 14:11:22 2022

@author: admin
"""

import sys
from PyQt5.QtWidgets import (QWidget, QToolTip, QLineEdit, QLabel,
                             QPushButton, QApplication)
from PyQt5.QtGui import QFont,QCursor
from PyQt5 import QtCore


class Example(QWidget):

    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        self.setWindowTitle("加法计算")
        self.setGeometry(100, 100, 500, 103)

        font = QFont()
        font.setFamily("Arial")
        font.setPointSize(18)

        self.pushButton = QPushButton("=", self)
        self.pushButton.resize(50, 20)
        self.pushButton.move(294, 40)
        self.pushButton.setFont(font)
                      
        self.pushButton2 = QPushButton("重置", self)
        self.pushButton2.resize(50, 20)
        self.pushButton2.move(360, 70)
        
        self.pushButton3 = QPushButton("退出", self)
        self.pushButton3.resize(50, 20)
        self.pushButton3.move(425, 70)
        
        self.lineEdit = QLineEdit("0", self)
        self.lineEdit.resize(113, 20)
        self.lineEdit.move(20, 40)

        self.lineEdit_2 = QLineEdit("0", self)
        self.lineEdit_2.resize(113, 20)
        self.lineEdit_2.move(170, 40)

        self.lineEdit_3 = QLineEdit(self)
        self.lineEdit_3.resize(113, 20)
        self.lineEdit_3.move(360, 40)

        self.label = QLabel("+", self)
        self.label.resize(21, 21)
        self.label.setFont(font)
        self.label.move(144, 40)
        
        # self.label = QLabel("-", self)
        # self.label.resize(21, 21)
        # self.label.setFont(font)
        # self.label.move(144, 10)

        # self.label = QLabel("*", self)
        # self.label.resize(21, 21)
        # self.label.setFont(font)
        # self.label.move(144, 70)

        # self.label = QLabel("/", self)
        # self.label.resize(21, 21)
        # self.label.setFont(font)
        # self.label.move(144, 100)        

        QtCore.QMetaObject.connectSlotsByName(self)
        self.pushButton.clicked.connect(self.click_success)
        self.pushButton2.clicked.connect(self.click_reset)
        self.pushButton3.clicked.connect(self.quit)
        
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.SubWindow)
        self.setAutoFillBackground(False)
        
        self.show()

    def click_success(self):
        A = self.lineEdit.text()
        B = self.lineEdit_2.text()
        if len(A) <= 0 or not(A.isdigit()):
            self.lineEdit.setText("0")
            A = 0
        if len(B) <= 0 or not(B.isdigit()):
            self.lineEdit_2.setText("0")
            B = 0
        self.lineEdit_3.setText(str(int(A)+int(B)))

    def click_reset(self):
        self.lineEdit.setText("")
        self.lineEdit_2.setText("")
        self.lineEdit_3.setText("")

    def mousePressEvent(self, QMouseEvent):
        if QMouseEvent.button() == QtCore.Qt.LeftButton:
            self.pos_first = QMouseEvent.globalPos() - self.pos()
            QMouseEvent.accept()
            self.setCursor(QCursor(QtCore.Qt.OpenHandCursor))

    def mouseMoveEvent(self, QMouseEvent):
        if QtCore.Qt.LeftButton:
            self.move(QMouseEvent.globalPos() - self.pos_first)
            print(self.pos())
            self.x, self.y = self.pos().x, self.pos().y
            QMouseEvent.accept()
    def quit(self):
        self.close()
        sys.exit()


if __name__ == '__main__':

    app = QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())
