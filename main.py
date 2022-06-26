from PySide6.QtWidgets import QApplication
from comport_tool.main_window import MainWindow
from sys import exit

show_serial_thread_log = True

def run():
    app = QApplication()
    window = MainWindow()
    window.show()
    exit(app.exec())


if __name__ == '__main__':
    run()