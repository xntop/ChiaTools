from PyQt5.QtWidgets import QDialog, QMessageBox
from ui.CreatePlotDialog import Ui_CreatePlotDialog
from core.plot import PlotTask, PlotSubTask
from config import get_config, save_config
import os
from utils import make_name, size_to_str
from datetime import datetime
import psutil
from core import is_debug


class CreatePlotDialog(QDialog, Ui_CreatePlotDialog):
    def __init__(self, task: PlotTask=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)

        self.buttonBox.button(self.buttonBox.Ok).setText('创建')
        self.buttonBox.button(self.buttonBox.Cancel).setText('取消')
        self.checkBoxSpecifyCount.stateChanged.connect(self.checkSpecifyCount)

        self.modify = False

        if task:
            self.task = task
            self.modify = True

            self.comboSSD.addItem(task.ssd_folder, task.ssd_folder)
            self.comboSSD.setDisabled(True)

            self.comboHDD.addItem(task.hdd_folder, task.hdd_folder)
            self.comboHDD.setDisabled(True)

            self.editFpk.setPlainText(task.fpk)
            self.editFpk.setDisabled(True)
            self.editPpk.setPlainText(task.ppk)
            self.editPpk.setDisabled(True)

            self.checkBoxSpecifyCount.setChecked(task.specify_count)
            self.checkBoxSpecifyCount.setDisabled(True)
            self.spinNumber.setValue(task.count)
            self.spinNumber.setDisabled(True)

            self.spinThreadNum.setValue(task.number_of_thread)
            self.spinMemory.setValue(task.memory_size)

            self.timeEditDelay.setDisabled(True)

            self.setWindowTitle('编辑P图任务')

        else:
            self.task = PlotTask()
            config = get_config()
            for ssd_folder in config['ssd_folders']:
                text = ssd_folder
                if os.path.exists(ssd_folder):
                    usage = psutil.disk_usage(ssd_folder)
                    text += f" ({size_to_str(usage.free)}空闲)"
                else:
                    text += " (不存在)"
                self.comboSSD.addItem(text, ssd_folder)

            for hdd_folder_obj in config['hdd_folders']:
                folder = hdd_folder_obj['folder']
                text = folder
                if os.path.exists(folder):
                    usage = psutil.disk_usage(folder)
                    text += f" ({size_to_str(usage.free)}空闲)"
                else:
                    text += " (不存在)"
                self.comboHDD.addItem(text, folder)

            if 'fpk' in config:
                self.editFpk.setPlainText(config['fpk'])

            if 'ppk' in config:
                self.editPpk.setPlainText(config['ppk'])

            if 'num' in config:
                self.spinNumber.setValue(config['num'])

            if 'thread_num' in config:
                self.spinThreadNum.setValue(config['thread_num'])

            if 'memory_size' in config:
                self.spinMemory.setValue(config['memory_size'])

            if 'specify_count' in config:
                self.checkBoxSpecifyCount.setChecked(config['specify_count'])
                if config['specify_count']:
                    self.spinNumber.setDisabled(False)

    def checkSpecifyCount(self):
        self.spinNumber.setDisabled(not self.checkBoxSpecifyCount.isChecked())

    def accept(self) -> None:
        if self.modify:
            thread_num = self.spinThreadNum.value()
            memory_size = self.spinMemory.value()

            self.task.number_of_thread = thread_num
            self.task.memory_size = memory_size
            super().accept()
            return
        fpk = self.editFpk.toPlainText()
        ppk = self.editPpk.toPlainText()

        ssd_folder = self.comboSSD.currentData()
        hdd_folder = self.comboHDD.currentData()

        delayTime = self.timeEditDelay.time()
        delay = delayTime.hour() * 60*60 + delayTime.minute() * 60 + delayTime.second()

        specify_count = self.checkBoxSpecifyCount.isChecked()
        number = self.spinNumber.value()
        thread_num = self.spinThreadNum.value()
        memory_size = self.spinMemory.value()

        if not os.path.exists(ssd_folder):
            QMessageBox.information(self, '提示', '临时目录不存在')
            return

        if not os.path.exists(hdd_folder):
            QMessageBox.information(self, '提示', '最终目录不存在')
            return

        if not fpk:
            QMessageBox.information(self, '提示', '请输入fpk')
            return

        if not ppk:
            QMessageBox.information(self, '提示', '请输入ppk')
            return

        if not specify_count:
            number = 1

        config = get_config()

        config['fpk'] = fpk
        config['ppk'] = ppk
        config['specify_count'] = specify_count
        config['num'] = number
        config['thread_num'] = thread_num
        config['memory_size'] = memory_size

        save_config()

        temporary_folder = os.path.join(ssd_folder, make_name(12))
        temporary_folder = temporary_folder.replace('\\', '/')

        try:
            os.mkdir(temporary_folder)
        except:
            QMessageBox.information(self, '提示', '创建临时目录失败 %s' % temporary_folder)
            return

        ssd_usage = psutil.disk_usage(ssd_folder)
        hdd_usage = psutil.disk_usage(hdd_folder)

        if not is_debug() and ssd_usage.free < 2**30*332:
            QMessageBox.information(self, '提示', '临时目录的空间不够332G')
            return
        if not is_debug() and hdd_usage.free < 2**30*102:
            QMessageBox.information(self, '提示', '最终目录的空间不够101G')
            return

        self.task.create_time = datetime.now()
        self.task.fpk = fpk
        self.task.ppk = ppk
        self.task.ssd_folder = ssd_folder
        self.task.hdd_folder = hdd_folder
        self.task.temporary_folder = temporary_folder
        self.task.specify_count = specify_count
        self.task.count = number
        self.task.number_of_thread = thread_num
        self.task.memory_size = memory_size
        self.task.delay_seconds = delay

        if specify_count:
            for i in range(number):
                self.task.sub_tasks.append(PlotSubTask(i))
        else:
            self.task.sub_tasks.append(PlotSubTask(0))

        super().accept()
