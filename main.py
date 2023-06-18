import sys

from PyQt5.QtWidgets import QApplication

from FernetPack.fernet import load_dotenv_data
from app import MainWindow


def start_app():
    marker = 'Parser'
    app = QApplication(sys.argv)
    app_window = MainWindow(marker=marker)
    app_window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    load_dotenv_data()
    start_app()


