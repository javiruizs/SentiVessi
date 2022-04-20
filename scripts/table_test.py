import os
import sys

import pandas
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt

from view_controller.download_tab import ResultsModel


def main(app):

    mw = QtWidgets.QMainWindow()
    layout = QtWidgets.QGridLayout()
    mw.setLayout(layout)

    tv = QtWidgets.QTableView()

    layout.addWidget(tv)

    data = {
        "name": ["peter", "javier"],
        "lastname": ["lachett", "ruiz"]
    }

    df = pandas.DataFrame(data)

    tm = ResultsModel(df)

    tv.setModel(tm)
    tv.setSelectionBehavior(QtWidgets.QTableView.SelectRows)

    # mw.show()
    tv.show()


    sys.exit(app.exec())




if __name__ == '__main__':
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "2"
    QtWidgets.QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    app = QtWidgets.QApplication(sys.argv)

    main(app)
