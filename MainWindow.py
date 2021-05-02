from PyQt5.QtWidgets import QMainWindow, QMessageBox
from ui.MainWindow import Ui_MainWindow


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)
        self.tabFoldersWidget.setMainWindow(self)
        self.tabPlotWidget.setMainWindow(self)
        self.tabMineWidget.setMainWindow(self)
        self.tabWidget.indexOf(self.tabMineWidget)

    def closeEvent(self, event):
        if self.tabMineWidget.mine_process:
            QMessageBox.warning(self, '提示', '请先停止挖矿')
            event.ignore()
            return

        for task in self.tabPlotWidget.tasks:
            if not task.finish:
                QMessageBox.warning(self, '提示', '请先停止Plot任务')
                event.ignore()
                return
