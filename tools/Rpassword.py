# -*- coding: utf-8 -*-

"""
Module implementing Rpwd.
"""

from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6 import QtGui

from Ui_Rpassword import Ui_Form

import random
import secrets
import string

class Rpwd(QWidget, Ui_Form):
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
        self.setFixedSize(self.width(), self.height())
        self.passwLen.setValidator(QtGui.QIntValidator())
        self.Lcharcbx.setDisabled(True)
    
    @pyqtSlot()
    def on_pushButton_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        
        passlen = int(self.passwLen.text())
        pstr = 'abcdefghijklmnopqrstuvwxyz'
        if self.Ucharcbx.isChecked():
            pstr = pstr + 'ABCDEFGHIJKL MNOPQRSTUVIXYZ'
        if self.Numbercbx.isChecked():
            pstr = pstr + '01234567890'
        if self.Speccbx.isChecked():
            pstr = pstr + '~!@#$%^*<>?'    # "!@#$%^&*()_+~`|}{[]:;?><,./-="  "!#$%&()*+,-./:;<=>?@[\]^_`{|}~"
            # string.punctuation
        prefix = self.prefix.text()
    
        # Spass = ''.join(random.sample(pstr, passlen))
        
        Spass = "".join(secrets.choice(pstr) for _ in range(passlen))
        
        self.getPassword.setPlainText(self.getPassword.toPlainText()+ f'{prefix}{Spass:<20}'+ f'{self.passcheck(Spass):>5}' + '\n')
    
    @pyqtSlot()
    def on_btn_reset_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        self.getPassword.setPlainText('')


    def passcheck(self, password):
        pstrength = 0
        if len(password) >8:
            pstrength += 1
        for p in password:
            if p.isdecimal():
                pstrength += 1
                break
        for p in password:
            if p.isalpha() and p.islower():
                pstrength += 1
                break
        for p in password:
            if p.isalpha() and p.isupper():
                pstrength += 1
                break                    
        for p in password:
            if p in string.punctuation:
                pstrength += 1
                break       
 
        strength = {0: '弱',1: '弱', 2: '弱', 3: '中', 4: '中', 5: '强', 6: '强'}
        return  strength[pstrength]
    
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    rpwd = Rpwd()

    rpwd.show()
    sys.exit(app.exec())
