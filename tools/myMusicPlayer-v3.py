# -*- coding: utf-8 -*-

"""
Module implementing myMusicPlayer.
pygame == 2.3.0
"""
from PyQt6.QtCore import pyqtSlot, Qt, QModelIndex, QTimer, QThread, pyqtSignal, QMutex, QPoint, QCoreApplication
from PyQt6.QtWidgets import QMainWindow, QApplication, QFileDialog, QMenu, QSystemTrayIcon, QStyleFactory
from PyQt6.QtGui import QPixmap, QCloseEvent, QIcon, QAction


from Ui_MusicPlayer_v3 import Ui_MusicPlayer
import requests
import os
import sys
import time
import logging
from PIL import Image, ImageDraw, ImageFilter
from pygame import mixer
from eyed3 import load
# import win32con
# from win32process import SuspendThread, ResumeThread
# import ctypes


qmut = QMutex()
qmut_lrc = QMutex()

global musicepath  # mp3 存储路径 /musicdata
musicepath = os.path.join(os.getcwd(), 'musicdata')

global localpath  # mp3 存储路径 /musicdata
localpath = os.path.join(os.getcwd(), 'musicdata')

global background  # 图片地址
background = os.path.join(musicepath, "background.png")

global site
site = "web"  # love, local

global source  # 搜索源 '网易云'
global search  # 搜索文字
global myjson  # 资源列表
global myjson_love
global myjson_local
global pause
global curindex  # 当前mp3 编号
curindex = 0
global songname  # 歌曲名称
global filename  # 歌曲路径
global seq  # 播放顺序
seq = True

global page
global sourcelist
page = 2
sourcelist = {'网易云': 'netease', '酷我': 'kuwo', 'QQ': 'qq',
              '百度': 'baidu', '一听': 'yiting', '千千': 'tianhe', '咪咕': 'migu'}
urllist = {'通道1': 'http://miss.qingchengkg.cn/', '通道2': 'http://tool.tesiber.com/music/', '通道3': 'https://music.haom.ren/',
           '通道4': 'http://tool.eleuu.com/music/', '通道5': 'http://www.xmsj.org/', '通道6': 'http://y.yin2s.com/'}
global atimer
global working
global lrc_status

lrc_status = True

LOG = logging.getLogger(os.path.basename(sys.argv[0]))
logging.basicConfig(datefmt='%Y-%m-%d %H:%M:%S', format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    level=logging.INFO)


class GetListThread(QThread):
    # 自定义信号对象。参数str就代表这个信号可以传一个字符串
    trigger = pyqtSignal(str)

    def __init__(self):
        # 初始化函数
        super(GetListThread, self).__init__()
        self.working = True

    def __del__(self):
        # 线程状态改变与线程终止
        self.working = False
        self.wait()

    def run(self):
        # 重写线程执行的run函数
        # 触发自定义信号
        global source
        global search
        global page
        global myjson

        sourcecode = sourcelist[source]

        # urlss = ['http://miss.qingchengkg.cn/', 'http://www.xmsj.org/', 'http://y.yin2s.com/']
        url = urllist[urls]
        # url = urlss[0]
        header = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.110.430.128 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest'
        }
        myjson = []

        if len(search) <= 0:
            return

        for i in range(page):
            params = {'input': search, 'filter': 'name',
                      'type': sourcecode, 'page': i}
            res = requests.post(url, params, headers=header)
            html = res.json()
            LOG.info(html)
            if html['code'] == 200:
                myjson = myjson + html['data']

                # for it in range(10):
                #     # title = '('+ html['data'][it]['type']+')' + \
                #     title = '(' + source + ')' + html['data'][it]['title'] + '-' + \
                #             html['data'][it]['author']

                self.trigger.emit("ok")
            else:
                self.trigger.emit("err")
                LOG.warning(f"列表搜索失败！url:{url} params: {params}")
        LOG.info(f"列表搜索结束。 {len(myjson)}")
        return


