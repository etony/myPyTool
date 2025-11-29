# -*- coding: utf-8 -*-
"""
Module: BookInfo.py
功能：实现图书信息详情对话框，支持切换ISBN列表中的图书信息，关联主窗口刷新单本图书数据
依赖：PyQt6（UI组件）、Ui_BookInfo（Qt Designer生成的UI文件）
"""

# 导入PyQt6核心模块（槽函数、对话框组件）
from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QApplication, QDialog

# 导入UI界面文件（由Qt Designer设计并转换为Python代码）
from Ui_BookInfo import Ui_Dialog

# 系统模块（用于程序入口、命令行参数处理）
import sys
# from PyQt6 import QtCore, QtWidgets  # , QtGui


class BookInfo(QDialog, Ui_Dialog):
    """
    图书信息详情对话框类
    继承关系：
    - QDialog：PyQt6的对话框基类，提供对话框的基础交互能力
    - Ui_Dialog：从UI文件生成的界面类，包含对话框的控件定义（如按钮、文本框等）
    核心功能：展示单本图书信息，支持点击“下一个”按钮切换ISBN列表中的图书，并通知主窗口刷新对应信息
    """
    def __init__(self, parent=None, isbn_list=None, indx=None):
        """
        构造函数：初始化图书信息对话框

        @param parent: 父窗口对象（通常为主程序窗口），用于关联对话框与主窗口的交互
        @type parent: QWidget | None (可选，默认None)
        @param isbn_list: 图书ISBN列表，用于切换不同图书的信息
        @type isbn_list: list | None (可选，默认None)
        @param indx: 当前显示的ISBN在列表中的索引位置
        @type indx: int | None (可选，默认None)
        """
        
        # 调用父类构造函数初始化对话框
        super().__init__(parent)
        # 初始化ISBN列表（确保为列表类型，避免None值）
        self.isbn_list = list(isbn_list) if isbn_list is not None else []
        # 初始化当前ISBN的索引
        self.indx = indx if indx is not None else 0
        # 加载UI界面（由Ui_Dialog提供的setupUi方法，初始化对话框的控件）
        self.setupUi(self)

    @pyqtSlot()
    def on_pb_next_clicked(self):
        """
        槽函数：响应“下一个”按钮（pb_next）的点击事件
        功能：切换到ISBN列表中的下一个ISBN，若到列表末尾则循环到第一个；
              通知父窗口刷新当前选中ISBN对应的图书信息
        """
        # TODO: 待完善项（可补充）：
        # 1. 切换时更新对话框内的图书信息展示（如文本框、标签等）
        # 2. 添加“上一个”按钮的逻辑，实现双向切换
        # 3. 禁用按钮（当列表为空/只有1条数据时）

        # 当前索引+1，切换到下一个ISBN
        self.indx = self.indx + 1
        # 索引越界处理：若超过列表长度，循环到第一个元素（索引0）
        if self.indx >= len(self.isbn_list):
            self.indx = 0
            
        # 获取父窗口对象（主程序窗口）    
        booklist = self.parent()
        # 调用父窗口的refreshBookInfo方法，刷新当前ISBN的图书信息
        # 注：refreshBookInfo为父窗口定义的方法，需确保父窗口实现该方法
        booklist.refreshBookInfo(self.isbn_list[self.indx])


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dl = BookInfo()

    dl.show()
    # # apply_stylesheet(app, theme='dark_blue.xml')
    # blmain = QtWidgets.QDialog()
    # li =

    # # # 浅色样式
    # # app.setStyleSheet(qdarkstyle.load_stylesheet(qdarkstyle.LightPalette))
    # # # 深色样式
    # # app.setStyleSheet(qdarkstyle.load_stylesheet(qdarkstyle.DarkPalette))

    # # app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))

    # blmain.show()
    # sys.exit(app.exec())

    # app = QApplication(sys.argv)
    # dialog = CustomDialog()

    # Dialog = QtWidgets.QDialog()
    # CW_bookinfo = Ui_Dialog()
    # CW_bookinfo.tb_bookinfo.setText('<a href="https://www.example.com">点击打开链接</a>')
    # CW_bookinfo.setupUi(Dialog)
    # Dialog.show()

    sys.exit(app.exec())
