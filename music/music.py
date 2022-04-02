# -*- coding: utf-8 -*-

"""
Module implementing Music.
"""

from PyQt6.QtCore import pyqtSlot, QModelIndex, QTimer, QPoint, Qt
from PyQt6.QtWidgets import QDialog, QApplication, QFileDialog
from Ui_music import Ui_Dialog
import pygame
from mutagen import mp3
from PyQt6 import QtCore, QtGui, QtWidgets


class Music(QDialog, Ui_Dialog):
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
        self.line = 1
        pygame.mixer.init()
        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.start()
        self.timer.timeout.connect(self.timer_music)
        self.musiclength = 1
        self.flag = 0
        self.paused = False
        self.label.setText('')
        self.lb_time.setText('')
        self.listWidget.setContextMenuPolicy(
            QtCore.Qt.ContextMenuPolicy.CustomContextMenu)

    def timer_music(self):
        # self.label.setText(str(self.musiclength))

        if self.musiclength > 1:
            cu = pygame.mixer.music.get_pos()
            if cu > 0:
                self.horizontalSlider.setValue(
                    int((cu/self.musiclength)/10) + self.flag+1)
                self.horizontalSlider.setEnabled(True)
            else:
                self.horizontalSlider.setEnabled(False)
            #print(pygame.mixer.music.get_pos()/1000, self.musiclength)

            self.lb_time.setText(str(int(self.horizontalSlider.value(
            )*self.musiclength/100))+':'+str(int(self.musiclength)))

    @pyqtSlot(int)
    def on_horizontalSlider_sliderMoved(self, position):
        """
        Slot documentation goes here.

        @param position DESCRIPTION
        @type int
        """
        # TODO: not implemented yet
        # self.label.setText(str(self.horizontalSlider.value()))
        self.timer.stop()
        pygame.mixer.music.pause()
        pygame.mixer.music.set_pos(
            self.horizontalSlider.value()*self.musiclength/100)
        # sleep(2)
        pygame.mixer.music.unpause()
        print('set:',  int(pygame.mixer.music.get_pos()/1000))
        self.timer.start()
        self.flag = int(self.horizontalSlider.value() -
                        pygame.mixer.music.get_pos()/self.musiclength/10)
        print("拖动：",  self.flag)

    @pyqtSlot(int)
    def on_horizontalSlider_valueChanged(self, value):
        """
        Slot documentation goes here.

        @param value DESCRIPTION
        @type int
        """
        # TODO: not implemented yet
        # self.label.setText(str(self.horizontalSlider.value()))

    @pyqtSlot()
    def on_pushButton_2_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
#        self.listWidget.addItem(f'添加第{self.line}行')
#        self.line += 1
        filename = QFileDialog.getOpenFileName(
            self, '选择mp3', './', 'MP3 文件(*.mp3)')
        if filename[0]:
            self.listWidget.addItem(filename[0])

    @pyqtSlot(QModelIndex)
    def on_listWidget_clicked(self, index):
        """
        Slot documentation goes here.

        @param index DESCRIPTION
        @type QModelIndex
        """
        # TODO: not implemented yet
        print(
            f'当前:  {self.listWidget.currentRow()}  {self.listWidget.currentItem().text()}')
        print("总：",  self.listWidget.count(), ' 条')
        for i in range(self.listWidget.count()):
            print(f'第 {i+1} 条： {self.listWidget.item(i).text()}')

    @pyqtSlot(QModelIndex)
    def on_listWidget_doubleClicked(self, index):
        """
        Slot documentation goes here.

        @param index DESCRIPTION
        @type QModelIndex
        """
        # TODO: not implemented yet
        # self.label.setText(self.listWidget.currentItem().text())
        pygame.mixer.music.load(self.listWidget.currentItem().text())
        m3 = mp3.MP3(self.listWidget.currentItem().text())
        self.musiclength = m3.info.length
        pygame.mixer.music.play(-1)
        self.horizontalSlider.setValue(0)
        self.flag = 0
        #print("内部:",  m3.tags['TIT2'])
        filename = m3.filename.split('/')[-1].split('.')[0]
        self.label.setText(filename)

    @pyqtSlot()
    def on_pbPause_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        if self.paused:
            pygame.mixer.music.unpause()
            self.paused = False
            self.pbPause.setText("暂停")
        else:
            pygame.mixer.music.pause()
            self.paused = True
            self.pbPause.setText("继续")

    @pyqtSlot(int)
    def on_hsVule_valueChanged(self, value):
        """
        Slot documentation goes here.

        @param value DESCRIPTION
        @type int
        """
        # TODO: not implemented yet
        pygame.mixer.music.set_volume(self.hsVule.value()/100)

    @pyqtSlot(QPoint)
    def on_listWidget_customContextMenuRequested(self, pos):
        """
        Slot documentation goes here.

        @param pos DESCRIPTION
        @type QPoint
        """
        # TODO: not implemented yet
        if len(self.listWidget.selectedItems()) > 0:
            self.generateMenu(pos)
            if self.action == self.item1:
                self.listWidget.takeItem(self.listWidget.currentRow())
            elif self.action == self.item2:
                self.listWidget.clear()

    def generateMenu(self, pos):
        menu = QtWidgets.QMenu()
        ico_del = QtGui.QIcon('del.png')
        ico_clear = QtGui.QIcon('clear.png')
        self.item1 = menu.addAction(ico_del, u"删除")
        self.item2 = menu.addAction(ico_clear, u"清空")
        # menu.popup(QtGui.QCursor.pos())
        self.action = menu.exec(self.listWidget.mapToGlobal(pos))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    music = Music()

    music.show()
    sys.exit(app.exec())
