from PyQt5.QtWidgets import QWidget, QMessageBox
from PyQt5.Qt import pyqtSignal, QTimerEvent
from ui.MineWidget import Ui_MineWidget
from config import save_config, get_config
from utils import size_to_str
from datetime import datetime
import os
from core import BASE_DIR
from subprocess import Popen, PIPE
import socket
import threading
import platform


class MineWidget(QWidget, Ui_MineWidget):
    signalMineLog = pyqtSignal(str)
    signalMineTerminated = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)

        self.main_window = None

        self.mine_process = None
        self.mine_terminating = False
        self.mine_restarting = False

        self.signalMineLog.connect(self.outputMineLog)
        self.signalMineTerminated.connect(self.mineTerminated)

        self.timerIdUpdateSpace = self.startTimer(1000 * 10)

        config = get_config()

        if 'miner_name' in config:
            self.editMinerName.setText(config['miner_name'])
        else:
            self.editMinerName.setText(socket.gethostname())
        self.editMinerName.editingFinished.connect(self.saveMineConfig)

        if 'apikey' in config:
            self.editApiKey.setText(config['apikey'])
        self.editApiKey.editingFinished.connect(self.saveMineConfig)

        self.buttonStart.clicked.connect(self.clickStartMine)
        self.checkBoxAutoStart.stateChanged.connect(self.checkAutoStart)

    def setMainWindow(self, win):
        self.main_window = win

        config = get_config()

        if 'auto_mine' in config and config['auto_mine']:
            self.checkBoxAutoStart.setChecked(True)
            self.startMine()

    def timerEvent(self, event: QTimerEvent) -> None:
        timer = event.timerId()

        if timer == self.timerIdUpdateSpace:
            self.updateTotalGB()

    def updateTotalGB(self):
        config = get_config()

        total_size = 0
        total_count = 0

        if 'hdd_folders' in config:
            for folder_obj in config['hdd_folders']:
                if not folder_obj['mine']:
                    continue
                folder = folder_obj['folder']
                if not os.path.exists(folder):
                    continue

                try:
                    files = os.listdir(folder)
                    for f in files:
                        if not f.endswith('.plot'):
                            continue
                        file = os.path.join(folder, f)
                        if os.path.isfile(file):
                            total_size += os.path.getsize(file)
                            total_count += 1
                except:
                    return

        self.labelCurrentGB.setText(size_to_str(total_size))
        self.labelCurrentCount.setText(f'{total_count}个')

    def outputMineLog(self, text):
        text = text.strip()

        if not text:
            return

        self.textEditLog.append(text)

        log_size = len(self.textEditLog.toPlainText())
        if log_size > 1024 * 1024:
            self.textEditLog.clear()

    def minerLog(self, text):
        dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        self.textEditLog.append(dt + ' ' + text)

    def mineTerminated(self):
        self.editMinerName.setDisabled(False)
        self.editApiKey.setDisabled(False)
        self.buttonStart.setText('开始挖矿')

        index = self.main_window.tabWidget.indexOf(self.main_window.tabMine)
        self.main_window.tabWidget.setTabText(index, '矿池挖矿')

        if self.mine_restarting:
            self.mine_restarting = False
            self.startMine()
            return

        if not self.mine_terminating:
            self.minerLog('挖矿意外停止')
            self.minerLog('正在重新挖矿...')

            self.mine_process = None
            self.startMine()
            return

        self.minerLog('挖矿已停止')

        self.mine_terminating = False

    def saveMineConfig(self):
        miner_name = self.editMinerName.text()
        apikey = self.editApiKey.text()

        config = get_config()

        config['miner_name'] = miner_name
        config['apikey'] = apikey

        save_config()

    def restartMine(self, log=''):
        if self.mine_process is None:
            return

        if not log:
            log = '配置已更改，正在重新挖矿...'
        self.minerLog(log)

        self.mine_restarting = True

        self.mine_process.terminate()

    def checkAutoStart(self, i):
        config = get_config()
        config['auto_mine'] = self.checkBoxAutoStart.isChecked()
        save_config()

    def clickStartMine(self):
        self.textEditLog.clear()
        self.startMine()

    def startMine(self):
        if self.mine_process:
            self.mine_terminating = True
            self.mine_process.terminate()
            self.mine_process.wait()
            self.mine_process = None
            return

        config = get_config()

        if 'hdd_folders' not in config or not config['hdd_folders']:
            QMessageBox.information(self, '提示', '请先配置硬盘')
            return

        miner_name = config['miner_name']
        apikey = config['apikey']

        if not miner_name:
            self.editMinerName.setFocus()
            return

        if not apikey:
            self.editApiKey.setFocus()
            return

        if not self.generateMineConfig():
            return

        t = threading.Thread(target=self.mineThread)
        t.start()

        self.editMinerName.setDisabled(True)
        self.editApiKey.setDisabled(True)
        self.buttonStart.setText('停止挖矿')

        index = self.main_window.tabWidget.indexOf(self.main_window.tabMine)
        self.main_window.tabWidget.setTabText(index, '矿池挖矿（正在挖矿）')

    def generateMineConfig(self):
        config = get_config()

        if 'hdd_folders' not in config or not config['hdd_folders']:
            QMessageBox.information(self, '提示', '请先配置最终目录')
            return False

        plat = platform.system()
        if plat == 'Windows':
            folder = 'windows'
        elif plat == 'Darwin':
            folder = 'macos'
        elif plat == 'Linux':
            folder = 'linux'
        else:
            return False

        config_file = os.path.join(BASE_DIR, 'bin', folder, 'miner', 'config.yaml')

        paths = ''

        for folder_obj in config['hdd_folders']:
            if not folder_obj['mine']:
                continue
            folder = folder_obj['folder']
            if paths:
                paths += '\n'
            paths += '- %s' % folder

        if not paths:
            QMessageBox.information(self, '提示', '最终目录中没有可以挖矿的目录')
            return False

        content = f'''token: ""
path:
{paths}
minerName: {config['miner_name']}
apiKey: {config['apikey']}
cachePath: ""
deviceId: ""
extraParams: {{}}
log:
  lv: info
  path: ./log
  name: miner.log
url:
  info: ""
  submit: ""
scanPath: true
scanMinute: 10
debug: ""
'''

        try:
            open(config_file, 'w').write(content)
        except Exception as e:
            return False

        return True

    def mineThread(self):
        plat = platform.system()
        if plat == 'Windows':
            folder = 'windows'
            bin_file = 'hpool-miner-chia-console.exe'
        elif plat == 'Darwin':
            folder = 'macos'
            bin_file = 'hpool-miner-chia'
        elif plat == 'Linux':
            folder = 'linux'
            bin_file = 'hpool-miner-chia'
        else:
            return False

        config_file = os.path.join(BASE_DIR, 'bin', folder, 'miner', 'config.yaml')
        exe_file = os.path.join(BASE_DIR, 'bin', folder, 'miner', bin_file)

        self.mine_process = Popen([exe_file, '-config', config_file], stdout=PIPE, stderr=PIPE)

        while True:
            if self.mine_process is None:
                break
            line = self.mine_process.stdout.readline()
            text = line.decode('utf-8')
            if not text and self.mine_process.poll() is not None:
                break
            self.signalMineLog.emit(text)

        self.mine_process = None

        self.signalMineTerminated.emit()
