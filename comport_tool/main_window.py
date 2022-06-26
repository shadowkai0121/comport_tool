from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PySide6.QtCore import Slot, Signal, QIODevice, QObject, QTimer
from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo
from ui_py.main_window import Ui_MainWindow as Window
from datetime import datetime
from functools import partial
import re
import random


class SerialPortWorker(QObject):
    opened = Signal()
    open_fail = Signal(str)
    response = Signal(str)
    serial = None

    def __init__(self):
        super().__init__()
        self.script = {}

    @Slot()
    def read(self):
        if self.serial.isOpen() and self.serial.canReadLine():
            response = self.serial.readLine().toStdString().strip('\n')
            self.response.emit(response)
            # 遞迴取完每一行資料
            self.read()

    @Slot(str)
    def write(self, message: str):
        format_message = f'{message}'
        self.serial.write(format_message.encode('utf8'))

    @Slot(str)
    def open(self, port_name, baud_rate, data_bits, parity, stop_bits, flow_control):
        self.serial = QSerialPort()
        self.serial.readyRead.connect(self.read)
        self.serial.setPortName(port_name)
        self.serial.setBaudRate(baud_rate)
        self.serial.setDataBits(data_bits)
        self.serial.setParity(parity)
        self.serial.setStopBits(stop_bits)
        self.serial.setFlowControl(flow_control)
        result = self.serial.open(QIODevice.ReadWrite)
        if result:
            self.serial.clear()
            self.opened.emit()
        else:
            self.open_fail.emit(self.serial.errorString())
        self.serial.clearError()

    @Slot()
    def close(self):
        if self.serial and self.serial.isOpen():
            self.serial.close()


class MainWindow(QMainWindow):
    open_serial_port = Signal(
        str,
        QSerialPort.BaudRate,
        QSerialPort.DataBits,
        QSerialPort.Parity,
        QSerialPort.StopBits,
        QSerialPort.FlowControl
    )
    close_serial_port = Signal()
    port_write = Signal(str)
    sub_window = []
    script_map = {}

    def __init__(self):
        super().__init__()
        self.ui = Window()
        self.ui.setupUi(self)

        self.worker = SerialPortWorker()
        self.open_serial_port.connect(self.worker.open)
        self.close_serial_port.connect(self.worker.close)
        self.port_write.connect(self.worker.write)
        self.worker.opened.connect(self.port_opened)
        self.worker.open_fail.connect(self.port_open_fail)
        self.worker.response.connect(self.read)

        self.ui.combo_box_port_name.addItems([
            port.portName() for port in QSerialPortInfo().availablePorts()
        ])

        self.ui.combo_box_baud_rate.addItems([
            '1200', '2400', '4800', '9600', '19200', '38400', '57600', '115200'
        ])
        self.ui.combo_box_baud_rate.setCurrentIndex(7)

        self.ui.combo_box_data_bits.addItems([
            '5 bit', '6 bit', '7 bit', '8 bit',
        ])
        self.ui.combo_box_data_bits.setCurrentIndex(3)

        self.ui.combo_box_parity.addItems([
            'NoParity', 'EvenParity', 'OddParity', 'SpaceParity', 'MarkParity'
        ])

        self.ui.combo_box_stop_bits.addItems([
            'OneStop', 'TwoStop', 'OneAndHalfStop'
        ])

        self.ui.combo_box_flow_control.addItems([
            'No Flow Control', 'Hardware Control', 'Software Control'
        ])

        self.ui.button_connect.released.connect(self.open_port)
        self.ui.button_disconnect.released.connect(self.close_port)
        self.ui.button_write.released.connect(self.write)
        self.ui.action_new.triggered.connect(self.create_new_window)
        self.ui.button_run_script.toggled.connect(self.run_script)

    def run_script(self, check: bool):
        self.ui.input_script.setDisabled(check)
        if check:
            script = self.ui.input_script.toPlainText()
            for script_line in script.split('@'):
                if len(script_line) < 1:
                    continue
                command = script_line.split('!')
                pattern = command[0].strip('\n')
                action_list = []

                for action in command[1:]:
                    # 第一個換行之前為 delay 時間
                    index = action.find('\n')

                    delay = action[:index].strip()
                    if len(delay) == 0:
                        delay = 0
                    else:
                        delay = int(delay)
                    action_list.append([delay, action[index:].strip()])
                self.script_map[pattern] = action_list
        else:
            self.script_map = {}

    def create_new_window(self):
        self.sub_window = list(
            filter(lambda x: not x.isHidden(), self.sub_window))
        window = MainWindow()
        window.show()
        self.sub_window.append(window)

    def closeEvent(self, event):
        self.close_serial_port.emit()
        event.accept()

    @Slot(str)
    def read(self, message: str):
        self.write_log(f'Read\r\n{message}')
        if len(self.script_map) < 1:
            return

        for pattern in self.script_map.keys():
            result = re.search(pattern, message)
            if result == None:
                continue
            action = self.script_map[pattern]
            self.process_action(action)
            break

    def process_action(self, action_list):
        for action in action_list:
            if action[0] > 0:
                QTimer().singleShot(
                    action[0] * 1000,
                    partial(self.delay_operation, action[1])
                )
            else:
                self.delay_operation(action[1])

    def delay_operation(self, expression: str):
        result = eval(expression)
        self.ui.input_write.setPlainText(f'{result}\r\n')
        self.write()

    def write(self):
        message = self.ui.input_write.toPlainText()
        self.port_write.emit(message)
        self.write_log(f'Write\r\n{message}')
        self.ui.list_write_log.addItem(message)
        self.ui.input_write.clear()

    def open_port(self):
        baud_rate = int(self.ui.combo_box_baud_rate.currentText())
        data_bits = int(self.ui.combo_box_data_bits.currentText()[:1])
        parity = self.ui.combo_box_parity.currentIndex()
        stop_bits = self.ui.combo_box_stop_bits.currentIndex() + 1
        flow_control = self.ui.combo_box_flow_control.currentIndex()

        self.open_serial_port.emit(
            self.ui.combo_box_port_name.currentText(),
            QSerialPort.BaudRate(baud_rate),
            QSerialPort.DataBits(data_bits),
            QSerialPort.Parity(parity),
            QSerialPort.StopBits(stop_bits),
            QSerialPort.FlowControl(flow_control)
        )

    @Slot()
    def port_opened(self):
        pass

    @Slot(str)
    def port_open_fail(self, error: str):
        replay = QMessageBox.critical(
            self,
            "Serial Port Error",
            error,
            QMessageBox.Cancel | QMessageBox.Retry
        )
        if replay == QMessageBox.Retry:
            self.open_port()

    def close_port(self):
        self.close_serial_port.emit()

    def write_log(self, log: str):
        log_with_time = f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}>{log}'
        self.ui.list_log.addItem(log_with_time)
