from PyQt5.Qt import pyqtSignal
from PyQt5.Qt import QThread
import os


class DiskOperation(QThread):
    signalListDir = pyqtSignal()

    def __init__(self):
        super(DiskOperation, self).__init__()

    def run(self):
        pass
