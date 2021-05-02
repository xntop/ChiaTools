# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Users\peng\Desktop\chia-tools\ui\FoldersWidget.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_FoldersWidget(object):
    def setupUi(self, FoldersWidget):
        FoldersWidget.setObjectName("FoldersWidget")
        FoldersWidget.resize(1168, 601)
        self.verticalLayout = QtWidgets.QVBoxLayout(FoldersWidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.groupBox = QtWidgets.QGroupBox(FoldersWidget)
        self.groupBox.setObjectName("groupBox")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.groupBox)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.treeSSD = QtWidgets.QTreeWidget(self.groupBox)
        self.treeSSD.setRootIsDecorated(False)
        self.treeSSD.setObjectName("treeSSD")
        self.verticalLayout_3.addWidget(self.treeSSD)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.buttonAddSSDFolder = QtWidgets.QPushButton(self.groupBox)
        self.buttonAddSSDFolder.setObjectName("buttonAddSSDFolder")
        self.horizontalLayout.addWidget(self.buttonAddSSDFolder)
        self.buttonRemoveSSDFolder = QtWidgets.QPushButton(self.groupBox)
        self.buttonRemoveSSDFolder.setObjectName("buttonRemoveSSDFolder")
        self.horizontalLayout.addWidget(self.buttonRemoveSSDFolder)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.verticalLayout_3.addLayout(self.horizontalLayout)
        self.verticalLayout.addWidget(self.groupBox)
        self.groupBox_2 = QtWidgets.QGroupBox(FoldersWidget)
        self.groupBox_2.setObjectName("groupBox_2")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.groupBox_2)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.treeHDD = QtWidgets.QTreeWidget(self.groupBox_2)
        self.treeHDD.setRootIsDecorated(False)
        self.treeHDD.setObjectName("treeHDD")
        self.treeHDD.headerItem().setTextAlignment(0, QtCore.Qt.AlignCenter)
        self.verticalLayout_4.addWidget(self.treeHDD)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem2)
        self.buttonAddHDDFolder = QtWidgets.QPushButton(self.groupBox_2)
        self.buttonAddHDDFolder.setObjectName("buttonAddHDDFolder")
        self.horizontalLayout_2.addWidget(self.buttonAddHDDFolder)
        self.buttonRemoveHDDFolder = QtWidgets.QPushButton(self.groupBox_2)
        self.buttonRemoveHDDFolder.setObjectName("buttonRemoveHDDFolder")
        self.horizontalLayout_2.addWidget(self.buttonRemoveHDDFolder)
        spacerItem3 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem3)
        self.verticalLayout_4.addLayout(self.horizontalLayout_2)
        self.verticalLayout.addWidget(self.groupBox_2)

        self.retranslateUi(FoldersWidget)
        QtCore.QMetaObject.connectSlotsByName(FoldersWidget)

    def retranslateUi(self, FoldersWidget):
        _translate = QtCore.QCoreApplication.translate
        FoldersWidget.setWindowTitle(_translate("FoldersWidget", "Form"))
        self.groupBox.setTitle(_translate("FoldersWidget", "临时目录（固态硬盘）"))
        self.treeSSD.headerItem().setText(0, _translate("FoldersWidget", "目录"))
        self.treeSSD.headerItem().setText(1, _translate("FoldersWidget", "已使用"))
        self.treeSSD.headerItem().setText(2, _translate("FoldersWidget", "剩余"))
        self.treeSSD.headerItem().setText(3, _translate("FoldersWidget", "总容量"))
        self.treeSSD.headerItem().setText(4, _translate("FoldersWidget", "使用情况"))
        self.buttonAddSSDFolder.setText(_translate("FoldersWidget", "添加目录"))
        self.buttonRemoveSSDFolder.setText(_translate("FoldersWidget", "删除目录"))
        self.groupBox_2.setTitle(_translate("FoldersWidget", "最终目录（机械硬盘）"))
        self.treeHDD.headerItem().setText(0, _translate("FoldersWidget", "挖矿"))
        self.treeHDD.headerItem().setText(1, _translate("FoldersWidget", "目录"))
        self.treeHDD.headerItem().setText(2, _translate("FoldersWidget", "已使用"))
        self.treeHDD.headerItem().setText(3, _translate("FoldersWidget", "剩余"))
        self.treeHDD.headerItem().setText(4, _translate("FoldersWidget", "总容量"))
        self.treeHDD.headerItem().setText(5, _translate("FoldersWidget", "使用情况"))
        self.buttonAddHDDFolder.setText(_translate("FoldersWidget", "添加目录"))
        self.buttonRemoveHDDFolder.setText(_translate("FoldersWidget", "删除目录"))
