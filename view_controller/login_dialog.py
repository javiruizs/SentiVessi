"""Module dedicated to the login dialog."""
import configparser
import json

from PyQt5 import QtWidgets, uic, QtGui

from model import Downloader
from view_controller.utils import warning_dialog, critical_dialog, open_cfg_path


class LoginDialog(QtWidgets.QDialog):
    """
    Class to manage the login dialog.
    """

    def __init__(self, app):

        super().__init__()
        uic.loadUi("views/LoginDialog.ui", self)

        # Set window icon
        self.setWindowIcon(QtGui.QIcon('icons/icon.png'))

        self.json_btn.clicked.connect(self.load_cfg)
        self.login_btn.clicked.connect(self.login)

        self.dlr = None

        self.app = app

        self.show()

    def load_json(self):
        """
        Loads credentials and URL from a JSON format.
        :return: None.
        """
        file = open_cfg_path(self)[0]
        if not file:
            return

        with open(file) as f:
            config = json.load(f)

        # Replace
        urls = [self.url_ipt.itemText(i) for i in range(self.url_ipt.count())]
        try:
            if config['host'] not in urls:
                urls.append(config['host'])
                index = len(urls) - 1
            else:
                index = urls.index(config['host'])
            self.url_ipt.clear()
            self.url_ipt.addItems(urls)
            self.url_ipt.setCurrentIndex(index)

            self.pswd_ipt.setText(config['password'])
            self.usr_ipt.setText(config['username'])
        except KeyError:
            warning_dialog("Invalid JSON format.")

    def load_cfg(self):
        """
        Loads credentials and URL from a INI format.
        :return: None.
        """
        file = open_cfg_path(self)[0]
        if not file:
            return

        try:
            dlr = Downloader.from_file(file)
        except (configparser.NoOptionError, configparser.NoSectionError):
            warning_dialog(f"File '{file}' has an incompatible format.")
            return

        # Replace
        url = dlr.api_url.rstrip("/")
        urls = [self.url_ipt.itemText(i).rstrip("/") for i in range(self.url_ipt.count())]
        if url not in urls:
            urls.append(url)
            index = len(urls) - 1
        else:
            index = urls.index(url)
        self.url_ipt.clear()
        self.url_ipt.addItems(urls)
        self.url_ipt.setCurrentIndex(index)

        self.pswd_ipt.setText(dlr.session.auth[1])
        self.usr_ipt.setText(dlr.session.auth[0])

        self.dlr = dlr

    def login(self):
        """
        Logs in
        :return:
        """
        # Gets text from fields
        username = self.usr_ipt.text()
        password = self.pswd_ipt.text()
        url = self.url_ipt.currentText()

        # Checks if username and password are empty
        if not username or not password:
            critical_dialog("Username and password fields cannot be left empty!")
            return

        if url:
            api = Downloader(username, password, url)
        else:
            api = Downloader(username, password)

        if not api.check_creds():
            message = "Invalid login. Please check your credentials."

            warning_dialog(message)
        else:
            self.app.login_success(api, username)

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        """
        Action to fulfill when login dialog is closed.
        :param a0: Event.
        :return: None.
        """
        self.app.setEnabled(True)
