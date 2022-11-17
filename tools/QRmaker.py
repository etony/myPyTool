# -*- coding: utf-8 -*-

"""
Module implementing QRmaker.
"""

from PyQt6.QtCore import pyqtSlot, QSize, Qt, QRectF, QSizeF
from PyQt6.QtWidgets import QMainWindow, QApplication, QFileDialog, QMessageBox
from PyQt6.QtGui import QImage, QPixmap, QPainter,QMovie,QPainterPath

from Ui_QRmaker import Ui_MainWindow

from MyQR import myqr
import qrcode
from PIL import ImageQt, Image
import os
import cv2
import numpy as np

import logging
import datetime


class QRmaker(QMainWindow, Ui_MainWindow):
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

        filename = os.path.basename(sys.argv[0])
        self.LOG = logging.getLogger(filename)
        logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                            level=logging.INFO)

    @pyqtSlot()
    def on_pb_load_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        fpath, ftype = QFileDialog.getOpenFileName(
            self, "打开", os.getcwd(), "Image Files (*.png *.jpg *.bmp)")

        if os.path.exists(fpath):
            image = QPixmap(fpath)

            self.lab_image.setPixmap(image)
            #img = cv2.imread(fpath)
            image = ImageQt.fromqimage(image.toImage())
            img = cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR)

            det = cv2.QRCodeDetector()
            val, pts, st_code = det.detectAndDecode(img)
            self.te_out.setPlainText(val)
            self.LOG.info("二维码加载完毕！")

    @pyqtSlot()
    def on_pb_read_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        image = self.lab_image.pixmap().toImage()

        image = ImageQt.fromqimage(image)
        img = cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR)
        det = cv2.QRCodeDetector()
        val, pts, st_code = det.detectAndDecode(img)
        self.te_out.setPlainText(val)
        self.LOG.info("二维码读取完毕！")

    @pyqtSlot()
    def on_pb_create_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet

        qrtxt = self.te_info.toPlainText().strip()
        if len(qrtxt) == 0:
            QMessageBox(QMessageBox.Icon.Warning, '警告', '请输入二维码信息！',
                        QMessageBox.StandardButton.Ok).exec()
            self.LOG.warn("未输入二维码信息！")
        else:
            qr = qrcode.QRCode(version=5, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=8,
                               border=4)
            qr.add_data(qrtxt)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")

            self.lab_image.setPixmap(img.toqpixmap())
            self.LOG.info("二维码生成完毕！")

    @pyqtSlot()
    def on_pb_background_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        image = self.lab_image.pixmap()
        self.LOG.info(f'pixmap type  {type(image)}')
        w = image.width()
        h = image.height()
        self.LOG.info(f'pixmap   {w}:{h}')
        image2 = QPixmap("logo.png")
        logo_w = image2.width()
        logo_h = image2.height()
        self.LOG.info(f'logopixmap   {logo_w}:{logo_h}')
        if logo_w > 48 or logo_h > 48:
            if logo_h > logo_w:
                logo_w = int(logo_w*48/logo_h)
                logo_h = 48
            else:
                logo_h = int(logo_h*48/logo_w)
                logo_w = 48
            image2 = image2.scaled(QSize(
                logo_w, logo_h), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

        self.LOG.info(
            f'logopixmap scaled   {image2.width()}:{image2.height()}')

        painter = QPainter(image)
        painter.begin(self)
        #painter.drawImage(0, 0, image.toImage())
        ####
        
        # radius = 30

        # r = QRectF()
        # r.setSize(radius * QSizeF(1, 1))
        # r.moveCenter(QPixmap("logo.png").rect().center())
        # path = QPainterPath()
        # path.addEllipse(r)

        # painter.setRenderHints(
        #     QPainter.Antialiasing | QPainter.SmoothPixmapTransform
        # )
        # painter.setClipPath(path, Qt.IntersectClip)
        
        
        
        ####
        painter.drawImage(int((w - logo_w) / 2),
                          int((h - logo_h) / 2), image2.toImage())
        painter.end()
        painter.save()
        self.lab_image.setPixmap(image)

    @pyqtSlot()
    def on_pb_logo_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        image = ImageQt.fromqimage(self.lab_image.pixmap().toImage())
        w, h = image.size
        logo = Image.open("logo.png")

        logo_w, logo_h = logo.size
        if logo_w > 48 or logo_h > 48:
            if logo_h > logo_w:
                logo_w = int(logo_w*48/logo_h)
                logo_h = 48
            else:
                logo_h = int(logo_h*48/logo_w)
                logo_w = 48

        self.LOG.info(f"logo resize: {logo_w}   {logo_h}")
        logo = logo.resize((logo_w, logo_h), Image.ANTIALIAS)

        self.LOG.info(f'{w}:{h}  {logo_w}:{logo_h}')
        l_w = int((w - logo_w) / 2)
        l_h = int((h - logo_h) / 2)
        logo = logo.convert("RGBA")
        image.paste(logo, (l_w, l_h), logo)

        self.lab_image.setScaledContents(True)
        self.LOG.info(f"合成image type: {type(image)}")

        image.save("combine_QR_tmp.jpg")
        images = QPixmap("combine_QR_tmp.jpg")

        self.lab_image.setPixmap(images)
        self.lab_image.setScaledContents(True)
        self.LOG.info("再次加载完毕！")

    @pyqtSlot()
    def on_pb_save_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        img = self.lab_image.pixmap().toImage()
        nowtime = datetime.datetime.now().strftime("_%y-%m-%d")
        fpath, ftype = QFileDialog.getSaveFileName(
            self, "保存", os.path.join(os.getcwd(), nowtime+"_QR.jpg"),  "*.jpg;;*.png")

        if ftype:
            img.save(fpath)

    @pyqtSlot()
    def on_pb_addback_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        back = cv2.imread("background.jpg")

        ##################
        R = self.lab_image.pixmap().height()

        x, y = back.shape[:2]

        mask = np.zeros(back.shape[:2], dtype=np.uint8)

        mask = cv2.circle(mask, (int(y/2), int(x/2)),
                          int(R/2), (255, 255, 255), -1)
        back = cv2.add(back, np.zeros(
            np.shape(back), dtype=np.uint8), mask=mask)

        back = cv2.bitwise_and(back, back, mask=mask)
        x, y = back.shape[:2]

        # 白色
        white_px = np.asarray([255, 255, 255])
        # 黑色
        black_px = np.asarray([0, 0, 0])

        for h in range(x):
            for w in range(y):
                if all(back[h][w] == black_px):
                    back[h][w] = white_px

        ##################

        self.LOG.info(
            f"background image shape: {back.shape}, size: {back.size}")
        self.LOG.info(f"background image info: {back[500,500]}")

        # 设置边界框
        back = cv2.copyMakeBorder(
            back, 120, 120, 220, 220, cv2.BORDER_CONSTANT, value=(255, 255, 255))

        front = self.lab_image.pixmap().toImage()

        temp_shape = (front.height(), front.bytesPerLine()*8//front.depth())
        temp_shape += (4,)
        ptr = front.bits()
        ptr.setsize(front.bytesPerLine()*front.height())
        result = np.array(ptr, dtype=np.uint8).reshape(temp_shape)
        result = result[..., :3]

        self.LOG.info(f"front image: {type(result)}")
        self.LOG.info(f"back image: {type(back)}")

        combine = cv2.addWeighted(cv2.resize(
            result, (800, 800)), 0.7, cv2.resize(back, (800, 800)), 0.5, 5)

        img_rgb = cv2.cvtColor(combine, cv2.COLOR_RGB2BGR)
        QtImg = QImage(
            img_rgb.data, img_rgb.shape[1], img_rgb.shape[0], QImage.Format.Format_RGB888)
        self.lab_image.setPixmap(QPixmap.fromImage(QtImg))

    @pyqtSlot()
    def on_pb_anim_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        fpath, ftype = QFileDialog.getOpenFileName(
            self, "选择动图", os.getcwd(), "Image Files (*.gif)")

        if os.path.exists(fpath):
            self.gif = fpath

    @pyqtSlot()
    def on_pb_create_anim_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        if not os.path.exists(self.gif):
            self.gif = "back.gif"

        x, y, z = myqr.run(self.te_info.toPlainText().strip(), version=3, picture=(
            self.gif), save_name=("123456.gif"), colorized=True)
        
        self.LOG.info(f'myQR GIF 返回值：{x} {y} {z}')

        self.gif = QMovie("123456.gif")
        self.lab_image.setMovie(self.gif)
        self.gif.start()

    @pyqtSlot()
    def on_pb_save_anim_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        img = self.lab_image.movie()
        nowtime = datetime.datetime.now().strftime("_%y-%m-%d")
        fpath, ftype = QFileDialog.getSaveFileName(
            self, "保存", os.path.join(os.getcwd(), nowtime+"_QR.gif"),  "*.gif;;*.png")

        if ftype:
            img.save(fpath)


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)

    qRmaker = QRmaker()
    qRmaker.show()
    sys.exit(app.exec())


# https://blog.csdn.net/Time_D/article/details/88822258
# https://xxmdmst.blog.csdn.net/article/details/112172580
# python opencv把一张图片嵌入（叠加）到另一张图片上 https://blog.csdn.net/mao_hui_fei/article/details/106596807
# https://blog.csdn.net/cungudafa/article/details/85871871
# https://www.cnblogs.com/zhaoyingjie/p/14699837.html
# https://cloud.tencent.com/developer/ask/sof/1156847
