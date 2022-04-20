"""Main script where the program is launched."""
import os
import sys

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from view_controller import MainWindow


if __name__ == '__main__':
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "2"
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)

    mw = MainWindow()

    mw.show()

    sys.exit(app.exec())
