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
# from BookList import DouBanApi
from doubanapi import DouBanApi

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
        self.setFixedSize(self.width(), self.height())

    @pyqtSlot()
    def on_pb_next_clicked(self):
        """
        槽函数：响应“下一个”按钮（pb_next）的点击事件
        核心功能：
        1. 循环切换ISBN列表的索引（当前索引+1，末尾则回到第一个）
        2. 调用父窗口的刷新方法，展示当前选中ISBN的图书详情
        关键依赖：
        - self.indx: 类实例变量，记录当前选中的ISBN列表索引（初始需初始化，如self.indx=0）
        - self.isbn_list: 类实例变量，存储待切换的ISBN列表（需提前加载）
        - 父窗口需实现refreshBookInfo方法，接收ISBN参数并刷新图书信息
        """
        # TODO: 待完善优化项
        # 1. 初始化防护：isbn_list为空时禁用按钮，避免索引操作异常
        # 2. 视觉反馈：切换后高亮/标记当前ISBN，或更新按钮旁的索引提示（如“1/10”）
        # 3. 单向切换优化：若仅需单向不循环，可改为indx=min(indx+1, len(isbn_list)-1)
        # 4. 信息同步：切换后同步更新本窗口内的ISBN展示控件（如标签/输入框）

        # 步骤1：当前索引+1，准备切换到下一个ISBN
        self.indx += 1
        
        # 步骤2：边界处理（循环切换）：索引超过列表长度时，重置为第一个元素（索引0）
        # 说明：若需非循环逻辑，可注释此段，改为self.indx = len(self.isbn_list) - 1
        if self.indx >= len(self.isbn_list):
            self.indx = 0
            
        # 步骤3：获取父窗口对象（主窗口/图书列表窗口）
        # 注：parent()返回直接父对象，需确保本窗口初始化时正确设置父窗口   
        booklist = self.parent()
        
        # 步骤4：调用父窗口的刷新方法，传递当前选中的ISBN
        # refreshBookInfo：父窗口核心方法，根据ISBN从豆瓣接口拉取并展示图书详情
        booklist.refreshBookInfo(self.isbn_list[self.indx])

    @pyqtSlot()
    def on_pb_prev_clicked(self):
        """
        槽函数：响应“上一个”按钮（pb_prev）的点击事件
        核心功能：
        1. 循环切换ISBN列表的索引（当前索引-1，开头则回到最后一个）
        2. 调用父窗口的刷新方法，展示当前选中ISBN的图书详情
        关键依赖：
        - self.indx: 类实例变量，记录当前选中的ISBN列表索引（需与next按钮共用）
        - self.isbn_list: 类实例变量，存储待切换的ISBN列表（需非空）
        - 父窗口需实现refreshBookInfo方法，接收ISBN参数并刷新图书信息
        """
        # TODO: 与“下一个”按钮对齐的待完善项
        # 1. 初始化防护：isbn_list为空时禁用按钮，避免索引操作异常
        # 2. 视觉反馈：切换后更新索引提示（如“3/10”），提升用户体验
        # 3. 单向切换优化：若仅需单向不循环，可改为indx=max(indx-1, 0)
        # 4. 信息同步：切换后同步更新本窗口内的ISBN展示控件

        # 步骤1：当前索引-1，准备切换到上一个ISBN
        self.indx -= 1
        # 步骤2：边界处理（循环切换）：索引小于0时，重置为最后一个元素
        # 说明：len(self.isbn_list)-1 是列表最后一个元素的合法索引
        if self.indx < 0 :
            self.indx = len(self.isbn_list) -1
            
        # 步骤3：获取父窗口对象（主窗口/图书列表窗口）
        # 注：需确保本窗口通过setParent()或初始化时绑定了正确的父窗口   
        booklist = self.parent()
        
        # 步骤4：调用父窗口刷新方法，传递当前选中的ISBN
        # 触发父窗口从豆瓣接口拉取该ISBN的图书信息，并更新UI展示
        booklist.refreshBookInfo(self.isbn_list[self.indx])


if __name__ == "__main__":
    app = QApplication(sys.argv)
    bi = BookInfo()
    bi.show()
    sys.exit(app.exec())
