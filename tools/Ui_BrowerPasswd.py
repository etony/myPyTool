# Form implementation generated from reading ui file 'D:\work\GIT\Python-Study\tools\BrowerPasswd.ui'
#
# Created by: PyQt6 UI code generator 6.5.0
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(863, 612)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        self.centralwidget = QtWidgets.QWidget(parent=MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.tv_namepasswd = QtWidgets.QTableView(parent=self.centralwidget)
        self.tv_namepasswd.setGeometry(QtCore.QRect(10, 60, 843, 501))
        self.tv_namepasswd.setObjectName("tv_namepasswd")
        self.tv_namepasswd.verticalHeader().setVisible(False)
        self.layoutWidget = QtWidgets.QWidget(parent=self.centralwidget)
        self.layoutWidget.setGeometry(QtCore.QRect(10, 10, 841, 26))
        self.layoutWidget.setObjectName("layoutWidget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.layoutWidget)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtWidgets.QLabel(parent=self.layoutWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.cb_brower = QtWidgets.QComboBox(parent=self.layoutWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cb_brower.sizePolicy().hasHeightForWidth())
        self.cb_brower.setSizePolicy(sizePolicy)
        self.cb_brower.setEditable(False)
        self.cb_brower.setObjectName("cb_brower")
        self.cb_brower.addItem("")
        self.cb_brower.addItem("")
        self.cb_brower.addItem("")
        self.horizontalLayout.addWidget(self.cb_brower)
        self.le_askpass = QtWidgets.QLineEdit(parent=self.layoutWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.le_askpass.sizePolicy().hasHeightForWidth())
        self.le_askpass.setSizePolicy(sizePolicy)
        self.le_askpass.setObjectName("le_askpass")
        self.horizontalLayout.addWidget(self.le_askpass)
        self.pb_getit = QtWidgets.QPushButton(parent=self.layoutWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pb_getit.sizePolicy().hasHeightForWidth())
        self.pb_getit.setSizePolicy(sizePolicy)
        self.pb_getit.setObjectName("pb_getit")
        self.horizontalLayout.addWidget(self.pb_getit)
        self.pb_export = QtWidgets.QPushButton(parent=self.layoutWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pb_export.sizePolicy().hasHeightForWidth())
        self.pb_export.setSizePolicy(sizePolicy)
        self.pb_export.setObjectName("pb_export")
        self.horizontalLayout.addWidget(self.pb_export)
        self.line = QtWidgets.QFrame(parent=self.layoutWidget)
        self.line.setFrameShape(QtWidgets.QFrame.Shape.VLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        self.line.setObjectName("line")
        self.horizontalLayout.addWidget(self.line)
        self.le_search = QtWidgets.QLineEdit(parent=self.layoutWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.le_search.sizePolicy().hasHeightForWidth())
        self.le_search.setSizePolicy(sizePolicy)
        self.le_search.setObjectName("le_search")
        self.horizontalLayout.addWidget(self.le_search)
        self.pb_search = QtWidgets.QPushButton(parent=self.layoutWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pb_search.sizePolicy().hasHeightForWidth())
        self.pb_search.setSizePolicy(sizePolicy)
        self.pb_search.setObjectName("pb_search")
        self.horizontalLayout.addWidget(self.pb_search)
        self.pb_reset = QtWidgets.QPushButton(parent=self.layoutWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pb_reset.sizePolicy().hasHeightForWidth())
        self.pb_reset.setSizePolicy(sizePolicy)
        self.pb_reset.setObjectName("pb_reset")
        self.horizontalLayout.addWidget(self.pb_reset)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(parent=MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 863, 22))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(parent=MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "浏览器密码查看器"))
        self.label.setText(_translate("MainWindow", "浏览器："))
        self.cb_brower.setToolTip(_translate("MainWindow", "选择要查询的浏览器"))
        self.cb_brower.setItemText(0, _translate("MainWindow", "--- Chrome ---"))
        self.cb_brower.setItemText(1, _translate("MainWindow", "--- Edge ---"))
        self.cb_brower.setItemText(2, _translate("MainWindow", "--- Firefox ---"))
        self.le_askpass.setToolTip(_translate("MainWindow", "填入保护密码(Master password)"))
        self.pb_getit.setToolTip(_translate("MainWindow", "查询"))
        self.pb_getit.setText(_translate("MainWindow", "Go!"))
        self.pb_export.setToolTip(_translate("MainWindow", "导出查询内容到文件"))
        self.pb_export.setText(_translate("MainWindow", "导    出"))
        self.le_search.setToolTip(_translate("MainWindow", "<html><head/><body><p>仅在当前显示内容中查找。</p></body></html>"))
        self.pb_search.setText(_translate("MainWindow", "查    找"))
        self.pb_reset.setText(_translate("MainWindow", "重   置"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec())
