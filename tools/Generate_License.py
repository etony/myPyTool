# -*- coding: utf-8 -*-

"""
Module implementing Ge_Lic.
"""

import sys,time,os
from PyQt6.QtCore import pyqtSlot, QDateTime
from PyQt6.QtWidgets import QDialog

from Ui_generate_license import Ui_Ge_Lic
from PyQt6.QtWidgets import QApplication, QFileDialog
from PyQt6.QtGui import QIntValidator
import qdarkstyle

import json
from datetime import datetime, timedelta
from cryptography.fernet import Fernet

import uuid


from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding

def get_mac_address():


    mac = uuid.getnode()


    return ':'.join(("%012X" % mac)[i:i+2] for i in range(0, 12, 2))

class Ge_Lic(QDialog, Ui_Ge_Lic):
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
        
        self.le_mac.setInputMask('HH:HH:HH:HH:HH:HH;_')
        self.le_mac.setText(get_mac_address())
        
        self.dt_date.setCalendarPopup(True)
        self.now_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        self.dt_date.setDateTime(QDateTime.fromString(self.now_time, 'yyyy-MM-dd hh:mm:ss'))
        # self.le_duration_days.setValidator(QIntValidator().setRange(0, 1096))
        intValidator = QIntValidator()
        intValidator.setRange(1, 100)
        self.le_duration_days.setValidator(intValidator)

    @pyqtSlot()
    def on_pb_ver_clicked(self):
        """
        Slot documentation goes here.
        """
        self.Licfilepath, licType = QFileDialog.getOpenFileName(
            self, "选择存储文件", ".", "*.key;;All Files(*)") 
        
        self.te_info.setText(self.verify_time_limited_license(self.key,self.Licfilepath).strftime("%Y-%m-%d %H:%M:%S"))

    @pyqtSlot()
    def on_pb_create_clicked(self):
        """
        Slot documentation goes here.
        """
        keyfile = os.path.join(self.folderPath, 'License.key')
        self.key = Fernet.generate_key()
        print(self.key)
        print(keyfile)
        mac_address = self.le_mac.text()
        start_date= self.dt_date.text()
        duration_days = self.le_duration_days.text()
        
        self.generate_time_limited_license(mac_address, self.key, start_date, duration_days,keyfile)
        self.te_info.setText('生成授权文件成功！')

    @pyqtSlot()
    def on_pb_path_clicked(self):
        """
        Slot documentation goes here.
        """
        self.folderPath = QFileDialog.getExistingDirectory(
            self, "选择存储文件夹", ".")
        self.le_path.setText(self.folderPath)
        
    def generate_time_limited_license(self,mac_address, key, start_date, duration_days,keyfile):    
    
        fernet = Fernet(key)    
        license_info = {    
            "mac_address": mac_address,    
            "start_date": datetime.now().isoformat(),    
            "duration_days": duration_days
        }
        
        encrypted_info = fernet.encrypt(json.dumps(license_info).encode())
        with open(keyfile, 'wb') as file:
            file.write(encrypted_info)

    def verify_time_limited_license(self,key,Licfilepath):
        
        fernet = Fernet(key)   
        with open(Licfilepath, 'rb') as file:
            encrypted_info = file.read()
        license_info = json.loads(fernet.decrypt(encrypted_info).decode())
        print(license_info)
        start_date = datetime.fromisoformat(license_info['start_date'])
        duration = timedelta(days=int(license_info['duration_days']))

        return  start_date + duration
    
    @pyqtSlot()
    def on_pb_create_key_clicked(self):
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        public_key = private_key.public_key()
        
        # store private key
        pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        with open('private_key.pem', 'wb') as f:
            f.write(pem)
        
        # stroe public key
        pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        with open('public_key.pem', 'wb') as f:
            f.write(pem)


    def decrypt_encrypt(self):
        with open("private_key.pem", "rb") as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None,
                backend=default_backend()
            )

        with open("public_key.pem", "rb") as key_file:
            public_key = serialization.load_pem_public_key(
                key_file.read(),
                backend=default_backend()
            )    
        message = '加密内容'
        encrypted = public_key.encrypt(
            message,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        original_message = private_key.decrypt(
            encrypted,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        print(original_message)

        # https://blog.csdn.net/photon222/article/details/109447327



if __name__ == "__main__":
    # 创建应用程序
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet())  # 默认样式：暗黑样式

    gl = Ge_Lic()
    gl.setWindowTitle("授权文件生成器")
    gl.show()
    # 运行应用
    sys.exit(app.exec())