class DownloadThread(QThread):
    # 自定义信号对象。参数str就代表这个信号可以传一个字符串
    trigger = pyqtSignal(str)

    def __init__(self):
        # 初始化函数
        super(DownloadThread, self).__init__()
        self.working = True

    def __del__(self):
        # 线程状态改变与线程终止
        self.working = False
        self.wait()

    def run(self):
        qmut.lock()
        global myjson
        global curindex

        global songname
        global musicepath
        global filename
        LOG.info(f"进入DownloadThread线程: tab-{site} id-{curindex}")

        # 下载图片
        pic = myjson[curindex]['pic']
        url = myjson[curindex]['url']

        songname = myjson[curindex]['title'] + \
            '-' + myjson[curindex]['author']

        if site == 'love':
            pic = myjson_love[curindex]['pic']
            url = myjson_love[curindex]['url']

            songname = myjson_love[curindex]['title'] + \
                '-' + myjson_love[curindex]['author']

        filename = os.path.join(musicepath, songname) + '.mp3'
        self.download_background(pic)
        self.download_music(url, filename)
        self.trigger.emit('ok')
        qmut.unlock()

    def download_background(self, picurl):
        global background
        background = os.path.join(musicepath, "background.png")
        with requests.get(picurl) as r:
            with open(background, "wb") as w:
                w.write(r.content)

        self.draw_circle(background)

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
        if not os.path.exists(filename):
            with requests.get(url) as r:
                with open(filename, 'wb') as f:
                    f.write(r.content)

    def last(self):
        LOG.info("这里会执行吗？.............不会！")


class AddLoalThread(QThread):
    # 自定义信号对象。参数str就代表这个信号可以传一个字符串
    trigger = pyqtSignal(str)

    def __init__(self):
        # 初始化函数
        super(AddLoalThread, self).__init__()
        self.working = True

    def __del__(self):
        # 线程状态改变与线程终止
        self.working = False
        self.wait()

    def run(self):
        global myjson_local

        for root, dirs, files in os.walk(localpath):
            for file in files:
                if file.endswith('mp3'):
                    musicdict = {'type': '本地', 'link': os.path.join(root, file), 'songid': 0, 'title': file,
                                 'author': file, 'lrc': ' ', 'url': os.path.join(root, file), 'pic': background}
                    myjson_local.append(musicdict)

        self.trigger.emit('ok')


