from datetime import datetime
from PyQt5.Qt import pyqtSignal
from PyQt5.Qt import QThread
import time
import os
from subprocess import Popen, PIPE
from core import BASE_DIR, is_debug
import re
import shutil
import psutil
import platform
from utils import seconds_to_str


class PlotTask(object):
    def __init__(self):
        self.running = False
        self.phase = 1

        self.fpk = ''
        self.ppk = ''
        self.ssd_folder = ''
        self.hdd_folder = ''
        self.temporary_folder = ''
        self.number_of_thread = 0
        self.memory_size = 0
        self.delay_seconds = 0

        self.create_time = None

        self.specify_count = False
        self.count = 0
        self.current_task_index = 0
        self.sub_tasks: [PlotSubTask] = []

    def increase(self):
        self.sub_tasks.append(PlotSubTask(self.count))
        self.count += 1
        return self.sub_tasks[-1]

    def reduce(self):
        if self.pending_count() == 0:
            return
        self.sub_tasks.remove(self.sub_tasks[-1])
        self.count -= 1

    def pending_count(self):
        count = self.count - (self.current_task_index + 1)
        if count < 0:
            count = 0
        return count

    @property
    def status(self):
        return self.sub_tasks[self.current_task_index].status

    @property
    def finish(self):
        for sub in self.sub_tasks:
            if not sub.finish:
                return False
        return True

    @property
    def success(self):
        for sub in self.sub_tasks:
            if not sub.success:
                return False
        return True

    @property
    def suspend(self):
        for sub in self.sub_tasks:
            if sub.suspend:
                return True
        return False

    @property
    def abnormal(self):
        for sub in self.sub_tasks:
            if sub.abnormal:
                return True
        return False

    @property
    def begin_time(self):
        if not self.specify_count:
            return self.current_sub_task.begin_time
        return self.sub_tasks[0].begin_time

    @property
    def end_time(self):
        return self.sub_tasks[-1].end_time

    @property
    def suspended_seconds(self):
        suspended_seconds = 0
        for sub in self.sub_tasks:
            suspended_seconds += sub.suspended_seconds
        return suspended_seconds

    @property
    def ram(self):
        return self.sub_tasks[self.current_task_index].ram

    @property
    def progress(self):
        if not self.specify_count:
            return self.current_sub_task.progress

        total_progress = 0
        for sub in self.sub_tasks:
            total_progress += sub.progress
        return total_progress / self.count

    @property
    def current_sub_task(self):
        return self.sub_tasks[self.current_task_index]

    def delay_remain(self):
        if self.delay_seconds == 0:
            return 0
        remain = self.create_time.timestamp() + self.delay_seconds - time.time()
        if remain < 0:
            return 0
        return int(remain)

    def get_temp_files(self):
        all_files = []
        total_size = 0
        try:
            for file in os.listdir(self.temporary_folder):
                full = os.path.join(self.temporary_folder, file)
                if not os.path.isfile(full):
                    continue
                total_size += os.path.getsize(full)
                all_files.append(full)
        except:
            pass
        return all_files, total_size

    def delete_temp_files(self):
        all_files, total_size = self.get_temp_files()
        try:
            for file in all_files:
                os.remove(file)
        except:
            return False
        return True

    def remove_temp_folder(self):
        try:
            shutil.rmtree(self.temporary_folder)
        except:
            return False
        return True


class PlotSubTask(object):
    def __init__(self, index):
        self.index = index
        self.status = '等待'
        self.finish = False
        self.success = False
        self.abnormal = False
        self.suspend = False

        self.suspended_seconds = 0

        self.begin_time = None
        self.end_time = None
        self.progress = 0.0
        self.ram = 0

        self.plot_file = ''

        self.log = []


