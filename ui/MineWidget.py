# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Users\peng\Desktop\chia-tools\ui\MineWidget.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MineWidget(object):
    def setupUi(self, MineWidget):
        MineWidget.setObjectName("MineWidget")
        MineWidget.resize(989, 522)
        self.verticalLayout = QtWidgets.QVBoxLayout(MineWidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.label_2 = QtWidgets.QLabel(MineWidget)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_3.addWidget(self.label_2)
        self.editMinerName = QtWidgets.QLineEdit(MineWidget)
        self.editMinerName.setObjectName("editMinerName")
        self.horizontalLayout_3.addWidget(self.editMinerName)
        self.label = QtWidgets.QLabel(MineWidget)
        self.label.setObjectName("label")
        self.horizontalLayout_3.addWidget(self.label)
        self.editApiKey = QtWidgets.QLineEdit(MineWidget)
        self.editApiKey.setObjectName("editApiKey")
        self.horizontalLayout_3.addWidget(self.editApiKey)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem)
        self.label_4 = QtWidgets.QLabel(MineWidget)
        self.label_4.setObjectName("label_4")
        self.horizontalLayout_3.addWidget(self.label_4)
        self.labelCurrentCount = QtWidgets.QLabel(MineWidget)
        self.labelCurrentCount.setObjectName("labelCurrentCount")
        self.horizontalLayout_3.addWidget(self.labelCurrentCount)
        self.label_3 = QtWidgets.QLabel(MineWidget)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout_3.addWidget(self.label_3)
        self.labelCurrentGB = QtWidgets.QLabel(MineWidget)
        self.labelCurrentGB.setObjectName("labelCurrentGB")
        self.horizontalLayout_3.addWidget(self.labelCurrentGB)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem1)
        self.buttonStart = QtWidgets.QPushButton(MineWidget)
        self.buttonStart.setObjectName("buttonStart")
        self.horizontalLayout_3.addWidget(self.buttonStart)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.textEditLog = QtWidgets.QTextEdit(MineWidget)
        self.textEditLog.setObjectName("textEditLog")
        self.verticalLayout.addWidget(self.textEditLog)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.checkBoxAutoStart = QtWidgets.QCheckBox(MineWidget)
        self.checkBoxAutoStart.setObjectName("checkBoxAutoStart")
        self.horizontalLayout.addWidget(self.checkBoxAutoStart)
        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem2)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(MineWidget)
        QtCore.QMetaObject.connectSlotsByName(MineWidget)

    def retranslateUi(self, MineWidget):
        _translate = QtCore.QCoreApplication.translate
        MineWidget.setWindowTitle(_translate("MineWidget", "Form"))
        self.label_2.setText(_translate("MineWidget", "????????????"))
        self.label.setText(_translate("MineWidget", "API Key"))
        self.label_4.setText(_translate("MineWidget", "Plot????????????"))
        self.labelCurrentCount.setText(_translate("MineWidget", "10???"))
        self.label_3.setText(_translate("MineWidget", "?????????"))
        self.labelCurrentGB.setText(_translate("MineWidget", "0GB"))
        self.buttonStart.setText(_translate("MineWidget", "????????????"))
        self.checkBoxAutoStart.setText(_translate("MineWidget", "??????????????????"))
