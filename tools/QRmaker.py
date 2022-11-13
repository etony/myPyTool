# -*- coding: utf-8 -*-

"""
Module implementing QRmaker.
"""

from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QMainWindow, QApplication,QFileDialog, QMessageBox
from PyQt6.QtGui import QImage,QPixmap,QPainter

from Ui_QRmaker import Ui_MainWindow

from MyQR import myqr
import qrcode
from PIL import ImageQt,Image
import os
import cv2
import numpy as np

import logging






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
            img= cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR)

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
        qr = qrcode.QRCode(version=1,error_correction=qrcode.constants.ERROR_CORRECT_L,box_size=10,
                           border=4)
        qrtxt = self.te_info.toPlainText().strip()
        qr.add_data(qrtxt)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black",back_color="white")

        self.lab_image.setPixmap(img.toqpixmap())
        self.LOG.info("二维码生成完毕！")
        

    @pyqtSlot()
    def on_pb_background_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        image = self.lab_image.pixmap()
        self.LOG.info(f'pixmap   {type(image)}')
        w = image.width()
        h = image.height()
        self.LOG.info(f'pixmap   {w}:{h}')
        image2 = QPixmap("logo.png")
        logo_w = image2.width()
        logo_h = image2.height()
        self.LOG.info(f'logopixmap   {logo_w}:{logo_h}')
        
        painter = QPainter(image)
        painter.begin(self)
        painter.drawImage(0, 0, image.toImage())
        painter.drawImage(int((w - logo_w) / 2), int((h - logo_h) / 2), image2.toImage())    
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
        w,h = image.size
        logo = Image.open("logo.png") 
        logo_w, logo_h = logo.size
        
        self.LOG.info(f'{w}:{h}  {logo_w}:{logo_h}')
        l_w = int((w - logo_w) / 2)
        l_h = int((h - logo_h) / 2)
        logo = logo.convert("RGBA")
        image.paste(logo, (l_w, l_h), logo)
        
        self.lab_image.setScaledContents(True)
        image.save("rrrrrrrrrrrr.jpg")
        images = QPixmap("rrrrrrrrrrrr.jpg")

        self.lab_image.setPixmap(images)
        self.lab_image.setScaledContents(True)
        self.LOG.info("再次加载完毕！")
        
        
        
        
        

    @pyqtSlot()
    def on_pb_save_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        raise NotImplementedError

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