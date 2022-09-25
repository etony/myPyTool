# -*- coding: utf-8 -*-
"""
Module implementing ImageExifWindow.
"""

from PyQt6.QtCore import pyqtSlot, Qt
from PyQt6.QtWidgets import QMainWindow, QFileDialog
from PyQt6 import QtCore, QtGui, QtWidgets
from Ui_imagexif import Ui_MainWindow
import exifread
import datetime

from PIL import Image, ImageFont, ImageDraw


class ImageExifWindow(QMainWindow, Ui_MainWindow):
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

    @pyqtSlot()
    def on_pbselect_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        global imgNamepath
        imgNamepath, imgType = QFileDialog.getOpenFileName(
            self, "选择图片", "E:\\", "*.jpg;;*.png;;All Files(*)")

        if imgNamepath != "":
            self.label_2.setScaledContents(True)
            #img = QtGui.QPixmap(imgNamepath).scaled(self.label_2.size())
            img = QtGui.QPixmap(imgNamepath)
            print("img: ", img.width(), img.height())
            if img.width() > img.height():
                self.label_2.setFixedSize(
                    363, int(img.height() / img.width() * 363))
            else:
                self.label_2.setFixedSize(
                    int(img.width() / img.height() * 363), 363)
            # 在label控件上显示选择的图片
            self.label_2.setPixmap(img)
            self.label_2.repaint()
            # 显示所选图片的路径
            self.lineEdit_2.setText(imgNamepath)
            self.pbread.setEnabled(True)
            self.pbreset.setEnabled(True)

    @pyqtSlot()
    def on_pbread_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        f = open(imgNamepath, 'rb')
        tags = exifread.process_file(f)

        try:
            tags = exifread.process_file(f)
            exifinfo = "手机品牌:  " + str(tags["Image Make"])
            exifinfo += "<br>手机型号:  " + str(tags["Image Model"])
            exifinfo += "<br>图片尺寸:  " + str(
                tags["Image ImageWidth"]) + " x " + str(
                    tags["Image ImageLength"]) + ' 像素'
            exifinfo += "<br>拍摄时间:  " + datetime.datetime.strptime(
                str(tags["Image DateTime"]),
                '%Y:%m:%d %H:%M:%S').strftime('%Y年%m月%d日 %H:%M:%S')
            exifinfo += '<br>  经度值:  　' + str(
                tags['GPS GPSLongitudeRef']) + str(tags['GPS GPSLongitude'])
            exifinfo += '<br>  纬度值:  　' + str(
                tags['GPS GPSLatitudeRef']) + str(tags['GPS GPSLatitude'])
            exifinfo += '<br>  高度值:  　' + str(
                eval(str(tags['GPS GPSAltitude']))) + '米'
            #  print(tags)
            #  print('拍摄时间：', tags['EXIF DateTimeOriginal'])
            #  print('照相机制造商：', tags['Image Make'])
            #  print('照相机型号：', tags['Image Model'])
            #  print('照片尺寸：', tags['EXIF ExifImageWidth'], tags['EXIF ExifImageLength'])
            # print(str(tags['GPS GPSLatitude'].printable))
            # print(str(tags['GPS GPSLongitude'].printable))

            loc = self.locations(str(tags['GPS GPSLongitude']),
                                 str(tags['GPS GPSLatitude']))
            exifinfo += '<br>坐标值:  ' + str(loc)
            exifinfo += "<br>  分辨率:  " + str(
                tags["Image XResolution"]) + " x " + str(
                    tags["Image YResolution"]) + ' dpi'

            self.label.setText(exifinfo)
            self.pbsave.setEnabled(True)

        except:
            self.label.setText("不包含EXIF信息")
            pass

        # loc = self.locations('[106, 41, 52298583/1000000]','[26, 35, 21421051/500000]')
        # print(loc)

    @pyqtSlot()
    def on_pbsave_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        print(imgNamepath)
        self.pbsave.setDisabled(True)

        fontSize = 80
        text = self.label.text()
        liens = text.split('<br>')
        print(liens)
        #画布颜色
        im = Image.open(imgNamepath)
        #im = Image.new("RGB", (480, len(liens)*(fontSize+5)), (255, 0, 0))
        dr = ImageDraw.Draw(im)
        #字体样式，文章结尾我会放上连接
        fontPath = r"C:\Windows\Fonts\simkai.ttf"

        font = ImageFont.truetype(fontPath, fontSize)
        #文字颜色
        n = 0
        for tex in liens:
            n += 100
            dr.text((10, 10 + n), tex.lstrip(), font=font, fill="#485FD3")
        image_name = imgNamepath.split(".")[0]
        img_after = image_name + '_output.png'
        im.save(img_after)

        self.label_2.setScaledContents(True)
        #img = QtGui.QPixmap(imgNamepath).scaled(self.label_2.size())
        img = QtGui.QPixmap(img_after)
        print("img: ", img.width(), img.height())
        if img.width() > img.height():
            self.label_2.setFixedSize(363,
                                      int(img.height() / img.width() * 363))
        else:
            self.label_2.setFixedSize(int(img.width() / img.height() * 363),
                                      363)
        # 在label控件上显示选择的图片
        self.label_2.setPixmap(img)
        self.label_2.repaint()

    def locations(self, eLon, eLat):
        lon = eLon[1:-1].replace(' ', '').replace('/', ',').split(',')
        #'[116, 29, 10533/500]' to [116,29,10533,500]  type==(list)
        lon = float(
            lon[0]) + float(lon[1]) / 60 + float(lon[2]) / float(lon[3]) / 3600
        lat = eLat[1:-1].replace(' ', '').replace('/', ',').split(',')
        lat = float(
            lat[0]) + float(lat[1]) / 60 + float(lat[2]) / float(lat[3]) / 3600

        return [lon, lat]  #经度,纬度,拍摄时间

    @pyqtSlot()
    def on_pbreset_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        self.lineEdit_2.setText("")
        self.label.setText("")
        self.label_2.clear()
        self.pbreset.setDisabled(True)
        self.pbsave.setDisabled(True)
        self.pbread.setDisabled(True)

if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    ImageExif = ImageExifWindow()
    ImageExif.setFixedSize(ImageExif.width(), ImageExif.height())
    ImageExif.show()
    sys.exit(app.exec())
