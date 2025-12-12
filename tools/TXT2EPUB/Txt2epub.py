# -*- coding: utf-8 -*-

"""
Module implementing Txt2epub.
"""
import os
import re
import sys
import datetime
from loguru import logger  # 日志库（替代原生logging，更简洁）
import chardet  # 自动检测文件编码
from opencc import OpenCC  # 繁简转换工具

from PyQt6.QtCore import pyqtSlot  # PyQt槽函数装饰器
from PyQt6.QtWidgets import QMainWindow, QDialog
from PyQt6.QtWidgets import QApplication, QFileDialog, QMessageBox
from PyQt6.QtGui import QIcon, QPixmap, QImage  # PyQt图片处理

# 自定义UI类（Qt Designer生成）
from Ui_Txt2epub import Ui_MainWindow
from Ui_Dir import Ui_Dialog

# 自定义转换类（核心业务逻辑：Txt↔Epub/Mobi转换）
from Conver2epub import Conver2epub, Conver2txt, epub2mobi

# ===================== 常量定义（抽离魔法值）=====================
MIN_REG_LENGTH = 5  # 正则表达式最小长度
DEFAULT_ENCODING = "utf-8"  # 默认编码
COVER_FORMATS = "*.jpg;;*.png;;*.jpeg;;All Files(*)"  # 支持的封面格式
ILLEGAL_CHARS = r'[\\/:*?"<>|]'  # Windows非法文件名字符
SPLIT_PATTERN = r"[(（：【]"  # 标题拆分正则
PROGRESS_TITLE = "处理中"  # 进度弹窗标题
PROGRESS_LABEL = "请稍候..."  # 进度弹窗提示


