import os
import subprocess
import threading

import schedule
import design
from datetime import datetime
from time import sleep, perf_counter
from PyQt5.QtWidgets import QMainWindow, QMessageBox
from PyQt5.QtCore import QThread, pyqtSignal

from AsyncProcessPack import AsyncProcess
from MessagePack import print_info_msg
from WinSoundPack import beep
from save_data import save_json, get_json_data_from_file
from sites.roller import SiteParser as Parser


class QTTimer(QThread):

    def __init__(self, app):
        super().__init__()
        self.start_time = 0
        self.app = app

    def run(self):
        self.start_time = perf_counter()
        self.app.startTime.setText(datetime.now().strftime('%H:%M:%S'))
        self.app.workTime.setText('00:00:00')
        while self.app.run:
            time = perf_counter() - self.start_time
            self.app.workTime.setText(self.app.convert_sec_to_time_string(time))
            sleep(1)
        print('stop timer')
        self.quit()


class ScheduleThread(QThread):
    about_time = pyqtSignal(int)

    def __init__(self, app):
        super().__init__()
        self.app = app
        print('start scheduler')

    def add_time(self, time: int):
        # schedule.every(time).minutes.do(
        schedule.every(time).hours.do(
            lambda: self.about_time.emit(time)
        )

    def run(self):
        while self.app.run:
            schedule.run_pending()
            sleep(1)
        schedule.jobs.clear()
        sleep(1)
        print('stop scheduler')
        self.quit()


class MainWindow(QMainWindow, design.Ui_MainWindow):

    def __init__(self, marker: str = ''):
        # Обязательно нужно вызвать метод супер класса
        QMainWindow.__init__(self)
        self.setupUi(self)

        # ToolTips stylesheet
        self.setStyleSheet("""QToolTip {
                            border: 1px solid black;
                            padding: 3px;
                            border-radius: 3px;
                            opacity: 200;
                        }""")

        self._cpu = os.cpu_count()
        self._run = False
        self._interval = 1
        self._interval_timer = None

        self._n_list = []  # список названий запущенных парсеров
        self._p_list = []  # список запущенных парсеров

        self.setWindowTitle(marker)  # Устанавливаем заголовок окна
        self.startTime.setText('00:00:00')
        self.workTime.setText('00:00:00')
        self.statusLabel.setText('ОСТАНОВЛЕН')
        self.statusLabel.setStyleSheet(
            'background-color: rgb(255, 255, 255); color: rgb(255, 74, 101); border: 1px solid;')
        self.startButton.clicked.connect(self._start_click)
        self.stopButton.clicked.connect(self._stop_click)

    @property
    def run(self):
        return self._run

    @classmethod
    def convert_sec_to_time_string(cls, seconds):
        """ Convert time value in seconds to time data string - 00:00:00"""
        seconds = seconds % (24 * 3600)
        hour = seconds // 3600
        seconds %= 3600
        minutes = seconds // 60
        seconds %= 60
        return "%02d:%02d:%02d" % (hour, minutes, seconds)

    def _start_click(self):
        if self._run:
            return
        print('start')
        self._run = True
        # no sleep mode
        subprocess.call("powercfg -change -monitor-timeout-ac 0")
        subprocess.call("powercfg -change -disk-timeout-ac 0")
        subprocess.call("powercfg -change -standby-timeout-ac 0")
        # run timer
        self.timer = QTTimer(self)
        self.timer.start()
        # set ui data
        self.statusLabel.setText('ЗАПУЩЕН')
        self.statusLabel.setStyleSheet(
            'background-color: rgb(255, 255, 255); color: rgb(85, 170, 127); border: 1px solid;')
        AsyncProcess('clear UI', self.clear_ui, 1, (self, 'end_clear_ui'))

    def _stop_click(self):
        if not self._run:
            return
        print('stop')
        beep()
        self._run = False
        self.statusLabel.setText('ОСТАНОВЛЕН')
        self.statusLabel.setStyleSheet(
            'background-color: rgb(255, 255, 255); color: rgb(255, 74, 101); border: 1px solid;')

    def closeEvent(self, event):
        print('close event')
        if self._run:
            button = QMessageBox.question(self, "Внимание!", "Текущие процессы парсинга будут остановлены! Продолжить?")
            if button == QMessageBox.Yes:
                self._stop_click()
                sleep(10)
                event.accept()
            else:
                event.ignore()

    def _run_app(self):
        if not self._run:
            return
        beep()
        self.parser = Parser(self, 'https://www.rollerderbyhouse.eu', 1)
        self.parser.start()

    def set_counter(self, url):
        num = int(self.counter.text())
        self.counter.setText(str(num + 1))
        self.listWidget.addItem(url)
        self.listWidget.scrollToBottom()

    def end_pars(self):
        self._stop_click()

    def clear_ui(self):
        self.listWidget.clear()
        self.counter.setText('0')

    def end_clear_ui(self):
        self._run_app()


