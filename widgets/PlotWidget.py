from PyQt5.QtWidgets import QWidget, QTreeWidgetItem, QHeaderView, QProgressBar, QMessageBox, QMenu
from PyQt5.Qt import QBrush, QColor, QModelIndex, QTimerEvent, QCursor
from PyQt5.QtCore import Qt
from ui.PlotWidget import Ui_PlotWidget
from config import save_config, get_config
from utils import size_to_str, delta_to_str, seconds_to_str
from datetime import datetime, timedelta
from core.plot import PlotTask, PlotSubTask, PlotWorker
from CreatePlotDialog import CreatePlotDialog
from TaskOutputDialog import TaskOutputDialog
import os
import pickle
from subprocess import run
from core import BASE_DIR
import threading
import platform


class PlotWidget(QWidget, Ui_PlotWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)

        self.main_window = None

        self.treePlot.header().setSectionResizeMode(QHeaderView.ResizeToContents)

        self.tasks: [PlotTask] = []
        self.workers = []
        self.task_lock = threading.Lock()

        self.outputDialogs = []

        self.loadTasks()

        self.treePlot.doubleClicked.connect(self.showTaskOutput)
        self.treePlot.expanded.connect(self.onExpanded)
        self.treePlot.collapsed.connect(self.onCollapsed)
        self.treePlot.setContextMenuPolicy(Qt.CustomContextMenu)
        self.treePlot.customContextMenuRequested.connect(self.showTaskMenu)

        self.checkBoxPhase1Limit.stateChanged.connect(self.checkPhase1Limit)
        self.checkBoxTotalLimit.stateChanged.connect(self.checkTotalLimit)
        self.checkBoxAutoRestartMine.stateChanged.connect(self.checkAutoRestartMine)
        self.spinBoxPhase1Count.valueChanged.connect(self.changePhase1LimitCount)
        self.spinBoxTotalCount.valueChanged.connect(self.changeTotalLimitCount)

        self.buttonCreatePlot.clicked.connect(self.clickCreatePlot)

        self.timerIdUpdateTime = self.startTimer(1000)

        config = get_config()

        if 'total_limit' in config:
            self.checkBoxTotalLimit.setChecked(config['total_limit'])
        if 'phase1_limit' in config:
            self.checkBoxPhase1Limit.setChecked(config['phase1_limit'])

        if 'total_limit_count' in config:
            self.spinBoxTotalCount.setValue(config['total_limit_count'])

        if 'phase1_limit_count' in config:
            self.spinBoxPhase1Count.setValue(config['phase1_limit_count'])

        if 'auto_restart_mine' in config:
            self.checkBoxAutoRestartMine.setChecked(config['auto_restart_mine'])

    def checkPhase1Limit(self, i):
        config = get_config()
        config['phase1_limit'] = self.checkBoxPhase1Limit.isChecked()
        save_config()

    def checkTotalLimit(self, i):
        config = get_config()
        config['total_limit'] = self.checkBoxTotalLimit.isChecked()
        save_config()

    def checkAutoRestartMine(self, i):
        config = get_config()
        config['auto_restart_mine'] = self.checkBoxAutoRestartMine.isChecked()
        save_config()

    def changePhase1LimitCount(self):
        config = get_config()
        config['phase1_limit_count'] = self.spinBoxPhase1Count.value()
        save_config()

    def changeTotalLimitCount(self):
        config = get_config()
        config['total_limit_count'] = self.spinBoxTotalCount.value()
        save_config()

    def setMainWindow(self, win):
        self.main_window = win

    def timerEvent(self, event: QTimerEvent) -> None:
        timer = event.timerId()

        if timer == self.timerIdUpdateTime:
            self.updateAllTaskItems()

    def showTaskMenu(self, pos):
        item: QTreeWidgetItem = self.treePlot.itemAt(pos)
        index = self.treePlot.indexAt(pos)
        if not item:
            return
        if not index:
            return

        parent_item = item.parent()

        if parent_item:
            task_item = parent_item
            sub_task_item = item
        else:
            task_item = item
            sub_task_item = None

        worker: PlotWorker = task_item.data(1, Qt.UserRole)
        task: PlotTask = task_item.data(0, Qt.UserRole)

        if sub_task_item:
            sub_task: PlotSubTask = sub_task_item.data(0, Qt.UserRole)
        else:
            sub_task: PlotSubTask = task.current_sub_task

        menu = QMenu(self)

        action_detail = menu.addAction(u"查看日志")
        action_modify = None
        action_delete = None
        action_stop = None
        action_suspend = None
        action_resume = None
        action_next_stop = None
        action_locate_temp = None
        action_clean_temp = None
        action_increase_number = None
        action_reduce_number = None

        if not sub_task_item and task.count != 1:
            action_detail.setDisabled(True)

        if task.finish:
            if not sub_task_item:
                menu.addSeparator()
                action_delete = menu.addAction(u"删除")
                if not task.success:
                    if os.path.exists(task.temporary_folder):
                        action_clean_temp = menu.addAction(u"清除临时文件")
        elif worker:
            if not sub_task_item:
                menu.addSeparator()
                action_modify = menu.addAction(u"编辑")
                menu.addSeparator()

                if task.specify_count:
                    action_increase_number = menu.addAction(u"增加数量")
                    if task.pending_count():
                        action_reduce_number = menu.addAction(u"减少数量")
                else:
                    action_next_stop = menu.addAction(u"下个任务停止")
                    action_next_stop.setCheckable(True)
                    action_next_stop.setChecked(worker.next_stop)

            if not sub_task_item or sub_task == task.current_sub_task:
                menu.addSeparator()
                if task.delay_remain():
                    action_stop = menu.addAction(u"取消")
                else:
                    action_stop = menu.addAction(u"停止")

                if sub_task.suspend:
                    action_resume = menu.addAction(u"继续")
                else:
                    action_suspend = menu.addAction(u"暂停")

        if os.path.exists(task.temporary_folder) and platform.system() == 'Windows':
            menu.addSeparator()
            action_locate_temp = menu.addAction(u"浏览临时文件")

        action = menu.exec(QCursor.pos())

        if action is None:
            return

        if action == action_detail:
            self.showTaskOutput(index)
        elif action == action_modify:
            dlg = CreatePlotDialog(task=task)
            if dlg.exec() == dlg.rejected:
                return
            self.saveTasks()
        elif action == action_delete:
            all_files, total_size = task.get_temp_files()

            if len(all_files):
                if QMessageBox.information(self, '提示', f"确定要删除临时目录吗？\n{len(all_files)}个文件\n{size_to_str(total_size)}GB", QMessageBox.Ok | QMessageBox.Cancel) == QMessageBox.Cancel:
                    return
            if os.path.exists(task.temporary_folder) and not task.remove_temp_folder():
                QMessageBox.warning(self, '提示', '清除临时目录失败！')
                return

            self.treePlot.takeTopLevelItem(index.row())
            self.tasks.remove(task)
            self.saveTasks()
        elif action == action_stop:
            if QMessageBox.information(self, '提示', "确定要停止任务吗？停止后无法恢复", QMessageBox.Ok | QMessageBox.Cancel) == QMessageBox.Cancel:
                return
            worker.stop()
        elif action == action_suspend:
            worker.suspend()
        elif action == action_resume:
            worker.resume()
        elif action == action_next_stop:
            worker.next_stop = not worker.next_stop
        elif action == action_locate_temp:
            folder = task.temporary_folder.replace('/', '\\')
            run('explorer /select, ' + folder)
        elif action == action_clean_temp:
            all_files, total_size = task.get_temp_files()

            if len(all_files) == 0:
                QMessageBox.information(self, '提示', '没有临时文件')
                return
            if QMessageBox.information(self, '提示', f"确定要清除临时文件吗？\n{len(all_files)}个文件\n{size_to_str(total_size)}GB", QMessageBox.Ok | QMessageBox.Cancel) == QMessageBox.Cancel:
                return
            if not task.delete_temp_files():
                QMessageBox.warning(self, '提示', '清除临时文件失败！')
        elif action == action_increase_number:
            sub_task = task.increase()
            if task.count == 2:
                self.addSubTaskItem(item, task.sub_tasks[0])
            self.addSubTaskItem(item, sub_task)
        elif action == action_reduce_number:
            sub_task = task.sub_tasks[-1]
            self.removeSubTaskItem(item, sub_task)
            task.reduce()
            if task.count == 1:
                self.removeSubTaskItem(item, task.sub_tasks[0])

    def onExpanded(self, index: QModelIndex):
        item = self.treePlot.itemFromIndex(index)
        if not item:
            return
        task: PlotTask = item.data(0, Qt.UserRole)
        if not task.specify_count:
            return

        if task.count > 1:
            self.treePlot.setItemWidget(item, 7, None)

    def onCollapsed(self, index: QModelIndex):
        item = self.treePlot.itemFromIndex(index)
        if not item:
            return
        task: PlotTask = item.data(0, Qt.UserRole)
        if not task.specify_count:
            return

        progress = QProgressBar()
        progress.setValue(task.progress)
        self.treePlot.setItemWidget(item, 7, progress)

    def showTaskOutput(self, index: QModelIndex):
        item = self.treePlot.itemFromIndex(index)
        parent_item = item.parent()

        if parent_item:
            task_item = parent_item
            sub_task_item = item
        else:
            task_item = item
            sub_task_item = None

        worker = task_item.data(1, Qt.UserRole)
        task = task_item.data(0, Qt.UserRole)

        show_output = True

        if sub_task_item is None and not task.specify_count:
            show_output = True
        elif sub_task_item is None and task.count != 1:
            show_output = False

        if not show_output:
            item.setExpanded(not item.isExpanded())
            return

        if sub_task_item:
            sub_task = sub_task_item.data(0, Qt.UserRole)
        else:
            sub_task = task.current_sub_task

        for d in self.outputDialogs:
            if d.task == task and d.sub_task == sub_task:
                d.activateWindow()
                return

        dlg = TaskOutputDialog(worker, task, sub_task)
        dlg.signalClose.connect(self.closeTaskOutputDialog)
        dlg.show()

        self.outputDialogs.append(dlg)

    def closeTaskOutputDialog(self, dlg):
        self.outputDialogs.remove(dlg)

    def updateAllTaskItems(self):
        count = self.treePlot.topLevelItemCount()
        for i in range(count):
            item = self.treePlot.topLevelItem(i)
            task: PlotTask = item.data(0, Qt.UserRole)
            if not task.finish:
                if task.current_sub_task.suspend:
                    task.current_sub_task.suspended_seconds += 1

                self.updateTaskItem(item, task)
                sub_item = self.getSubItemFromSubTask(item, task.current_sub_task)
                if sub_item:
                    self.updateSubTaskItem(sub_item, task.current_sub_task)

    def loadTasks(self):
        filename = os.path.join(BASE_DIR, 'tasks.pkl')
        if os.path.exists(filename):
            task_data = open(filename, 'rb').read()
            self.tasks = pickle.loads(task_data)

        changed = False
        for task in self.tasks:
            for sub_task in task.sub_tasks:
                if not sub_task.finish:
                    sub_task.status = '异常结束'
                    sub_task.end_time = datetime.now()
                    sub_task.finish = True
                changed = True

        if changed:
            self.saveTasks()

        if self.treePlot.topLevelItemCount() == 0:
            for task in self.tasks:
                self.addTaskItem(task)

    def saveTasks(self):
        filename = os.path.join(BASE_DIR, 'tasks.pkl')
        tasks_data = pickle.dumps(self.tasks)
        open(filename, 'wb').write(tasks_data)

    def clickCreatePlot(self):
        config = get_config()
        if 'ssd_folders' not in config or not config['ssd_folders'] or 'hdd_folders' not in config or not config['hdd_folders']:
            QMessageBox.information(self, '提示', '请先配置硬盘')
            return

        dlg = CreatePlotDialog(parent=self, task=None)
        if dlg.exec() == dlg.Rejected:
            return

        self.tasks.append(dlg.task)
        self.saveTasks()

        item: QTreeWidgetItem = self.addTaskItem(dlg.task)

        worker = PlotWorker(dlg.task, self)
        item.setData(1, Qt.UserRole, worker)
        self.workers.append(worker)
        worker.signalUpdateTask.connect(self.updateTaskStatus)
        worker.signalRequireTask.connect(self.requireTask)
        worker.signalNewPlot.connect(self.onNewPlot)
        worker.start()

    def onNewPlot(self, task: PlotTask, sub_task: PlotSubTask):
        if not task.specify_count:
            item = self.getItemFromTask(task)
            self.addSubTaskItem(item, sub_task)

        config = get_config()
        if 'auto_restart_mine' in config and config['auto_restart_mine']:
            self.restartMine('生成了新Plot文件，正在重新挖矿...')

    def restartMine(self, log=''):
        if not self.main_window:
            return

        self.main_window.tabMineWidget.restartMine(log)

    def updateTaskStatus(self, task: PlotTask, sub_task: PlotSubTask):
        item = self.getItemFromTask(task)
        if not item:
            return

        self.updateTaskItem(item, task)

        if not task.specify_count:
            sub_item = self.getSubItemFromSubTask(item, sub_task)
            if sub_item:
                self.updateSubTaskItem(sub_item, sub_task)

        self.saveTasks()

    def requireTask(self, task: PlotTask):
        self.task_lock.acquire()

        config = get_config()

        total_count = 0
        phase1_count = 0

        for _task in self.tasks:
            if _task == task:
                continue
            if _task.running and not _task.finish:
                total_count += 1
                if _task.phase == 1:
                    phase1_count += 1

        total_limit = 'total_limit' in config and config['total_limit']
        total_limit_count = 'total_limit_count' in config and config['total_limit_count']
        phase1_limit = 'phase1_limit' in config and config['phase1_limit']
        phase1_limit_count = 'phase1_limit_count' in config and config['phase1_limit_count']

        if total_limit and total_count >= total_limit_count:
            self.task_lock.release()
            return False

        if phase1_limit and phase1_count >= phase1_limit_count:
            self.task_lock.release()
            return False

        task.running = True
        self.task_lock.release()
        return True

    def getItemFromTask(self, task: PlotTask):
        for i in range(self.treePlot.topLevelItemCount()):
            item = self.treePlot.topLevelItem(i)
            if item.data(0, Qt.UserRole) == task:
                return item
        return None

    def getSubItemFromSubTask(self, item: QTreeWidgetItem, sub_task: PlotSubTask):
        for i in range(item.childCount()):
            sub_item = item.child(i)
            if sub_item.data(0, Qt.UserRole) == sub_task:
                return sub_item
        return None

    def addTaskItem(self, task: PlotTask):
        item = QTreeWidgetItem()
        item.setData(0, Qt.UserRole, task)

        self.treePlot.addTopLevelItem(item)

        progress = QProgressBar()
        progress.setValue(task.progress)

        if task.specify_count:
            if task.count > 1:
                for sub in task.sub_tasks:
                    self.addSubTaskItem(item, sub)
            else:
                self.treePlot.setItemWidget(item, 7, progress)
            item.setExpanded(True)
        else:
            sub_tasks = task.sub_tasks
            if not task.success:
                sub_tasks = task.sub_tasks[0:-2]
            for sub in sub_tasks:
                if sub.finish and sub.success:
                    self.addSubTaskItem(item, sub)
            self.treePlot.setItemWidget(item, 7, progress)

        self.updateTaskItem(item, task)

        return item

    def addSubTaskItem(self, item: QTreeWidgetItem, sub_task: PlotSubTask):
        sub_item = QTreeWidgetItem()
        sub_item.setData(0, Qt.UserRole, sub_task)
        item.addChild(sub_item)
        self.treePlot.setItemWidget(sub_item, 7, QProgressBar())
        self.updateSubTaskItem(sub_item, sub_task)

    def removeSubTaskItem(self, item: QTreeWidgetItem, sub_task: PlotSubTask):
        sub_item = self.getSubItemFromSubTask(item, sub_task)
        if sub_item:
            sub_item.removeChild(sub_item)

    def updateTaskItem(self, item: QTreeWidgetItem, task: PlotTask):
        index = 0

        item.setText(index, task.ssd_folder)

        index += 1
        item.setText(index, task.hdd_folder)

        index += 1
        delay = task.delay_remain()
        item.setText(index, task.status)
        item.setBackground(index, QBrush(QColor('#ffffff')))
        item.setForeground(index, QBrush(QColor(0, 0, 0)))

        if task.finish:
            if task.success:
                color = QColor('#50c350')
            else:
                color = QColor('#e86363')
            item.setBackground(index, QBrush(color))
            item.setForeground(index, QBrush(QColor(255, 255, 255)))
        elif task.suspend:
            item.setText(index, '已暂停')
        elif task.abnormal:
            item.setBackground(index, QBrush(QColor('#ffb949')))
            item.setForeground(index, QBrush(QColor(255, 255, 255)))
        elif delay:
            item.setText(index, '等待%s' % seconds_to_str(delay))

        index += 1
        if task.specify_count:
            item.setText(index, '%d/%d' % (task.current_task_index + 1, task.count))
        else:
            if task.success:
                item.setText(index, '%d' % task.count)
            else:
                item.setText(index, '%d' % (task.count - 1))

        index += 1
        if task.begin_time:
            item.setText(index, task.begin_time.strftime('%Y-%m-%d %H:%M:%S'))
        else:
            item.setText(index, '--')

        index += 1
        if task.begin_time:
            end_time = task.end_time
            if not end_time:
                end_time = datetime.now()
            delta = end_time - task.begin_time - timedelta(seconds=task.suspended_seconds)
            item.setText(index, delta_to_str(delta))
        else:
            item.setText(index, '--')

        index += 1
        item.setText(index, size_to_str(task.ram) if task.ram and not task.finish else '--')

        index += 1
        if task.specify_count and item.isExpanded() and task.count > 1:
            self.treePlot.setItemWidget(item, index, None)
        else:
            progress: QProgressBar = self.treePlot.itemWidget(item, index)
            if not progress:
                progress = QProgressBar()
                self.treePlot.setItemWidget(item, index, progress)
            progress.setValue(task.progress)

    def updateSubTaskItem(self, item: QTreeWidgetItem, task: PlotSubTask):
        index = 0

        item.setText(index, '')

        index += 1
        item.setText(index, '')

        index += 1
        item.setText(index, task.status)
        item.setBackground(index, QBrush(QColor('#ffffff')))
        item.setForeground(index, QBrush(QColor(0, 0, 0)))

        if task.finish:
            if task.success:
                color = QColor('#50c350')
            else:
                color = QColor('#e86363')
            item.setBackground(index, QBrush(color))
            item.setForeground(index, QBrush(QColor(255, 255, 255)))
        elif task.suspend:
            item.setText(index, '已暂停')
        elif task.abnormal:
            item.setBackground(index, QBrush(QColor('#ffb949')))
            item.setForeground(index, QBrush(QColor(255, 255, 255)))

        index += 1
        item.setText(index, '%d' % (task.index + 1))

        index += 1
        if task.begin_time:
            item.setText(index, task.begin_time.strftime('%Y-%m-%d %H:%M:%S'))
        else:
            item.setText(index, '--')

        index += 1
        if task.begin_time:
            end_time = task.end_time
            if not end_time:
                end_time = datetime.now()
            delta = end_time - task.begin_time - timedelta(seconds=task.suspended_seconds)
            item.setText(index, delta_to_str(delta))
        else:
            item.setText(index, '--')

        index += 1
        item.setText(index, size_to_str(task.ram) if task.ram and not task.finish else '--')

        index += 1
        progress: QProgressBar = self.treePlot.itemWidget(item, index)
        if progress:
            progress.setValue(task.progress)
