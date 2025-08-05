# -*- coding: utf-8 -*-
"""
Module implementing SqlmapUI.
"""

from PyQt6.QtCore import pyqtSlot, Qt
from PyQt6.QtWidgets import QMainWindow, QApplication, QFileDialog

from Ui_sqlmap import Ui_SqlmapUI
from PyQt6.QtGui import QIcon
import subprocess
import os
import platform

class SqlmapUI(QMainWindow, Ui_SqlmapUI):
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
        url = self.le_url.text()
        if len(url.strip()) < 2:
            self.pb_getcommand.setDisabled(True)
        self.str_commad = ""
        self.cbb_tampers.addItem("")
        #dir = os.getcwd() + "/tamper/"
        dir = os.path.join(os.getcwd(), "tamper")
        if os.path.exists(dir):
            self.load_temperfile(dir)
        self.pb_startscan.setDisabled(True)
        self.setWindowIcon(QIcon("gui.ico"))

    @pyqtSlot(bool)
    def on_cb_forms_clicked(self, checked):
        """
        Slot documentation goes here.
        
        @param checked DESCRIPTION
        @type bool
        """
        # TODO: not implemented yet

    @pyqtSlot(bool)
    def on_cb_batch_clicked(self, checked):
        """
        Slot documentation goes here.
        
        @param checked DESCRIPTION
        @type bool
        """
        # TODO: not implemented yet

    @pyqtSlot(bool)
    def on_cb_osshell_clicked(self, checked):
        """
        Slot documentation goes here.
        
        @param checked DESCRIPTION
        @type bool
        """
        # TODO: not implemented yet

    @pyqtSlot(bool)
    def on_cb_random_clicked(self, checked):
        """
        Slot documentation goes here.
        
        @param checked DESCRIPTION
        @type bool
        """
        # TODO: not implemented yet

    @pyqtSlot(bool)
    def on_cb_o_clicked(self, checked):
        """
        Slot documentation goes here.
        
        @param checked DESCRIPTION
        @type bool
        """
        # TODO: not implemented yet

    @pyqtSlot(bool)
    def on_cb_sqlshell_clicked(self, checked):
        """
        Slot documentation goes here.
        
        @param checked DESCRIPTION
        @type bool
        """
        # TODO: not implemented yet

    @pyqtSlot(bool)
    def on_cb_keeplive_clicked(self, checked):
        """
        Slot documentation goes here.
        
        @param checked DESCRIPTION
        @type bool
        """
        # TODO: not implemented yet

    @pyqtSlot(bool)
    def on_cb_level3_clicked(self, checked):
        """
        Slot documentation goes here.
        
        @param checked DESCRIPTION
        @type bool
        """
        # TODO: not implemented yet
        if checked:
            self.cb_level5.setChecked(False)

    @pyqtSlot(bool)
    def on_cb_risk2_clicked(self, checked):
        """
        Slot documentation goes here.
        
        @param checked DESCRIPTION
        @type bool
        """
        # TODO: not implemented yet
        if checked:
            self.cb_risk3.setChecked(False)

    @pyqtSlot(bool)
    def on_cb_level5_clicked(self, checked):
        """
        Slot documentation goes here.
        
        @param checked DESCRIPTION
        @type bool
        """
        # TODO: not implemented yet
        if checked:
            self.cb_level3.setChecked(False)

    @pyqtSlot(bool)
    def on_cb_risk3_clicked(self, checked):
        """
        Slot documentation goes here.
        
        @param checked DESCRIPTION
        @type bool
        """
        # TODO: not implemented yet
        if checked:
            self.cb_risk2.setChecked(False)

    @pyqtSlot(bool)
    def on_cb_banner_clicked(self, checked):
        """
        Slot documentation goes here.
        
        @param checked DESCRIPTION
        @type bool
        """
        # TODO: not implemented yet

    @pyqtSlot(bool)
    def on_cb_dbs_clicked(self, checked):
        """
        Slot documentation goes here.
        
        @param checked DESCRIPTION
        @type bool
        """
        # TODO: not implemented yet

    @pyqtSlot(bool)
    def on_cb_currentuser_clicked(self, checked):
        """
        Slot documentation goes here.
        
        @param checked DESCRIPTION
        @type bool
        """
        # TODO: not implemented yet

    @pyqtSlot(bool)
    def on_cb_currentdb_clicked(self, checked):
        """
        Slot documentation goes here.
        
        @param checked DESCRIPTION
        @type bool
        """
        if checked:
            self.le_dbname.setText("")


    @pyqtSlot(bool)
    def on_cb_tables_clicked(self, checked):
        """
        Slot documentation goes here.
        
        @param checked DESCRIPTION
        @type bool
        """
        if checked:
            self.le_tablename.setText("")

    @pyqtSlot(bool)
    def on_cb_columns_clicked(self, checked):
        """
        Slot documentation goes here.
        
        @param checked DESCRIPTION
        @type bool
        """
        # TODO: not implemented yet

    @pyqtSlot(bool)
    def on_cb_isdba_clicked(self, checked):
        """
        Slot documentation goes here.
        
        @param checked DESCRIPTION
        @type bool
        """
        # TODO: not implemented yet

    @pyqtSlot(bool)
    def on_cb_passwords_clicked(self, checked):
        """
        Slot documentation goes here.
        
        @param checked DESCRIPTION
        @type bool
        """
        # TODO: not implemented yet

    @pyqtSlot(bool)
    def on_cb_privileges_clicked(self, checked):
        """
        Slot documentation goes here.
        
        @param checked DESCRIPTION
        @type bool
        """
        # TODO: not implemented yet

    @pyqtSlot(bool)
    def on_cb_users_clicked(self, checked):
        """
        Slot documentation goes here.
        
        @param checked DESCRIPTION
        @type bool
        """
        # TODO: not implemented yet

    @pyqtSlot(bool)
    def on_cb_roles_clicked(self, checked):
        """
        Slot documentation goes here.
        
        @param checked DESCRIPTION
        @type bool
        """
        # TODO: not implemented yet

    @pyqtSlot(bool)
    def on_cb_mysql_clicked(self, checked):
        """
        Slot documentation goes here.
        
        @param checked DESCRIPTION
        @type bool
        """
        # TODO: not implemented yet
        if checked:
            self.cb_mssql.setChecked(False)
            self.cb_oracle.setChecked(False)

    @pyqtSlot(bool)
    def on_cb_oracle_clicked(self, checked):
        """
        Slot documentation goes here.
        
        @param checked DESCRIPTION
        @type bool
        """
        # TODO: not implemented yet
        if checked:
            self.cb_mysql.setChecked(False)
            self.cb_mssql.setChecked(False)

    @pyqtSlot(bool)
    def on_cb_mssql_clicked(self, checked):
        """
        Slot documentation goes here.
        
        @param checked DESCRIPTION
        @type bool
        """
        # TODO: not implemented yet
        if checked:
            self.cb_oracle.setChecked(False)
            self.cb_mysql.setChecked(False)

    @pyqtSlot(str)
    def on_le_url_textChanged(self, p0):
        """
        Slot documentation goes here.
        
        @param p0 DESCRIPTION
        @type str
        """
        # TODO: not implemented yet
        if len(self.le_url.text().strip()) > 2:
            self.pb_getcommand.setEnabled(True)
        else:
            self.pb_getcommand.setDisabled(True)

    @pyqtSlot()
    def on_pb_getcommand_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        sqlmap = self.le_sqlmap.text().strip()
        self.str_commad = "python " + sqlmap + " -u " + self.le_url.text(
        ) + " "
        if self.cb_batch.isChecked():
            self.str_commad += self.cb_batch.text()
        if self.cb_banner.isChecked():
            self.str_commad += self.cb_banner.text()
        if self.cb_columns.isChecked():
            self.str_commad += self.cb_columns.text()
        if self.cb_currentdb.isChecked():
            self.str_commad += self.cb_currentdb.text()
        if self.cb_currentuser.isChecked():
            self.str_commad += self.cb_currentuser.text()
        if self.cb_dbs.isChecked():
            self.str_commad += self.cb_dbs.text()
        if self.cb_forms.isChecked():
            self.str_commad += self.cb_forms.text()
        if self.cb_isdba.isChecked():
            self.str_commad += self.cb_isdba.text()
        if self.cb_keeplive.isChecked():
            self.str_commad += self.cb_keeplive.text()
        if self.cb_level5.isChecked():
            self.str_commad += self.cb_level5.text()
        if self.cb_level3.isChecked():
            self.str_commad += self.cb_level3.text()
        if self.cb_mssql.isChecked():
            self.str_commad += self.cb_mssql.text()
        if self.cb_mysql.isChecked():
            self.str_commad += self.cb_mysql.text()
        if self.cb_oracle.isChecked():
            self.str_commad += self.cb_oracle.text()
        if self.cb_o.isChecked():
            self.str_commad += self.cb_o.text()
        if self.cb_osshell.isChecked():
            self.str_commad += self.cb_osshell.text()
        if self.cb_passwords.isChecked():
            self.str_commad += self.cb_passwords.text()
        if self.cb_privileges.isChecked():
            self.str_commad += self.cb_privileges.text()
        if self.cb_random.isChecked():
            self.str_commad += self.cb_random.text()
        if self.cb_risk2.isChecked():
            self.str_commad += self.cb_risk2.text()
        if self.cb_risk3.isChecked():
            self.str_commad += self.cb_risk3.text()
        if self.cb_sqlshell.isChecked():
            self.str_commad += self.cb_sqlshell.text()
        if self.cb_tables.isChecked():
            self.str_commad += self.cb_tables.text()
        if self.cb_users.isChecked():
            self.str_commad += self.cb_users.text()
        if self.cb_roles.isChecked():
            self.str_commad += self.cb_roles.text()
            
        str_dbname = self.le_dbname.text().strip()
        str_tablename = self.le_tablename.text().strip()
        str_options = self.le_options.text().strip()

        if len(str_dbname)>=3:
            self.str_commad += '-D '+ str_dbname

        if len(str_tablename):
            self.str_commad += '-T'+ str_tablename
            
        if len(str_options) >= 3:
            self.str_commad += str_options


        self.tb_command.setTextColor(Qt.GlobalColor.blue)
        if self.cbb_tampers.currentIndex() > 0:
            self.str_commad += " --tamper " + self.cbb_tampers.currentText()

        if len(self.le_options.text().strip()) >= 2:
            self.str_commad += self.le_options.text()
        self.tb_command.setText(self.str_commad)
        self.pb_startscan.setEnabled(True)

    @pyqtSlot()
    def on_pb_startscan_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        cmd = self.str_commad
        self.pb_startscan.setDisabled(True)
        print(cmd)
        # p = subprocess.Popen(cmd,
        #                      shell=True,
        #                      stdin=subprocess.PIPE,
        #                      stdout=subprocess.PIPE,
        #                      stderr=subprocess.PIPE)
        SYSTEM_PLATFORM = platform.system()
        if(SYSTEM_PLATFORM == "Linux"):
            os.system("x-terminal-emulator -e '"+ cmd + "'")
        elif (SYSTEM_PLATFORM == "Windows"):
            os.system("start cmd.exe /k " + cmd)
            
        #os.system("start cmd.exe /k " + cmd)
        #os.system("x-terminal-emulator -e '"+ cmd + "'")

    @pyqtSlot()
    def on_pb_selectSqlmap_clicked(self):
        fileName_choose, filetype = QFileDialog.getOpenFileName(
            self,
            "指定sqlmap.py位置",
            os.getcwd(),  # 起始路径
            "Sqlmap File (sqlmap.py);;Python Files (*.py)")
        if fileName_choose != "":
            self.le_sqlmap.setText(fileName_choose)

        dir = os.path.join(os.path.dirname(fileName_choose), "tamper")

        if os.path.exists(dir):
            self.load_temperfile(dir)
        # tampers = [x for x in os.listdir(dir) if x.endswith('.py')]
        # for tamp_list in sorted(tampers):
        #     if tamp_list not in "__init__.py":
        #         self.cbb_tampers.addItem(tamp_list)

    def load_temperfile(self, dir):
        tampers = [x for x in os.listdir(dir) if x.endswith('.py')]
        for tamp_list in sorted(tampers):
            if tamp_list not in "__init__.py":
                self.cbb_tampers.addItem(tamp_list)

    @pyqtSlot(str)
    def on_le_dbname_textChanged(self, p0):
        """
        Slot documentation goes here.

        @param p0 DESCRIPTION
        @type str
        """
        self.cb_currentdb.setChecked(False)

    @pyqtSlot(str)
    def on_le_tablename_textChanged(self, p0):
        """
        Slot documentation goes here.

        @param p0 DESCRIPTION
        @type str
        """
        self.cb_tables.setChecked(False)

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    SqlmapUI = SqlmapUI()
    SqlmapUI.setFixedSize(SqlmapUI.width(), SqlmapUI.height())

    SqlmapUI.show()
    sys.exit(app.exec())