class LrcThread(QThread):
    # 自定义信号对象。参数str就代表这个信号可以传一个字符串
    trigger = pyqtSignal(str)

    def __init__(self):
        # 初始化函数
        super(LrcThread, self).__init__()
        self.working = True
        # handle = -1

    def __del__(self):
        # 线程状态改变与线程终止
        self.working = False
        # self.wait()

    def run(self):
        LOG.info(f'歌词显示~~~~ tab-{site}  id-{curindex}')
        # try:
        #     self.handle = ctypes.windll.kernel32.OpenThread(win32con.PROCESS_ALL_ACCESS, False, int(QThread.currentThreadId()))
        # except Exception as e:
        #     LOG.info(f'thread id  {int(QThread.currentThreadId())}')
        # qmut_lrc.lock()
        lrc = myjson[curindex]['lrc']
        lrclist = lrc.strip().splitlines()
        # for l in lrclist:
        #     self.lw_lrc.addItem(l)
        #     LOG.info(lrclist)
        musicDict = {}  # 用字典来保存该时刻对应的歌词
        musicL = []
        for i in lrclist:
            musicTime = i.split("]")

            for j in musicTime[:-1]:
                # LOG.info(f'歌词分割:  {j}')
                try:
                    musicTime1 = j[1:].split(":")
                    musicTL = float(musicTime1[0])*60+float(musicTime1[1])
                    musicDict[musicTL] = musicTime[-1]
                except Exception as e:
                    LOG.info(f'歌词分割异常:  {e}')
                    pass
        for i in musicDict:
            musicL.append(i)  # 将时间存到列表中
        LOG.info(f'线程内  {lrc_status}')
        if len(musicL) < 2:
            self.trigger.emit("无歌词~~")
        else:
            for j in range(len(musicL)-1):
                # if lrc_status:
                str = musicDict.get(musicL[j])
                self.trigger.emit(str)
                LOG.info(str)  # 输出歌词
                time.sleep(musicL[j+1]-musicL[j])

            # else:
            #     LOG.info("收到终止信号~")
            #     qmut_lrc.unlock()
            #     return
        # qmut_lrc.unlock()


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
        pix = QPixmap(background)
        self.lab_background.setPixmap(pix.scaled(
            200, 200, Qt.AspectRatioMode.KeepAspectRatio))

        self.pause = False
        mixer.init(size=-16, channels=2)
        # frequency这里是调频率...
        # size参数表示每个音频样本使用的位数。如果值为负，则将使用带符号的样本值。正值表示将使用不带符号的音频样本，无效值会引发异常。
        # channels参数用于指定是使用单声道还是立体声。 1为单声道，2为立体声。不支持其他值（负值被视为1，大于2的值被视为2）。

        self.lw_songs.setStyleSheet("QListWidget{border:1px solid gray; color:black; }"
                                    "QListWidget::Item{padding-top:5px; padding-bottom:1px; }"
                                    "QListWidget::Item:hover{background:skyblue; }"
                                    "QListWidget::item:selected{background:lightgray; color:blue; }"
                                    "QListWidget::item:selected:!active{border-width:0px; background:skyblue; }"
                                    )
        self.lw_lovesongs.setStyleSheet("QListWidget{border:1px solid gray; color:black; }"
                                        "QListWidget::Item{padding-top:5px; padding-bottom:1px; }"
                                        "QListWidget::Item:hover{background:skyblue; }"
                                        "QListWidget::item:selected{background:lightgray; color:blue; }"
                                        "QListWidget::item:selected:!active{border-width:0px; background:skyblue; }"
                                        )
        self.lw_lrc.setStyleSheet("QListWidget{border:1px solid gray; color:black; }"
                                  "QListWidget::Item{padding-top:1px; padding-bottom:1px; }"
                                  "QListWidget::Item:hover{background:skyblue; }"
                                  "QListWidget::item:selected{background:lightgray; color:blue; }"
                                  "QListWidget::item:selected:!active{border-width:0px; background:skyblue; }"
                                  )

        self.tabWidget.setStyleSheet(
            "QTabBar::tab::selected{background:rgb(0, 144, 255)}")
        self.lw_lrc.setVisible(False)

        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.stop()
        self.timer.timeout.connect(self.timer_music)
        self.sourcelist = {'网易云': 'netease', 'QQ': 'qq', '酷我': 'kuwo',
                           '百度': 'baidu', '一听': 'yiting', '千千': 'tianhe', '咪咕': 'migu'}
        self.seq = True
        self.atimer = 0
        self.statusbar.showMessage("就绪")
        self.lab_songname.setText('')
        self.setWindowTitle("音乐播放器  -  在线版")
        self.setFixedSize(self.width(), self.height())

        global myjson
        myjson = []
        global myjson_local
        myjson_local = []
        global myjson_love
        myjson_love = []
        global songname
        songname = ''
        global filename
        filename = ''
        global urls

        self.lw_localsongs.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu)  # 对象的上下文菜单的策略
        self.lw_songs.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu)  # 对象的上下文菜单的策略
        self.lw_lovesongs.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu)  # 对象的上下文菜单的策略

        self.lrcwork = LrcThread()
        # self.lrcwork.finished.connect(self.lrcwork.deleteLater)
        self.lrcwork.trigger.connect(self.dislrc)

    #     self.lw_localsongs.customContextMenuRequested.connect(self.on_context_menu) # 设置唤起右键菜单的slots

    # def on_context_menu(self,pos):

    #     menu = QMenu()
    #     item1 = menu.addAction(u"清除")
    #     item2 = menu.addAction(u"拷贝")
    #     item3 = menu.addAction(u"粘贴")
    #     self.action = menu.exec(self.lw_localsongs.mapToGlobal(pos))

    #     if self.action == item1:
    #         LOG.info('清除')
    # 托盘图标
        self.showAction = QAction("显示", self, triggered=self.showNormal)
        self.quitAction = QAction(
            "退出", self, triggered=self.quitApp)  # app.quit
        self.showAction.setIcon(QIcon("show.jpg"))
        self.quitAction.setIcon(QIcon("quit.jpg"))
        self.trayIconMenu = QMenu(self)
        self.trayIconMenu.addAction(self.showAction)
        self.trayIconMenu.addAction(self.quitAction)

        self.trayIcon = QSystemTrayIcon(self)
        self.trayIcon.setIcon(QIcon("music-tray.png"))
        self.trayIcon.setContextMenu(self.trayIconMenu)
        self.trayIcon.show()

        # 下载通道选项
        urls = self.cb_urls.currentText().strip()

        self.cbbox.addItems(['windows11', 'Fusion'])

    def quitApp(self):
        self.trayIcon = None
        # app.quit()
        sys.exit(app.exec())
        # QCoreApplication.quit()

    def changeEvent(self, event):
        if event.type() == 105:
            if self.isMinimized():
                self.hide()
                LOG.info("==========窗口最小化==========")

    def timer_music(self):
        x = mixer.music.get_pos()
        seconds = int(x / 1000)
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        time = "%d:%02d:%02d" % (h, m, s)

        self.lab_song2.setText(time)  # str(x)
        # x = round(float(x/1000),2)
        # self.lw_lrc.addItem(self.musicDict[self.musicL.index(x)])

        if not mixer.music.get_busy():
            self.next_song()

    def next_song(self):
        global curindex
        ll = len(myjson)
        if site == 'love':
            ll = len(myjson_love)
        elif site == 'local':
            ll = len(myjson_local)
            LOG.info(f"自动 next song: tab-{str(ll)}  id-{curindex}")

        try:
            time.sleep(1)
            if not mixer.music.get_busy() and not self.pause:
                if seq:
                    curindex += 1
                    if curindex >= ll:
                        curindex = 0
                else:
                    import random
                    curindex = random.randint(0, ll-1)
        except:
            pass
        LOG.info(f"next song: 共 {str(ll)}  第 id-{curindex}")
        if site == 'web':

            try:
                self.downloadwork = DownloadThread()
                self.downloadwork.start()
                self.downloadwork.trigger.connect(self.beginplay)
                self.lw_songs.setCurrentRow(curindex)
                self.displaylrc()
            except:
                pass
        elif site == 'love':
            try:
                self.downloadwork = DownloadThread()
                self.downloadwork.start()
                self.downloadwork.trigger.connect(self.beginplay)
                self.lw_lovesongs.setCurrentRow(curindex)
                self.displaylrc()
            except:
                pass
        elif site == 'local':
            asong = myjson_local[curindex]['url']
            name = os.path.splitext(myjson_local[curindex]['title'])[0]
            self.playmusic(asong)
            self.lab_songname.setText(name)
            self.lw_localsongs.setCurrentRow(curindex)

        self.pb_pause.setText("||")
        self.pause = False

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

    # def download_music(self, url, filename):
    #     self.statusbar.showMessage("开始下载 ... " + self.songname)
    #     filename = os.path.join(self.musicepath, filename) + '.mp3'
    #     if not os.path.exists(filename):
    #         with requests.get(url) as r:
    #             with open(filename, 'wb') as f:
    #                 f.write(r.content)

    #         self.statusbar.showMessage("下载完毕 ... " + filename)
    #         self.ready = True

    #     if mixer.get_busy():
    #         mixer.stop()

    #     try:

    #         mixer.music.load(filename)
    #         # loops 是一个可选的整数参数，默认情况下为 0 ，它告诉您重复播放音乐多少次。如果将此参数设置为 -1 ,则音乐会无限重复播放。
    #         mixer.music.play(0)
    #         musicinfo = load(filename)
    #         self.timer.start()
    #     except:
    #         self.statusbar.showMessage("下载失败  (┬＿┬) ... " + self.songname)
    #         mixer.music.unload()
    #         # os.remove(filename)
    #         return
    #     try:
    #         timenum = musicinfo.info.time_secs
    #         m, s = divmod(timenum, 60)
    #         h, m = divmod(m, 60)
    #         time = "%d:%02d:%02d" % (h, m, s)
    #         self.lab_song.setText(time)
    #     except:
    #         pass

    #     self.lab_songname.setText(self.songname)
    #     self.statusbar.showMessage('播放中 ... ')

    @pyqtSlot(QModelIndex)
    def on_lw_songs_clicked(self, index):
        """
        Slot documentation goes here.

        @param index DESCRIPTION
        @type QModelIndex
        """

        global curindex
        curindex = self.lw_songs.currentRow()
        global site
        global lrc_status
        site = "web"

        LOG.info(f"开始调用线程进行mp3下载: tab-{site}  id-{curindex}")
        self.downloadwork = DownloadThread()
        lrc_status = False

        try:
            lrc_status = True
            self.downloadwork.start()
            self.downloadwork.trigger.connect(self.beginplay)
            self.displaylrc()

        except Exception as e:
            LOG.warning(f'start download mp3 error:  {e}')
            pass

        # try:
        #     self.lw_lrc.clear()
        #     # ret = ctypes.windll.kernel32.TerminateThread(self.lrcwork.handle, 0)
        #     # LOG.info(f'终止线程   {self.lrcwork.handle}   {ret}')
        #     self.lrcwork.terminate()

        # except Exception as e:
        #     LOG.info(f'start displaly lrc error:  {e}')
        #     pass
        # time.sleep(2)

        # self.lrcwork.start()
        # # pic = myjson[self.curindex]['pic']
        # # url = myjson[self.curindex]['url']

        # # self.loadbackground(pic)
        # # filename = myjson[self.curindex]['title'] + \
        # #     '-' + myjson[self.curindex]['author']
        # # self.songname = filename
        # # self.download_music(url, filename)
        # # self.pb_pause.setText("||")
        # # self.pause = False
        # self.lw_lrc.setVisible(True)

    def displaylrc(self):
        try:
            self.lw_lrc.clear()
            self.lrcwork.terminate()
        except Exception as e:
            LOG.warning(f'stop displaly lrc error:  {e}')

        time.sleep(2)
        self.lrcwork.start()
        self.lw_lrc.setVisible(True)

        return

    def beginplay(self, str):
        LOG.info(f"线程返回值： {str}")

        global songname
        global background
        if str == 'ok':
            self.pb_pause.setText("||")
            self.statusbar.showMessage("下载完毕 ... " + songname)
            LOG.info(f"播放音乐:  {songname}")
            self.playmusic(filename)
            self.lab_songname.setText(songname)

            pix = QPixmap(background)

            self.lab_background.setPixmap(pix.scaled(
                220, 220, Qt.AspectRatioMode.KeepAspectRatio))

        else:
            self.statusbar.showMessage("下载失败  (┬＿┬) ... " + songname)

    def playmusic(self, asong):

        if mixer.get_busy():
            mixer.stop()

        try:

            mixer.music.load(asong)
            # loops 是一个可选的整数参数，默认情况下为 0 ，它告诉您重复播放音乐多少次。
            # 如果将此参数设置为 -1 ,则音乐会无限重复播放。
            mixer.music.play(0)
            musicinfo = load(asong)
            self.timer.start()

        except:
            self.statusbar.showMessage(f"播放失败  (┬＿┬) ... {songname}")
            mixer.music.unload()
            LOG.info(f"删除问题地址: tab-{site} id-{curindex} : {asong}")
            os.remove(asong)
            if site == 'web':
                self.lw_songs.takeItem(curindex)
                global myjson
                del myjson[curindex]
            elif site == 'love':
                self.lw_lovesongs.takeItem(curindex)
                global myjson_love
                del myjson_love[curindex]
            return
        try:
            timenum = musicinfo.info.time_secs
            m, s = divmod(timenum, 60)
            h, m = divmod(m, 60)
            time = "%d:%02d:%02d" % (h, m, s)
            self.lab_song.setText(time)
        except:
            pass

        # self.downloadwork = None

    def dislrc(self, lrc):
        self.lw_lrc.addItem(lrc)
        size = self.lw_lrc.count()
        if size >= 1:
            self.lw_lrc.setCurrentRow(size-1)
        if size > 6:
            self.lw_lrc.takeItem(0)

    @pyqtSlot()
    def on_pb_search_clicked(self):
        """
        Slot documentation goes here.
        """

        global source
        global search
        global urls

        source = self.cb_list.currentText().strip('-').strip()
        urls = self.cb_urls.currentText().strip()
        search = self.le_search.text().strip()
        if len(search) <= 0:
            self.statusbar.showMessage('搜索中 ...  寂寞啊~~~')
        else:
            self.statusbar.showMessage('搜索中 ...')
            self.getlistwork = GetListThread()
            self.getlistwork.trigger.connect(self.displaylist)
            self.getlistwork.start()
            self.tabWidget.setCurrentIndex(0)

        # sourcecode = self.sourcelist[source]

        # urlss = ['http://www.xmsj.org/', 'http://y.yin2s.com/']
        # url = urlss[0]
        # header = {
        #     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.110.430.128 Safari/537.36',
        #     'X-Requested-With': 'XMLHttpRequest'
        # }

        # self.myjson = []

        # search = self.le_search.text().strip()
        # if len(search) <= 0:
        #     return

        # for i in range(self.page):
        #     params = {'input': search, 'filter': 'name',
        #               'type': sourcecode, 'page': i+1}
        #     res = requests.post(url, params, headers=header)
        #     html = res.json()
        #     if html['code'] == 200:
        #         self.myjson = self.myjson + html['data']

        #         for it in range(10):
        #             # title = '('+ html['data'][it]['type']+')' + \
        #             title = '(' + source + ')' + html['data'][it]['title'] + '-' + \
        #                     html['data'][it]['author']
        #             self.lw_songs.addItem(title)
        #             self.statusbar.showMessage('资源搜索完毕 ...')
        #     else:
        #         self.statusbar.showMessage('资源搜索失败，通道试试！！！   (┬＿┬) ')

    @pyqtSlot()
    def on_le_search_returnPressed(self):
        global source
        global search

        source = self.cb_list.currentText().strip('-').strip()
        search = self.le_search.text().strip()
        if len(search) <= 0:
            self.statusbar.showMessage('搜索中 ...  寂寞啊~~~')
        else:
            self.statusbar.showMessage('搜索中 ...')
            self.getlistwork = GetListThread()
            self.getlistwork.trigger.connect(self.displaylist)
            self.getlistwork.start()

    def displaylist(self, status):
        global source
        global myjson
        self.lw_songs.clear()
        if status == 'ok':
            ll = len(myjson)
            if ll > 1:
                for it in range(ll):
                    title = '(' + source + ')   ' + \
                        myjson[it]['title'] + '-' + myjson[it]['author']
                    self.lw_songs.addItem(title)
                    self.statusbar.showMessage('资源搜索完毕 ...')
            else:
                self.statusbar.showMessage('资源搜索失败，通道试试！！！   (┬＿┬) ')

    @pyqtSlot()
    def on_pb_back_clicked(self):
        """
        Slot documentation goes here.
        """

        global curindex
        ll = len(myjson)
        if site == 'love':
            ll = len(myjson_love)
        elif site == 'local':
            ll = len(myjson_local)
        if ll > 0:
            curindex -= 1
            if curindex < 0:
                curindex = ll-1
            LOG.info(f"上一首 : tab-{site} id-{curindex}")
        else:
            return

        if site == 'web':
            self.downloadwork = DownloadThread()

            try:
                self.downloadwork.start()
                self.downloadwork.trigger.connect(self.beginplay)
                self.displaylrc()
            except:
                pass

            self.pb_pause.setText("||")
            self.pause = False
            self.lw_songs.setCurrentRow(curindex)
        elif site == 'love':

            self.downloadwork = DownloadThread()

            try:
                self.downloadwork.start()
                self.downloadwork.trigger.connect(self.beginplay)
                self.displaylrc()
            except:
                pass

            self.pb_pause.setText("||")
            self.pause = False
            self.lw_lovesongs.setCurrentRow(curindex)
            pass
        elif site == 'local':
            asong = myjson_local[curindex]['url']
            name = os.path.splitext(myjson_local[curindex]['title'])[0]
            self.playmusic(asong)
            self.lab_songname.setText(name)
            self.lw_localsongs.setCurrentRow(curindex)

    @pyqtSlot()
    def on_pb_pause_clicked(self):
        """
        Slot documentation goes here.
        """

        # if self.downloadwork.isRunning():
        #     LOG.info("线程运行中")
        #     #self.getlistwork = None
        # else:
        #     LOG.info("线程已经结束啦~~~")

        if self.pause:
            if len(myjson) > 0:
                mixer.music.unpause()
                self.pb_pause.setText("||")
                self.pause = False
                self.timer.start()
                time.sleep(4)  # 时间同步补偿 4 秒
                self.lrcwork.start()
        else:
            mixer.music.pause()
            self.pb_pause.setText("▶")
            self.pause = True
            self.timer.stop()
            self.lrcwork.exec()

    @pyqtSlot()
    def on_pb_forwad_clicked(self):
        """
        Slot documentation goes here.
        """

        # global curindex

        # ll = len(myjson)
        # if ll > 0:
        #     curindex += 1
        #     if curindex >= ll:
        #         curindex = 0
        #     LOG.info("下一首")

        #     self.downloadwork = DownloadThread()

        #     try:
        #         self.downloadwork.start()
        #         self.downloadwork.trigger.connect(self.beginplay)
        #     except:
        #         pass

        #     self.pb_pause.setText("||")
        #     self.pause = False
        #     self.lw_songs.setCurrentRow(curindex)
        global curindex
        ll = len(myjson)
        if site == 'love':
            ll = len(myjson_love)
        elif site == 'local':
            ll = len(myjson_local)
        if ll > 0:
            curindex += 1
            if curindex >= ll:
                curindex = 0
            LOG.info(f"下一首: tab-{site} id-{curindex}")
        else:
            return

        if site == 'web':
            self.downloadwork = DownloadThread()

            try:
                self.downloadwork.start()
                self.downloadwork.trigger.connect(self.beginplay)
                self.displaylrc()
            except:
                pass

            self.pb_pause.setText("||")
            self.pause = False
            self.lw_songs.setCurrentRow(curindex)
        elif site == 'love':
            self.downloadwork = DownloadThread()

            try:
                self.downloadwork.start()
                self.downloadwork.trigger.connect(self.beginplay)
                self.displaylrc()
            except:
                pass

            self.pb_pause.setText("||")
            self.pause = False
            self.lw_lovesongs.setCurrentRow(curindex)
            pass
        elif site == 'local':
            asong = myjson_local[curindex]['url']
            name = os.path.splitext(myjson_local[curindex]['title'])[0]
            self.playmusic(asong)
            self.lab_songname.setText(name)
            self.lw_localsongs.setCurrentRow(curindex)

    @pyqtSlot()
    def on_pb_seq_clicked(self):
        """
        Slot documentation goes here.
        """
        global seq
        if seq:
            self.pb_seq.setText("x")
            seq = False
        else:
            self.pb_seq.setText("=")
            seq = True

        # if self.pb_seq.text() == '=':
        #     self.pb_seq.setText("x")
        # elif self.pb_seq.text() == 'x':
        #     self.pb_seq.setText("o")
        # else:
        #     self.pb_seq.setText("=")

    @pyqtSlot(QCloseEvent)
    def closeEvent(self, QCloseEvent):
        LOG.info('窗口关闭')
        global lrc_status
        lrc_status = False
        self.lrcwork.terminate()

        if hasattr(self, 'downloadwork'):
            self.downloadwork.quit()

        mixer.music.stop()
        mixer.quit()
        # os._exit(0)

    @pyqtSlot()
    def on_hs_value_sliderReleased(self):
        """
        Slot documentation goes here.
        """

        mixer.music.set_volume(round(self.hs_value.value()/100, 1))

    @pyqtSlot(QPoint)
    def on_lw_localsongs_customContextMenuRequested(self, pos):
        self.generateMenu(pos)
        global myjson_local
        global localpath

        if self.action == None:
            return
        if self.action == self.load:
            self.filepath = QFileDialog.getExistingDirectory(
                None, '选择路径', os.getcwd())

            if self.filepath != None:
                self.addlocalwork = AddLoalThread()
                try:
                    self.addlocalwork.start()
                    self.addlocalwork.trigger.connect(self.displayLocal)
                except:
                    pass

        elif self.action == self.clear:
            myjson_local.clear()
            self.lw_localsongs.clear()
        elif self.action == self.dele:
            items = self.lw_localsongs.selectedIndexes()
            for it in items:
                r = it.row()
                LOG.info(f'删除:  tab-{site} id-{curindex}')
                self.lw_localsongs.takeItem(r)
                del myjson_local[r]

    def displayLocal(self, status):
        if status == 'ok':
            ll = len(myjson_local)
            if ll > 0:
                self.lw_localsongs.clear()
                for it in range(ll):
                    title = '(' + myjson_local[it]['type'] + \
                        ')   ' + myjson_local[it]['title']
                    self.lw_localsongs.addItem(title)
            LOG.info(f"加载本地音乐: 共 {str(ll)} 首")

    @pyqtSlot(QModelIndex)
    def on_lw_localsongs_clicked(self, index):
        global site
        site = "local"
        global curindex

        curindex = self.lw_localsongs.currentRow()
        asong = myjson_local[curindex]['url']
        name = os.path.splitext(myjson_local[curindex]['title'])[0]
        self.playmusic(asong)
        self.lab_songname.setText(name)
        self.lw_lrc.setVisible(False)

    def generateMenu(self, pos):
        menu = QMenu()
        ico_load = QIcon('local.png')
        ico_clear = QIcon('clear.png')
        ico_del = QIcon('delete.png')
        ll = len(myjson_local)
        self.load = menu.addAction(ico_load, u"加载")
        if ll > 0:
            self.dele = menu.addAction(ico_del, u"删除")
            self.clear = menu.addAction(ico_clear, u"清空")
        self.action = menu.exec(self.lw_localsongs.mapToGlobal(pos))

    @pyqtSlot(QModelIndex)
    def on_lw_lovesongs_clicked(self, index):
        global site
        site = "love"
        global curindex
        curindex = self.lw_lovesongs.currentRow()

        LOG.info(f"开始调用线程进行mp3下载: tab-{site} id-{curindex}")
        self.downloadwork = DownloadThread()

        try:
            self.downloadwork.start()
            self.downloadwork.trigger.connect(self.beginplay)
            self.displaylrc()
        except:
            pass

    @pyqtSlot(QPoint)
    def on_lw_songs_customContextMenuRequested(self, pos):
        self.genALoveMenu(pos)

        if self.action == self.love:
            items = self.lw_songs.selectedIndexes()
            global myjson_love
            for it in items:
                myjson_love.append(myjson[it.row()])

                LOG.info(f'选中操作-我喜欢:  id-{it.row()}')
                title = myjson[it.row()]['title'] + '-' + \
                    myjson[it.row()]['author']
                self.lw_lovesongs.addItem(title)
            pass
            # LOG.info(str(self.lw_songs.)))
        else:
            pass

    def genALoveMenu(self, pos):
        menu = QMenu()
        ico_love = QIcon('heart.png')

        ll = len(myjson)
        if ll > 0:
            self.love = menu.addAction(ico_love, u"我喜欢")
        self.action = menu.exec(self.lw_songs.mapToGlobal(pos))

    @pyqtSlot(QPoint)
    def on_lw_lovesongs_customContextMenuRequested(self, pos):
        self.genLoveMenu(pos)

        items = self.lw_lovesongs.selectedIndexes()
        global myjson_love
        if self.action == None:
            return
        if self.action == self.clear:
            myjson_love.clear()
            self.lw_lovesongs.clear()
        elif self.action == self.dele:
            items = self.lw_lovesongs.selectedIndexes()
            for it in items:
                r = it.row()
                LOG.info(f'remove love item:  id-{r}')
                self.lw_lovesongs.takeItem(r)
                del myjson_love[r]

    def genLoveMenu(self, pos):
        menu = QMenu()
        ico_clear = QIcon('clear.png')
        ico_del = QIcon('delete.png')

        ll = len(myjson_love)
        if ll > 0:
            self.dele = menu.addAction(ico_del, u"删除")
            self.clear = menu.addAction(ico_clear, u"清空")
        self.action = menu.exec(self.lw_songs.mapToGlobal(pos))

    @pyqtSlot(int)
    def on_tabWidget_currentChanged(self, index):
        tab = self.tabWidget.currentWidget().objectName()
        LOG.info(f'当前标签页:  {tab}')
        if tab != "local":
            self.pb_lrc.setVisible(True)
        else:
            self.pb_lrc.setVisible(False)

    @pyqtSlot()
    def on_pb_lrc_clicked(self):
        if self.lw_lrc.isVisible():
            self.lw_lrc.setVisible(False)
        else:
            self.lw_lrc.setVisible(True)

        pass

    @pyqtSlot(str)
    def on_cbbox_textActivated(self, p0):
        QApplication.setStyle(QStyleFactory.create(p0))
        # QApplication.setPalette(QApplication.style().standardPalette())
        # time.sleep(5)
        # QApplication.setPalette(QApplication.palette())

    def flush(self):
        pass
        # 避免出现 RuntimeError: wrapped C/C++ object of type LrcThread has been deleted


