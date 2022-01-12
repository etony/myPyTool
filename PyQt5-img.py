import sys
import os
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *


class Gadgets(QWidget):
    def __init__(self):
        super(Gadgets, self).__init__()

        self.windowinit()

    def windowinit(self):
        self.x = 100
        self.y = 80
        self.setGeometry(self.x, self.y, 700, 600)
        self.setWindowTitle('My Gadgets')
        self.lab = QLabel(self)
        self.img_path = './image/1.png'
        self.qpixmap = QPixmap(self.img_path)
        self.lab.setPixmap(self.qpixmap)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
                            | Qt.SubWindow)
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self.show()

    def mousePressEvent(self, QMouseEvent):
        if QMouseEvent.button() == Qt.LeftButton:
            self.pos_first = QMouseEvent.globalPos() - self.pos()
            QMouseEvent.accept()
            self.setCursor(QCursor(Qt.OpenHandCursor))

    def mouseMoveEvent(self, QMouseEvent):
        if Qt.LeftButton:
            self.move(QMouseEvent.globalPos() - self.pos_first)
            print(self.pos())
            self.x, self.y = self.pos().x, self.pos().y
            QMouseEvent.accept()


if __name__ == '__main__':
    # 这里我们提供必要的引用。基本控件位于pyqt5.qtwidgets模块中。
    # 每一pyqt5应用程序必须创建一个应用程序对象。sys.argv参数是一个列表，从命令行输入参数。
    app = QApplication(sys.argv)
    # QWidget部件是pyqt5所有用户界面对象的基类。他为QWidget提供默认构造函数。默认构造函数没有父类。
    pet = Gadgets()
    # 系统exit()方法确保应用程序干净的退出
    # 的exec_()方法有下划线。因为执行是一个Python关键词。因此，exec_()代替
    sys.exit(app.exec_())
