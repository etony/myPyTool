# -*- coding: utf-8 -*-

"""
Module implementing BookSearch.
"""

from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QDialog

from .Ui_BooSearch import Ui_Dialog


class BookSearch(QDialog, Ui_Dialog):
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
    def on_pb_search_douban_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        raise NotImplementedError
