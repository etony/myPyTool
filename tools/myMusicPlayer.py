# -*- coding: utf-8 -*-

"""
Module implementing myMusicPlayer.
"""
from PyQt6.QtCore import pyqtSlot, QSize, Qt, QRectF, QSizeF, QModelIndex, QTimer
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
from eyed3 import load
from threading import Thread

global musicepath
global background
global myjson
global ready
global pause
global curindex
global page
global songname
global seq
global sourcelist

global atimer


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

        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.stop()
        self.timer.timeout.connect(self.timer_music)
        self.sourcelist = {'网易云': 'netease', 'QQ': 'qq', '酷我': 'kuwo',
                           '百度': 'baidu', '一听': 'yiting', '千千': 'tianhe', '咪咕': 'migu'}
        self.seq = True
        self.atimer = 0


    def timer_music(self):
        x = mixer.music.get_pos()
        seconds = int(x / 1000)
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        time = "%d:%02d:%02d" % (h, m, s)
         
        self.lab_song2.setText(time)
        
        print("timer is running...." + str(self.atimer))
        self.atimer += 1
        if mixer.music.get_busy() :
            print("忙")
        else:
            print("闲")

        self.next_song()

    def next_song(self):
        print("多线程开启")
        try:
            import time
            time.sleep(1)
            if not mixer.music.get_busy() and not self.pause :
                if self.seq:                    
                    self.curindex += 1
                    if self.curindex >= 20:
                        self.curindex = 0
                else:
                    import random
                    self.curindex = random.randint(0,20)


                pic = self.myjson[self.curindex]['pic']
                url = self.myjson[self.curindex]['url']

                self.loadbackground(pic)
                filename = self.myjson[self.curindex]['title'] + \
                    '-' + self.myjson[self.curindex]['author']
                self.download_music(url, filename)
                self.pb_pause.setText("||")
                self.pause = False
                self.lw_songs.setCurrentRow(self.curindex)
                
        except:
            pass
                    
        self.timer.start()        
        

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
        self.statusbar.showMessage("开始下载 ... " + self.songname)
        filename = os.path.join(self.musicepath, filename) + '.mp3'
        if not os.path.exists(filename):
            with requests.get(url) as r:
                with open(filename, 'wb') as f:
                    f.write(r.content)

            self.statusbar.showMessage("下载完毕 ... " + filename)
            self.ready = True

        if mixer.get_busy():
            mixer.stop()

        try:

            mixer.music.load(filename)
            # loops 是一个可选的整数参数，默认情况下为 0 ，它告诉您重复播放音乐多少次。如果将此参数设置为 -1 ,则音乐会无限重复播放。
            mixer.music.play()
            musicinfo = load(filename)
            self.timer.start()
        except:
            self.statusbar.showMessage("下载失败  (┬＿┬) ... " + self.songname)
            mixer.music.unload()
            os.remove(filename)
            return
        try:
            timenum = musicinfo.info.time_secs
            m, s = divmod(timenum, 60)
            h, m = divmod(m, 60)
            time = "%d:%02d:%02d" % (h, m, s)
            self.lab_song.setText(time)
        except:
            pass
        
        self.lab_songname.setText(self.songname)
        self.statusbar.showMessage('播放中 ... ')

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
        self.songname = filename
        self.download_music(url, filename)
        self.pb_pause.setText("||")
        self.pause = False

    @pyqtSlot()
    def on_pb_search_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        source = self.cb_list.currentText().strip('-').strip()
        sourcecode = self.sourcelist[source]

        self.lw_songs.addItem('搜索中')
        urlss = ['http://www.xmsj.org/', 'http://y.yin2s.com/']
        url = urlss[0]
        header = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.110.430.128 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest'
        }
        self.lw_songs.clear()
        self.myjson = []

        search = self.le_search.text().strip()
        if len(search) <= 0:
            return

        for i in range(self.page):
            params = {'input': search, 'filter': 'name',
                      'type': sourcecode, 'page': i+1}
            res = requests.post(url, params, headers=header)
            html = res.json()
            print("*"*30)
            print(html)
            if html['code'] == 200:
                self.myjson = self.myjson + html['data']

                for it in range(10):
                    # title = '('+ html['data'][it]['type']+')' + \
                    title = '(' + source + ')' + html['data'][it]['title'] + '-' + \
                            html['data'][it]['author']
                    self.lw_songs.addItem(title)
                    self.statusbar.showMessage('资源搜索完毕 ...')
            else:
                self.statusbar.showMessage('资源搜索失败，通道试试！！！   (┬＿┬) ')

    @pyqtSlot()
    def on_pb_back_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        self.curindex -= 1
        if self.curindex < 0:
            self.curindex = 19

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
            mixer.music.unpause()
            self.pb_pause.setText("||")
            self.pause = False
            self.timer.start()
        else:
            mixer.music.pause()
            self.pb_pause.setText("▶")
            self.pause = True
            self.timer.stop()

    @pyqtSlot()
    def on_pb_forwad_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet

        self.curindex += 1
        if self.curindex >= 20:
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
        if self.seq :
            self.pb_seq.setText("x")
            self.seq = False
        else:
            self.pb_seq.setText("=")
            self.seq = True

    @pyqtSlot(QCloseEvent)
    def closeEvent(self, QCloseEvent):
        mixer.quit()

    @pyqtSlot()
    def on_hs_value_sliderReleased(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet

        mixer.music.set_volume(round(self.hs_value.value()/100, 1))


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    myMusicPlayer = myMusicPlayer()
    myMusicPlayer.show()
    sys.exit(app.exec())
