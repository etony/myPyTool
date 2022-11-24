# -*- coding: utf-8 -*-

"""
Module implementing myMusicPlayer.
"""
from PyQt6.QtCore import pyqtSlot, QSize, Qt, QRectF, QSizeF, QModelIndex
from PyQt6.QtWidgets import QMainWindow, QApplication, QFileDialog, QMessageBox
from PyQt6.QtGui import QImage, QPixmap, QPainter, QMovie, QPainterPath, QCloseEvent

from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QMainWindow

from Ui_MusicPlayer import Ui_MusicPlayer
import requests
import os
import sys
from PIL import Image, ImageDraw, ImageFilter
from pygame import mixer

global musicepath
global background
global myjson
global ready
global pause
global curindex
global page


class myMusicPlayer(QMainWindow, Ui_MusicPlayer):
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
        self.musicepath = os.path.join(os.getcwd(), 'musicdata')
        if not os.path.exists(self.musicepath):
            os.mkdir(self.musicepath)

        url = "https://api.dujin.org/bing/1920.php"
        self.loadbackground(url)
        ready = False
        self.page = 2
        self.pause = False
        mixer.init(frequency=8000, size=-16, channels=4)

        self.lw_songs.setStyleSheet("QListWidget{border:1px solid gray; color:black; }"
                                    "QListWidget::Item{padding-top:5px; padding-bottom:1px; }"
                                    "QListWidget::Item:hover{background:skyblue; }"
                                    "QListWidget::item:selected{background:lightgray; color:blue; }"
                                    "QListWidget::item:selected:!active{border-width:0px; background:skyblue; }"
                                    )

    def loadbackground(self, url):

        background = os.path.join(self.musicepath, "background.png")
        with requests.get(url) as r:
            with open(background, "wb") as w:
                w.write(r.content)
        self.background = background
        self.draw_circle(self.background)
        pix = QPixmap(self.background)

        self.lab_background.setPixmap(pix.scaled(
            220, 220, Qt.AspectRatioMode.KeepAspectRatio))

    def draw_circle(self, imgfile):
        img = Image.open(imgfile)
        w, h = img.size
        radius = int(w/2)
        if w > h:
            radius = int(h/2)

        startx, starty = 0, 0
        if w > h:
            startx = int((w-h)/2)
        if w < h:
            starty = int((h-w)/2)

        img = img.crop((startx, starty, startx+radius*2, starty+radius*2))

        mask = Image.new("L", img.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, radius*2, radius*2), fill=255)
        mask = mask.filter(ImageFilter.GaussianBlur(0))
        result = img.copy()
        result.putalpha(mask)
        result.save(imgfile)

    def download_music(self, url, filename):
        self.statusbar.showMessage("开始下载 ... " + filename)
        filename = os.path.join(self.musicepath, filename) + '.mp3'
        if not os.path.exists(filename):
            with requests.get(url) as r:
                with open(filename, 'wb') as f:
                    f.write(r.content)

        self.statusbar.showMessage("下载完毕 ... " + filename)
        self.ready = True

        if mixer.get_busy():
            mixer.stop()
        self.sound = mixer.Sound(filename)
        self.sound.play()

        self.statusbar.showMessage('播放中 ... ' + filename)

    @pyqtSlot(QModelIndex)
    def on_lw_songs_clicked(self, index):
        """
        Slot documentation goes here.

        @param index DESCRIPTION
        @type QModelIndex
        """

        self.curindex = self.lw_songs.currentRow()

        pic = self.myjson[self.curindex]['pic']
        url = self.myjson[self.curindex]['url']

        self.loadbackground(pic)
        filename = self.myjson[self.curindex]['title'] + \
            '-' + self.myjson[self.curindex]['author']
        self.download_music(url, filename)
        self.pb_pause.setText("||")
        self.pause = False

    @pyqtSlot()
    def on_pb_search_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        self.lw_songs.addItem('搜索中')
        urlss = ['http://www.xmsj.org/', 'http://y.yin2s.com/']
        url = urlss[0]
        header = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.110.430.128 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest'

        }
        self.lw_songs.clear()
        self.myjson = []
        for i in range(self.page):
            params = {'input': "童话镇", 'filter': 'name',
                      'type': 'netease', 'page': i+1}
            res = requests.post(url, params, headers=header)
            html = res.json()
            self.myjson = self.myjson + html['data']

            for it in range(10):
                title = '('+html['data'][it]['type']+')' + \
                    html['data'][it]['title'] + '-' + \
                        html['data'][it]['author']
                self.lw_songs.addItem(title)

    @pyqtSlot()
    def on_pb_back_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        self.curindex -= 1
        if self.curindex < 0:
            self.curindex = 9

        pic = self.myjson[self.curindex]['pic']
        url = self.myjson[self.curindex]['url']

        self.loadbackground(pic)
        filename = self.myjson[self.curindex]['title'] + \
            '-' + self.myjson[self.curindex]['author']
        self.download_music(url, filename)
        self.pb_pause.setText("||")
        self.pause = False
        self.lw_songs.setCurrentRow(self.curindex)

    @pyqtSlot()
    def on_pb_pause_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        if self.pause:
            mixer.unpause()
            self.pb_pause.setText("||")
            self.pause = False
        else:
            mixer.pause()
            self.pb_pause.setText("▶")
            self.pause = True

    @pyqtSlot()
    def on_pb_forwad_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet

        self.curindex += 1
        if self.curindex >= 10:
            self.curindex = 0

        pic = self.myjson[self.curindex]['pic']
        url = self.myjson[self.curindex]['url']

        self.loadbackground(pic)
        filename = self.myjson[self.curindex]['title'] + \
            '-' + self.myjson[self.curindex]['author']
        self.download_music(url, filename)
        self.pb_pause.setText("||")
        self.pause = False
        self.lw_songs.setCurrentRow(self.curindex)

    @pyqtSlot()
    def on_pb_seq_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        raise NotImplementedError

    @pyqtSlot(QCloseEvent)
    def closeEvent(self, QCloseEvent):
        mixer.quit()

    @pyqtSlot()
    def on_hs_value_sliderReleased(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet

        self.sound.set_volume(round(self.hs_value.value()/100, 1))


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    myMusicPlayer = myMusicPlayer()
    myMusicPlayer.show()
    sys.exit(app.exec())
