# -*- coding: utf-8 -*-
"""
Module implementing Image-Conver.
"""

from PyQt6.QtCore import pyqtSlot, Qt
from PyQt6.QtWidgets import QMainWindow, QFileDialog

from Ui_imageconver import Ui_MainWindow
from PyQt6 import QtCore, QtGui, QtWidgets
from model import Generator
import torch
from torchvision.transforms.functional import to_tensor, to_pil_image
from PIL import Image
import cv2


class Image_Conver(QMainWindow, Ui_MainWindow):
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
        self.pbstart.setDisabled(True)
        self.pbsave.setDisabled(True)


    @pyqtSlot()
    def on_pbselect_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        global imgNamepath
        imgNamepath, imgType = QFileDialog.getOpenFileName(
            self, "选择图片", "D:\\", "*.png;;*.jpg;;All Files(*)")

        if imgNamepath != "":
            self.label_2.setScaledContents(True)
            #img = QtGui.QPixmap(imgNamepath).scaled(self.label_2.size())
            img = QtGui.QPixmap(imgNamepath)
            print("img: ", img.width(), img.height())
            if img.width() > img.height():
                self.label_2.setFixedSize(363, int(img.height()/img.width()*363))
            else:
                self.label_2.setFixedSize(int(img.width()/img.height()*363), 363)
            # 在label控件上显示选择的图片
            self.label_2.setPixmap(img)
            self.label_2.repaint()
            # 显示所选图片的路径
            self.lineEdit_2.setText(imgNamepath)
            self.pbstart.setEnabled(True)


    @pyqtSlot()
    def on_pbstart_clicked(self):
        """
        Slot documentation goes here.
        """
        self.label.setText("开始加载图片.......")
        if self.rbtn_dm.isChecked():
            net = Generator()
            net.load_state_dict(
                torch.load("./torch/face_paint_512_v2.pt", map_location="cpu"))
            net.to("cpu").eval()
            image = self.load_image(imgNamepath)
            print("开始加载图片.......")

            with torch.no_grad():
                image = to_tensor(image).unsqueeze(0) * 2 - 1
                out = net(image.to("cpu"), False).cpu()
                out = out.squeeze(0).clip(-1, 1) * 0.5 + 0.5
                out = to_pil_image(out)
            image_name = imgNamepath.split(".")[0]
            out.save(image_name + "_animegan" + ".png")
            img_after = image_name + '_animegan.png'
            print("图片保存成功！！")

        if self.rbtn_sm.isChecked():
            img = cv2.imread(imgNamepath)
            # img = cv2.resize(img, dsize=(768, 1080))
            gray_image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            inverted_gray_image = cv2.bitwise_not(gray_image)
            blurred_inverted_gray_image = cv2.GaussianBlur(
                inverted_gray_image, (111, 111), 0)
            image_name = imgNamepath.split(".")[0]
            invblur_img = cv2.bitwise_not(blurred_inverted_gray_image)
            sketch_img_test = cv2.divide(gray_image, invblur_img, scale=256.0)
            cv2.imwrite(image_name + '_sumiao.png', sketch_img_test)
            img_after = image_name + '_sumiao.png'
            print("图片保存成功！！")

        #imgShow = QtGui.QPixmap(img_after).scaled(self.label.size())
        imgShow = QtGui.QPixmap(img_after)
        if imgShow.width() > imgShow.height():
            self.label.setFixedSize(363, int(imgShow.height() / imgShow.width() * 363))
        else:
            self.label.setFixedSize(int(imgShow.width() / imgShow.height() * 363), 363)
        # self.label.setFixedSize(imgShow.width(), imgShow.height())
        self.label.setScaledContents(True)
        self.label.setPixmap(imgShow)
        print(f"image saved: {image_name}")
        self.pbsave.setEnabled(True)

    @pyqtSlot()
    def on_pbsave_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        img = self.label.pixmap().toImage()
        fpath, ftype = QFileDialog.getSaveFileName(
            self, "保存", "D:\\", "*.jpg;;*.png;;All Files(*)")
        img.save(fpath)

    def load_image(self, image_path, x32=False):
        img = Image.open(image_path).convert("RGB")
        if x32:

            def to_32s(x):
                return 256 if x < 256 else x - x % 32

            w, h = img.size
            img = img.resize((to_32s(w), to_32s(h)))
        return img


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Imageconver = Image_Conver()
    Imageconver.setFixedSize(Imageconver.width(),Imageconver.height())

    Imageconver.show()
    sys.exit(app.exec())