if __name__ == "__main__":
    import sys
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    myMusicPlayer = myMusicPlayer()
    myMusicPlayer.show()
    sys.exit(app.exec())


# class qthreadtest(QDialog, Ui_Dialog):
#     """
#     Class documentation goes here.
#     """

#     def __init__(self, parent=None):
#         """
#         Constructor

#         @param parent reference to the parent widget (defaults to None)
#         @type QWidget (optional)
#         """
#         super().__init__(parent)
#         self.setupUi(self)
#         self.work = WorkThread()
#         self.work.trigger.connect(self.display)

#     @pyqtSlot()
#     def on_pushButton_clicked(self):
#         """
#         Slot documentation goes here.
#         """
#         self.work.start()
#         # 线程自定义信号连接的槽函数
#         #self.pushButton.setEnabled(False)


#     def display(self,str):
#         # 由于自定义信号时自动传递一个字符串参数，所以在这个槽函数中要接受一个参数
#         self.listWidget.addItem(str)

# class WorkThread(QThread):
#     # 自定义信号对象。参数str就代表这个信号可以传一个字符串
#     trigger = pyqtSignal(str)

#     def __int__(self):
#         # 初始化函数
#         super(WorkThread, self).__init__()
#         self.working = True


#     def __del__(self):
#         #线程状态改变与线程终止
#         self.working = False
#         self.wait()

#     def run(self):
#         #重写线程执行的run函数
#         #触发自定义信号
#         for i in range(5):
#             time.sleep(1)
#             # 通过自定义信号把待显示的字符串传递给槽函数
#             self.trigger.emit(str(i))