class Txt2epub(QMainWindow, Ui_MainWindow):
    """
    Txt↔Epub/Mobi 格式转换工具主窗口类
    核心功能：
    1. TXT文件转换为EPUB（支持自定义标题/作者/封面/章节正则/编码）；
    2. EPUB文件转换为TXT（支持繁简转换、编码自定义）；
    3. 提取EPUB元信息（标题/作者/日期等）并支持修改；
    4. 批量重命名EPUB文件（按元信息自动命名）；
    5. EPUB转MOBI格式；
    6. 生成EPUB章节目录预览；
    依赖组件：
    - Ui_MainWindow：主窗口UI（含输入框/按钮/状态栏/图片显示）；
    - Conver2epub/Conver2txt/epub2mobi：核心转换逻辑类；
    - chardet：自动检测TXT文件编码；
    - opencc：繁简中文转换；
    - loguru：日志记录（按日分割，含时间/级别/位置）；
    - PyQt6：GUI交互（文件选择/弹窗/状态栏/图片显示）。
    """

    def __init__(self, parent=None):
        """
        构造函数：初始化主窗口

        @param parent: 父窗口对象（默认None，主窗口无父窗口）
        @type parent: QWidget | None
        """
        # 调用父类构造函数，初始化QMainWindow和UI
        super().__init__(parent)
        self.setupUi(self)  # 加载Qt Designer生成的UI布局

        # 初始化核心变量
        self.coverpath = ''  # 存储EPUB封面图片路径
        self.dirname = ""  # 源TXT文件目录
        self.in_dirname = ""  # 源EPUB文件目录
        self.epubpath = ""  # 目标EPUB路径
        self.out_txtpath = ""  # 目标TXT路径
        self.title = ""  # 默认标题
        self.conver2txt = None  # 转换类实例缓存

        self.setFixedSize(self.width(), self.height())  # 固定窗口大小，避免布局错乱
        self.setWindowTitle("Txt↔Epub/Mobi 转换工具")
        self.setWindowIcon(QIcon('bookinfo.ico'))
        # 配置日志：按日分割，格式包含时间/级别/模块.函数/消息
        logger.add(
            '日志_{time:YYYY-MM-DD}.log',  # 日志文件名（按日期）
            rotation="1 day",  # 每日分割新日志文件
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {module}.{function} : {message}",
            retention="7 days",  # 保留7天日志
            enqueue=True  # 异步日志，避免阻塞UI
        )
        logger.info('程序加载完成.')  # 记录程序启动日志
        self.pb_epub.setDisabled(True)
        # self.lb_cover.clicked.connect(self.on_lb_cover_clicked)

    @pyqtSlot()
    @logger.catch()
    def on_pb_convert_clicked(self):
        """
        槽函数：响应「转换(TXT→EPUB)」按钮点击事件
        核心逻辑：
        1. 校验源TXT文件是否存在；
        2. 初始化转换类，设置自定义参数（标题/作者/封面/正则/编码）；
        3. 执行转换，记录日志并更新状态栏；
        4. 弹窗提示转换完成，支持打开存储目录（跨平台）；
        异常处理：loguru自动捕获并记录所有异常，避免程序崩溃。
        """
        # 提取界面输入参数（去除首尾空格，避免空字符串干扰）
        txtfile = self.le_txt.text().strip()       # 源TXT文件路径
        epubfile = self.le_epub.text().strip()     # 目标EPUB文件路径
        title = self.le_title.text().strip()       # 自定义EPUB标题
        author = self.le_author.text().strip()     # 自定义EPUB作者
        reg = self.te_reg.toPlainText().strip()    # 章节匹配正则表达式

        # 校验源文件是否存在（核心前置条件）
        if os.path.exists(txtfile):
            # 初始化TXT→EPUB转换类
            conver2 = Conver2epub(txtfile, epubfile)

            # 按需设置自定义参数（仅当输入非空时覆盖默认值）
            if len(title) > 1:
                conver2.set_title(title)
            if len(author) > 1:
                conver2.set_author(author)
            if len(self.coverpath) > 1:
                conver2.set_cover(self.coverpath)  # 设置封面
            if len(reg) > 5:
                conver2.set_reg(reg)  # 设置章节匹配正则
            if self.cb_encode.currentIndex() != 0:
                encode = self.cb_encode.currentText()
                conver2.set_encode(encode)  # 设置TXT文件编码
                logger.info(
                    f'指定文件编码: {self.cb_encode.currentIndex()}-{encode}')

            # 执行核心转换逻辑b')
            conver2.conver()
            logger.info(f'文件转换完成！   {epubfile}')
            self.statusBar.showMessage("文件转换完成！")  # 状态栏提示

            # 弹窗提示：询问是否打开存储目录
            reply = QMessageBox(QMessageBox.Icon.Information,  # 信息类弹窗
                                '信息',  # 弹窗标题
                                '转换完成,是否打开存储目录？',  # 弹窗内容
                                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.No  # 按钮
                                ).exec()

            # 按用户选择打开目录（跨平台兼容）
            if reply == QMessageBox.StandardButton.Ok:
                dirname, filename = os.path.split(epubfile)  # 拆分目录和文件名
                logger.info(f'打开存贮目录: {dirname}')
                if sys.platform == 'win32':
                    # os.system("start explorer %s" %dirname)
                    os.startfile(dirname)  # Windows打开目录
                elif sys.platform == 'linux':
                    os.system('xdg-open "%s"' % dirname)  # Linux打开目录
        else:
            # 源文件不存在时的提示
            self.statusBar.showMessage("未指定转换文件！")

    @pyqtSlot()
    def on_pb_epub_clicked(self):
        """
        槽函数：响应「选择EPUB保存路径」按钮点击事件
        核心逻辑：
        1. 校验源TXT文件是否已选择且存在；
        2. 打开文件保存对话框，限定EPUB格式；
        3. 记录选择的路径并更新输入框，日志留存；
        前置条件：必须先选择有效的源TXT文件。
        """
        # 校验源TXT文件是否有效
        # 前面是地址，后面是文件类型,得到输入地址的文件名和地址txt(*.txt*.xls);;image(*.png)不同类别

        if len(self.le_txt.text().strip()) > 5 and os.path.exists(self.le_txt.text().strip()):
            # 默认保存路径：源文件目录下的output子目录
            output = os.path.join(self.dirname, 'output')
            # 打开保存对话框（限定EPUB格式）
            epubpath, type = QFileDialog.getSaveFileName(
                self, "文件保存", output, 'epub(*.epub)')

            # 若用户选择了路径（未取消）
            if epubpath != '':
                self.le_epub.setText(epubpath)  # 更新EPUB路径输入框
                logger.info(f'指定存储路径: {epubpath}')
                # self.pb_mobi.setEnabled(True)
        else:
            # 源文件无效时的提示
            logger.info('未指定转换文件！')
            self.statusBar.showMessage('未指定转换文件！')

    @pyqtSlot()
    def on_pb_reset_clicked(self):
        """
        槽函数：响应「重置」按钮点击事件
        核心逻辑：清空所有输入框，恢复章节匹配正则为默认值，记录重置日志。
        默认正则：匹配「第/卷+数字+章/回/部/节/集/卷」开头的章节标题（如“第一章 序章”）。
        """
        self.le_author.clear()  # 清空作者输入框
        self.le_txt.clear()     # 清空TXT路径输入框
        self.le_epub.clear()    # 清空EPUB路径输入框
        # 恢复默认章节匹配正则
        self.te_reg.setPlainText(
            r"^\s*([第卷][0123456789一二三四五六七八九十零〇百千两]*[章回部节集卷].*)\s*")
        self.le_title.clear()  # 清空标题输入框
        logger.info('选项重置！')   # 记录重置操作

    @pyqtSlot()
    def on_pb_txt_clicked(self):
        """
        槽函数：响应「选择TXT源文件」按钮点击事件
        核心逻辑：
        1. 打开文件选择对话框，限定TXT格式；
        2. 自动填充EPUB路径（同目录+同文件名+.epub）；
        3. 自动填充标题/作者（默认=TXT文件名）；
        4. 自动检测TXT文件编码（chardet），更新状态栏和编码下拉框；
        5. 记录日志和状态栏提示。
        """
        # 打开文件选择对话框（限定TXT格式）
        txtpath, txtType = QFileDialog.getOpenFileName(
            self, "选择源文件", ".", "*.txt;;All Files(*)")

        if txtpath != "":
            self.le_txt.setText(txtpath)  # 更新TXT路径输入框
            self.pb_epub.setEnabled(True)

            # 拆分文件路径：目录/文件名/扩展名
            self.dirname, filename = os.path.split(txtpath)
            file_name, extension = os.path.splitext(os.path.basename(txtpath))
            # 自动生成EPUB默认路径（同目录+同文件名+.epub）
            self.epubpath = os.path.join(self.dirname, file_name) + '.epub'
            self.title = file_name.strip()  # 默认标题=文件名（去空格）

            # 自动填充EPUB路径、标题、作者输入框
            self.le_epub.setText(self.epubpath)
            self.le_title.setText(self.title)
            self.le_author.setText(self.title)
            logger.info(f'指定转换文件:{txtpath}')
            self.statusBar.showMessage(f'指定转换文件:{txtpath} ')

            # 自动检测文件编码（读取前512字节，平衡性能和准确性）
            with open(txtpath, mode='rb') as f:
                data = f.read(512)  # 读取前512字节用于编码检测
                fileinfo = chardet.detect(data)  # chardet核心检测方法
                logger.info(f'文件信息: {fileinfo}')

                # 更新状态栏（区分是否检测到语言）
                if fileinfo['language'] == '':
                    self.statusBar.showMessage(
                        f'指定转换文件:{txtpath} 编码:{chardet.detect(data)["encoding"]}')
                else:
                    self.statusBar.showMessage(
                        f'指定转换文件:{txtpath} 编码:{chardet.detect(data)["encoding"]} 语言:{chardet.detect(data)["language"]} ')
                    self.cb_encode.setCurrentIndex(1)  # 切换编码下拉框为非默认项

    @pyqtSlot()
    def on_pb_cover_clicked(self):
        """
        槽函数：响应「选择封面」按钮点击事件
        核心逻辑：
        1. 打开文件选择对话框，限定JPG格式；
        2. 加载选中的封面图片并显示在界面标签（lb_image）；
        3. 记录封面路径和日志。
        """
        self.coverpath, coverType = QFileDialog.getOpenFileName(
            self, "选择封面图片", ".", COVER_FORMATS)

        if self.coverpath != "":
            # 加载图片并显示在界面
            cover = QPixmap(self.coverpath)
            self.lb_image.setPixmap(cover)
            logger.info(f'指定封面图片:{self.coverpath}')

    @pyqtSlot()
    def on_pb_dir_clicked(self):
        """
        槽函数：响应「生成目录」按钮点击事件
        核心逻辑：
        1. 校验源TXT文件是否存在；
        2. 初始化转换类，设置正则/编码参数；
        3. 提取章节目录，显示在目录弹窗（Ui_Dialog）；
        4. 弹窗为模态（阻塞主窗口），固定大小；
        前置条件：必须先选择有效的源TXT文件。
        """
        # 初始化目录弹窗（模态）
        self.Dialog = QDialog()
        self.CW_dir = Ui_Dialog()
        self.CW_dir.setupUi(self.Dialog)
        self.Dialog.setModal(True)  # 模态弹窗：必须关闭弹窗才能操作主窗口

        # 提取源文件和正则参数
        txtfile = self.le_txt.text().strip()
        if os.path.exists(txtfile):
            epubfile = self.le_epub.text().strip()
            reg = self.te_reg.toPlainText().strip()

            # 初始化转换类，提取目录
            conver2 = Conver2epub(txtfile, epubfile)
            if len(reg) > 5:
                conver2.set_reg(reg)  # 设置章节正则
            if self.cb_encode.currentIndex() != 0:
                encode = self.cb_encode.currentText()
                conver2.set_encode(encode)
                logger.info(
                    f'指定文件编码: {self.cb_encode.currentIndex()}-{encode}')
            # 获取章节目录列表
            items = conver2.get_dir()

            # 将目录逐行添加到弹窗的文本框
            for i in items:
                self.CW_dir.tb_dir.append(i)

            # 固定弹窗大小并显示
            self.Dialog.setFixedSize(self.Dialog.width(), self.Dialog.height())
            self.Dialog.show()
            # self.statusBar.clearMessage()
            logger.info('生成章节目录！')
        else:
            # 源文件不存在时的提示
            self.statusBar.showMessage("未找到转换文件！")

    @pyqtSlot()
    def on_pb_in_epub_clicked(self):
        """
        槽函数：响应「选择EPUB源文件（EPUB→TXT）」按钮点击事件
        核心逻辑：
        1. 打开文件选择对话框，限定EPUB格式；
        2. 自动生成TXT默认路径（同目录+同文件名+.txt）；
        3. 提取EPUB元信息（标题/作者/贡献者/日期）并填充到界面；
        4. 提取EPUB封面并显示在界面标签（lb_cover）；
        5. 启用「选择TXT保存路径」按钮，记录日志和状态栏提示。
        """
        # 打开EPUB文件选择对话框
        in_epubpath, in_epubType = QFileDialog.getOpenFileName(
            self, "选择源文件", ".", "*.epub;;All Files(*)")

        if in_epubpath != "":
            self.le_in_epub.setText(in_epubpath)

            # 拆分文件路径，生成默认TXT路径
            self.in_dirname, in_filename = os.path.split(in_epubpath)
            in_file_name, in_extension = os.path.splitext(
                os.path.basename(in_epubpath))

            # if self.chb_fanjian.isChecked():
            #     cc = OpenCC('t2s')
            #     in_file_name = cc.convert(in_file_name)
            self.out_txtpath = os.path.join(
                self.in_dirname, in_file_name) + '.txt'
            self.le_out_txt.setText(self.out_txtpath)  # 填充TXT默认路径

            logger.info(f'指定转换文件:{in_epubpath}')
            self.statusBar.showMessage(f'指定转换文件:{in_epubpath}')

            # 初始化EPUB→TXT转换类，提取元信息
            conver2txt = Conver2txt(
                self.le_in_epub.text(), self.le_out_txt.text())
            book_info = conver2txt.get_info()  # 提取EPUB元信息

            # 填充元信息到界面输入框
            self.le_book_title.setText(book_info['title'])  # 标题
            self.le_book_creater.setText(book_info['creator'])  # 作者
            self.le_book_contrib.setText(book_info['contrib'])  # 贡献者

            # 格式化日期（ISO格式→人性化格式）
            date = datetime.datetime.fromisoformat(book_info['date'])

            self.le_book_date.setText(date.strftime('%Y-%m-%d %H:%M:%S'))
            self.pb_out_txt.setEnabled(True)

            # logger.info(f'cover type: {type(conver2txt.get_cover())}')
            # 提取并显示EPUB封面
            bookcover = conver2txt.get_cover()  # 获取封面二进制数据
            img = QImage.fromData(bookcover)  # 二进制数据转QImage
            cover = QPixmap.fromImage(img)  # QImage转QPixmap
            self.lb_cover.setPixmap(cover)  # 显示在界面标签
            logger.info(f'提取epub文件信息完毕: {book_info}')

    @pyqtSlot()
    def on_pb_out_txt_clicked(self):
        """
        槽函数：响应「选择TXT保存路径（EPUB→TXT）」按钮点击事件
        核心逻辑：
        1. 打开文件保存对话框，限定TXT格式；
        2. 更新TXT保存路径输入框，记录日志。
        """
        # 默认保存路径：源EPUB目录下的output子目录
        output = os.path.join(self.in_dirname, 'output')
        out_txtpath, type = QFileDialog.getSaveFileName(
            self, "文件保存", output, 'txt(*.txt)')

        if out_txtpath != '':
            self.le_out_txt.setText(out_txtpath)  # 更新TXT路径输入框
            logger.info(f'指定转换文件:{out_txtpath}')

    @pyqtSlot()
    def on_pb_out_conver_chapter_clicked(self):
        """
        槽函数：响应「转换(EPUB→TXT)」按钮点击事件(按章节导出)
        核心逻辑：
        1. 初始化EPUB→TXT转换类；
        2. 设置输出编码（若用户自定义）；
        3. 执行转换（支持繁简转换）；
        4. 记录日志和状态栏提示。
        """
        # 初始化转换类
        self.conver2txt = Conver2txt(
            self.le_in_epub.text(), self.le_out_txt.text())

        # 设置输出编码（非默认项时）
        if self.cb_out_code.currentIndex() != 0:
            encode = self.cb_out_code.currentText()
            self.conver2txt.set_code(encode)

        # 获取繁简转换开关状态
        fanjian = self.chb_fanjian.isChecked()
        # 执行按章节转换(传入繁简转换参数)
        self.conver2txt.conver_chapter(fanjian=fanjian)
        
        cur_dir= os.path.dirname(self.txtfileself.le_out_txt.text())
        logger.info(f'文件按章节转换完成！  {cur_dir}')
        self.statusBar.showMessage(f"文件按章节转换完成！  {cur_dir}")

    @pyqtSlot()
    def on_pb_out_conver_clicked(self):
        """
        槽函数：响应「转换(EPUB→TXT)」按钮点击事件
        核心逻辑：
        1. 初始化EPUB→TXT转换类；
        2. 设置输出编码（若用户自定义）；
        3. 执行转换（支持繁简转换）；
        4. 记录日志和状态栏提示。
        """
        # 初始化转换类
        self.conver2txt = Conver2txt(
            self.le_in_epub.text(), self.le_out_txt.text())

        # 设置输出编码（非默认项时）
        if self.cb_out_code.currentIndex() != 0:
            encode = self.cb_out_code.currentText()
            self.conver2txt.set_code(encode)

        # 获取繁简转换开关状态
        fanjian = self.chb_fanjian.isChecked()
        # 执行转换（传入繁简转换参数）
        self.conver2txt.conver(fanjian=fanjian)

        logger.info(f'文件转换完成！  {self.le_out_txt.text()}')
        self.statusBar.showMessage(f"文件转换完成！  {self.le_out_txt.text()}")

    @pyqtSlot()
    def on_pb_out_reset_clicked(self):
        """
        槽函数：响应「重置(EPUB→TXT)」按钮点击事件
        核心逻辑：清空所有EPUB→TXT相关输入框，禁用「选择TXT保存路径」按钮，记录日志。
        """
        self.le_book_contrib.clear()   # 清空贡献者
        self.le_book_creater.clear()   # 清空作者
        self.le_book_date.clear()      # 清空日期
        self.le_book_title.clear()     # 清空标题
        self.le_in_epub.clear()        # 清空EPUB路径
        self.le_out_txt.clear()        # 清空TXT路径
        self.pb_out_txt.setEnabled(False)  # 禁用「选择TXT保存路径」按钮
        logger.info('选项重置！')

    @pyqtSlot()
    def on_chb_fanjian_clicked(self):
        """
        槽函数：响应「繁简转换」复选框点击事件
        核心逻辑：
        1. 若勾选繁简转换且已选择EPUB文件；
        2. 将文件名从繁体转为简体（opencc）；
        3. 更新TXT默认保存路径。
        """
        in_epubpath = self.le_in_epub.text()
        self.in_dirname, in_filename = os.path.split(in_epubpath)
        in_file_name, in_extension = os.path.splitext(
            os.path.basename(in_epubpath))

        # 勾选状态且文件名有效时，执行繁简转换
        if self.chb_fanjian.isChecked() and (in_file_name != '') and (in_file_name is not None):
            cc = OpenCC('t2s')  # 初始化繁简转换（t2s=繁体→简体）
            in_file_name = cc.convert(in_file_name)  # 转换文件名

            # 生成新的TXT路径（简体文件名）
            self.out_txtpath = os.path.join(
                self.in_dirname, in_file_name) + '.txt'
            self.le_out_txt.setText(self.out_txtpath)  # 更新路径输入框

    @pyqtSlot()
    def on_pb_out_modi_clicked(self):
        """
        槽函数：响应「修改EPUB元信息」按钮点击事件
        核心逻辑：
        1. 收集界面输入的新元信息（标题/作者/贡献者/日期）；
        2. 调用转换类的修改方法；
        3. 记录日志和状态栏提示。
        """
        # 初始化转换类
        self.conver2txt = Conver2txt(
            self.le_in_epub.text(), self.le_out_txt.text())
        # 收集新的元信息
        bookinfo = {}
        bookinfo['title'] = self.le_book_title.text()      # 新标题
        bookinfo['creator'] = self.le_book_creater.text()  # 新作者
        bookinfo['contrib'] = self.le_book_contrib.text()  # 新贡献者
        bookinfo['date'] = self.le_book_date.text()        # 新日期
        bookinfo['filename'] = self.le_in_epub.text()      # EPUB文件路径

        logger.info(f'文件信息：  {bookinfo}')
        self.conver2txt.modi(bookinfo)  # 执行元信息修改

        logger.info(f'文件修改完成！  {self.le_out_txt.text()}')
        self.statusBar.showMessage(f"文件修改完成！  {self.le_out_txt.text()}")

    @pyqtSlot()
    def on_pb_bat_rename_clicked(self):
        """
        槽函数：响应「批量重命名EPUB」按钮点击事件
        核心逻辑：
        1. 选择目标目录，遍历所有EPUB文件；
        2. 提取每个EPUB的标题/作者元信息；
        3. 按「标题_作者.epub」格式重命名（正则拆分标题前缀）；
        4. 异常处理：重命名失败时记录日志，跳过该文件；
        5. 记录总处理数和状态栏提示。
        """
        # 选择目标目录
        dir_path = QFileDialog.getExistingDirectory(
            None, "选择epub文件目录", ".")
        epubfile = []  # 存储遍历到的EPUB文件

        # 遍历目录（含子目录）下的所有文件
        for root, dirs, files in os.walk(dir_path):
            for file in files:
                old_file_name = os.path.join(root, file)  # 原文件完整路径
                # f_old_file_name = os.path.join(root, 'F_'+file)
                file_name, file_extension = os.path.splitext(
                    os.path.basename(file))

                # 仅处理EPUB文件
                if file_extension == '.epub':
                    epubfile.append(file)
                    try:
                        # 提取EPUB元信息
                        conver2txt = Conver2txt(
                            os.path.join(root, file), self.le_out_txt.text())
                        book_info = conver2txt.get_info()

                        # 正则拆分标题（取「(（：【」前的前缀
                        filename = re.split(r"[(（：【]", book_info['title'], maxsplit=1, flags=0)[
                            0] + '_' + book_info['creator']
                        # 生成新文件名
                        new_file_name = os.path.join(
                            root, filename + file_extension)
                        # 执行重命名
                        os.rename(old_file_name, new_file_name)
                    except:
                        # os.rename(old_file_name, f_old_file_name)
                        # 重命名失败时记录日志，跳过该文件
                        logger.info(f'重命名失败: {file}')
                        pass
        # 记录批量重命名结果
        logger.info(f'批量重命名完成: {dir_path} - {len(epubfile)} 个文件')
        self.statusBar.showMessage(f"批量重命名完成: {dir_path} 个文件")

    @pyqtSlot()
    def on_lb_image_clicked(self):
        """
        槽函数：响应「封面图片标签」点击事件（备用封面选择入口）
        逻辑与on_pb_cover_clicked完全一致，提供便捷操作。
        """
        self.coverpath, coverType = QFileDialog.getOpenFileName(
            self, "选择封面图片", ".", COVER_FORMATS)

        if self.coverpath != "":
            cover = QPixmap(self.coverpath)
            self.lb_image.setPixmap(cover)
            logger.info(f'指定封面图片:{self.coverpath}')

    @pyqtSlot()
    def on_pb_mobi_clicked(self):
        """
        槽函数：响应「EPUB→MOBI」按钮点击事件
        核心逻辑：
        1. 从EPUB路径生成MOBI路径（替换扩展名）；
        2. 初始化转换类，执行EPUB→MOBI转换。
        """
        epubfile = self.le_epub.text().strip()  # 获取EPUB路径
        mobifile = epubfile.rsplit('.', 1)[0]+".mobi"  # 生成MOBI路径（替换扩展名）
        e2mobi = epub2mobi(epubfile, mobifile)  # 初始化转换类
        e2mobi.e2mobi()  # 执行转换


if __name__ == "__main__":
    """
    程序入口：初始化PyQt应用，创建主窗口，启动事件循环。
    """
    app = QApplication(sys.argv)  # 初始化PyQt应用
    txt2epub = Txt2epub()         # 创建主窗口实例
    txt2epub.show()               # 显示主窗口
    sys.exit(app.exec())          # 启动事件循环，退出时返回状态码