class PlotWorker(QThread):
    signalUpdateTask = pyqtSignal(PlotTask, PlotSubTask)
    signalRequireTask = pyqtSignal(PlotTask)
    signalTaskOutput = pyqtSignal(PlotTask, PlotSubTask, str)
    signalNewPlot = pyqtSignal(PlotTask, PlotSubTask)

    def __init__(self, task, plot_widget):
        super(PlotWorker, self).__init__()

        self.task: PlotTask = task
        self.plot_widget = plot_widget

        self.process = None

        self.plot_filename = ''

        self.stopping = False
        self.next_stop = False

        self.phase = 0
        self.table = ''
        self.bucket = 0
        self.phase3_first_computation = True

    def get_pos_process(self):
        if not self.process:
            return None
        try:
            p = psutil.Process(pid=self.process.pid)
            ps = p.children()
            if len(ps) != 1:
                return None
            p = ps[0]
            if p.name().lower() == 'proofofspace.exe':
                return p
            return None
        except:
            return None

    def reset(self):
        self.plot_filename = ''
        self.phase = 0
        self.table = ''
        self.bucket = 0
        self.phase3_first_computation = True

    def handleProgress(self, text):
        if text.startswith('Starting phase 1/4'):
            self.phase = 1
            self.task.phase = 1
        elif text.startswith('Computing table'):
            self.table = text
        elif text.startswith('Starting phase 2/4'):
            self.phase = 2
            self.task.phase = 2
        elif text.startswith('Backpropagating on table'):
            self.table = text
        elif text.startswith('Starting phase 3/4'):
            self.phase = 3
            self.task.phase = 3
        elif text.startswith('Compressing tables'):
            self.phase3_first_computation = True
            self.table = text
        elif text.startswith('First computation'):
            self.phase3_first_computation = False
        elif text.startswith('Starting phase 4/4'):
            self.phase = 4
            self.task.phase = 4
        elif text.startswith('Wrote left entries'):
            if self.table == 'Backpropagating on table 7':
                self.task.current_sub_task.progress = 29.167
                self.updateTask()
        elif text.startswith('Bucket'):
            r = re.compile(r'Bucket (\d*) ')
            found = re.findall(r, text)
            if not found:
                return
            self.bucket = int(found[0])

            if self.phase == 1:
                if self.table == 'Computing table 2':
                    base_progress = 0.0
                    max_progress = 4.167
                    total_bucket = 127
                elif self.table == 'Computing table 3':
                    base_progress = 4.167
                    max_progress = 8.333
                    total_bucket = 127
                elif self.table == 'Computing table 4':
                    base_progress = 8.333
                    max_progress = 12.500
                    total_bucket = 127
                elif self.table == 'Computing table 5':
                    base_progress = 12.500
                    max_progress = 16.667
                    total_bucket = 127
                elif self.table == 'Computing table 6':
                    base_progress = 16.667
                    max_progress = 20.833
                    total_bucket = 127
                elif self.table == 'Computing table 7':
                    base_progress = 20.833
                    max_progress = 25.000
                    total_bucket = 127
                else:
                    return
            elif self.phase == 2:
                if self.table == 'Backpropagating on table 6':
                    base_progress = 29.167
                    max_progress = 33.333
                    total_bucket = 110
                elif self.table == 'Backpropagating on table 5':
                    base_progress = 33.333
                    max_progress = 37.500
                    total_bucket = 110
                elif self.table == 'Backpropagating on table 4':
                    base_progress = 37.500
                    max_progress = 41.667
                    total_bucket = 110
                elif self.table == 'Backpropagating on table 3':
                    base_progress = 41.667
                    max_progress = 45.833
                    total_bucket = 110
                elif self.table == 'Backpropagating on table 2':
                    base_progress = 45.833
                    max_progress = 50.000
                    total_bucket = 110
                else:
                    return
            elif self.phase == 3:
                if self.table == 'Compressing tables 1 and 2':
                    base_progress = 50.000
                    max_progress = 54.167
                    total_bucket = 127
                elif self.table == 'Compressing tables 2 and 3':
                    base_progress = 54.167
                    max_progress = 58.333
                    total_bucket = 102 + 81 + 1
                    if not self.phase3_first_computation:
                        self.bucket = 102 + 1 + self.bucket
                elif self.table == 'Compressing tables 3 and 4':
                    base_progress = 58.333
                    max_progress = 62.500
                    total_bucket = 102 + 82 + 1
                    if not self.phase3_first_computation:
                        self.bucket = 102 + 1 + self.bucket
                elif self.table == 'Compressing tables 4 and 5':
                    base_progress = 62.500
                    max_progress = 66.667
                    total_bucket = 103 + 83 + 1
                    if not self.phase3_first_computation:
                        self.bucket = 103 + 1 + self.bucket
                elif self.table == 'Compressing tables 5 and 6':
                    base_progress = 66.667
                    max_progress = 70.833
                    total_bucket = 105 + 86 + 1
                    if not self.phase3_first_computation:
                        self.bucket = 105 + 1 + self.bucket
                elif self.table == 'Compressing tables 6 and 7':
                    base_progress = 70.833
                    max_progress = 75.000
                    total_bucket = 110 + 95 + 1
                    if not self.phase3_first_computation:
                        self.bucket = 110 + 1 + self.bucket
                else:
                    return
            elif self.phase == 4:
                base_progress = 75.000
                max_progress = 99.000
                total_bucket = 127
            else:
                return
            # bucket_progress = 100 * self.bucket / total_bucket
            # progress = bucket_progress * max_progress / 100
            self.task.current_sub_task.progress = (100*self.bucket/total_bucket) * (max_progress-base_progress) / 100 + base_progress
            self.updateTask()
        elif text.startswith('Final File size'):
            self.task.current_sub_task.status = '生成文件'
            self.updateTask()
        elif text.startswith('Copied final file'):
            self.task.current_sub_task.progress = 100.0
            self.updateTask()

    def handleLog(self, text):
        text = text.strip()

        failed = False
        finished = False

        self.task.current_sub_task.abnormal = False

        if text.startswith('Generating plot for'):
            r = re.compile(r'filename=(.*) id=')
            found = re.findall(r, text)
            if found:
                self.plot_filename = found[0]
        elif text.startswith('Bucket'):
            r = re.compile(r'Ram: (.*)GiB, u_sort')
            found = re.findall(r, text)
            if found:
                ram = float(found[0]) * 2**30
                if self.task.current_sub_task.ram != ram:
                    self.task.current_sub_task.ram = ram
                    self.updateTask()
        elif text.startswith('time=') and text.count('level='):
            r = re.compile(r'level=(.*) msg=')
            found = re.findall(r, text)
            if found:
                level = found[0]
                if level == 'fatal':
                    failed = True
        elif text.count('Error') and text.count('Retrying'):
            self.task.current_sub_task.abnormal = True
        elif text.startswith('Renamed final file from'):
            finished = True

        self.handleProgress(text)

        return failed, finished

    def stop(self):
        if self.task.delay_remain():
            self.stopping = True
            return

        self.stopping = True

        if self.process:
            pos_process = self.get_pos_process()
            self.process.terminate()
            if pos_process:
                pos_process.resume()
                pos_process.terminate()

    def suspend(self):
        self.task.current_sub_task.suspend = True
        self.updateTask()

        if self.process is None:
            return

        pos_process = self.get_pos_process()
        if not pos_process:
            return

        try:
            pos_process.suspend()
        except:
            pass

    def resume(self):
        self.task.current_sub_task.suspend = False
        self.updateTask()

        if self.process is None:
            return

        pos_process = self.get_pos_process()
        if not pos_process:
            return

        try:
            pos_process.resume()
        except:
            pass

    def run(self):
        t = self.task

        plat = platform.system()
        if plat == 'Windows':
            folder = 'windows'
            bin_file = 'chia-plotter-windows-amd64.exe'
        elif plat == 'Darwin':
            folder = 'macos'
            bin_file = 'chia-plotter-darwin-amd64'
        elif plat == 'Linux':
            folder = 'linux'
            bin_file = 'chia-plotter-linux-amd64'
        else:
            return False

        if plat == 'Windows' and 'DEBUG' in os.environ and os.environ['DEBUG'] == '1':
            bin_file = 'test.exe'

        exe_cwd = os.path.join(BASE_DIR, 'bin', folder, 'plotter')
        exe = os.path.join(exe_cwd, bin_file)

        param = f'-action plotting -plotting-fpk {t.fpk} -plotting-ppk {t.ppk} -plotting-n 1 -r {t.number_of_thread} -b {t.memory_size} -d "{t.hdd_folder}" -t "{t.temporary_folder}" -2 "{t.temporary_folder}"'

        cmd = f'"{exe}" {param}'
        args = [
            exe,
            '-action', 'plotting',
            '-plotting-fpk', t.fpk,
            '-plotting-ppk', t.ppk,
            '-plotting-n', '1',
            '-r', f'{t.number_of_thread}',
            '-b', f'{t.memory_size}',
            '-d', t.hdd_folder,
            '-t', t.temporary_folder,
            '-2', t.temporary_folder,
        ]

        while True:
            self.reset()

            delay_remain = self.task.delay_remain()

            current_sub_task: PlotSubTask = self.task.current_sub_task

            if self.stopping:
                self.stopping = False
                current_sub_task.status = '已取消'
                current_sub_task.finish = True
                current_sub_task.success = False
                current_sub_task.end_time = datetime.now()

                for i in range(self.task.current_task_index + 1, self.task.count):
                    rest_sub_task = self.task.sub_tasks[i]
                    rest_sub_task.success = False
                    rest_sub_task.status = '已手动停止'
                    rest_sub_task.finish = True
                    self.updateTask(sub_task=rest_sub_task)
                else:
                    self.updateTask()
                break

            if current_sub_task.suspend:
                self.task.delay_seconds += 1

            if delay_remain:
                time.sleep(1)
                continue

            self.task.running = False
            if not self.plot_widget.requireTask(self.task):
                current_sub_task.status = '排队中'
                time.sleep(1)
                continue

            current_sub_task.begin_time = datetime.now()
            current_sub_task.status = '正在执行'
            current_sub_task.progress = 0
            self.updateTask()

            self.process = Popen(args, stdout=PIPE, stderr=PIPE, cwd=exe_cwd)

            success = True
            finished = False
            while True:
                line = self.process.stdout.readline()

                text = line.decode('utf-8', errors='replace')
                text = text.rstrip()

                if not text and self.process.poll() is not None:
                    break

                if text:
                    current_sub_task.log.append(text)
                    _failed, _finished = self.handleLog(text)
                    if _failed:
                        success = False
                    if _finished:
                        finished = True
                    self.signalTaskOutput.emit(self.task, current_sub_task, text)
                    self.updateTask()

            self.process = None
            self.task.running = False

            stop = False
            failed = False

            plot_path = os.path.join(self.task.hdd_folder, self.plot_filename)

            if self.stopping:
                self.stopping = False
                stop = failed = True
                current_sub_task.status = '已手动停止'
            elif not self.plot_filename:
                stop = failed = True
                current_sub_task.status = '没有plot文件名'
            elif not success or not finished:
                stop = failed = True
                current_sub_task.status = '失败'
            elif not os.path.exists(plot_path) and not is_debug():
                stop = failed = True
                current_sub_task.status = 'plot文件不存在'
            else:
                current_sub_task.status = '完成'
                current_sub_task.finish = True
                current_sub_task.success = True
                current_sub_task.progress = 100.0
                current_sub_task.end_time = datetime.now()
                current_sub_task.plot_file = plot_path

                self.signalNewPlot.emit(self.task, current_sub_task)

                self.updateTask()

                if self.task.specify_count:
                    if self.task.current_task_index + 1 >= self.task.count:
                        break
                    else:
                        self.task.current_task_index += 1
                        continue
                else:
                    if self.next_stop:
                        break
                    self.task.count += 1
                    self.task.current_task_index += 1
                    self.task.sub_tasks.append(PlotSubTask(self.task.current_task_index))

            self.updateTask()

            if failed:
                current_sub_task.success = False
                current_sub_task.finish = True
                current_sub_task.end_time = datetime.now()

            if stop:
                for i in range(self.task.current_task_index + 1, self.task.count):
                    rest_sub_task = self.task.sub_tasks[i]
                    rest_sub_task.success = False
                    rest_sub_task.status = '已手动停止'
                    rest_sub_task.finish = True
                    self.updateTask(sub_task=rest_sub_task)
                else:
                    self.updateTask()

                break

    def updateTask(self, task=None, sub_task=None):
        if task is None:
            task = self.task
        if sub_task is None:
            sub_task = self.task.current_sub_task

        self.signalUpdateTask.emit(task, sub_task)
