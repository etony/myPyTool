# -*- coding: utf-8 -*-

"""
Module implementing Rpwd.
"""

from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6 import QtGui

from Ui_Rpassword import Ui_Form

import random

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
            pstr = pstr + '~!@#$%^*<>?'
        prefix = self.prefix.text()
    
        Spass = ''.join(random.sample(pstr, passlen))
        
        self.getPassword.setPlainText(self.getPassword.toPlainText()+prefix+Spass+'\n')
    
    @pyqtSlot()
    def on_btn_reset_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        self.getPassword.setPlainText('')

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    rpwd = Rpwd()

    rpwd.show()
    sys.exit(app.exec())
