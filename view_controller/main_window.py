"""Module for main window implementation."""
import os
import shutil

from PyQt5 import QtWidgets, uic, QtGui

import view_controller.utils
from .download_tab import DownloaderTab
from .login_dialog import LoginDialog
from .manual_tab import ChangeDetectorPanel
from .manual_tab import VesselDetectorPanel


class MainWindow(QtWidgets.QMainWindow):
    """Class for the main window management. View-controller."""

    def __init__(self):
        super().__init__()
        uic.loadUi("views/MainWindow.ui", self)

        # Set window icon
        self.setWindowIcon(QtGui.QIcon('icons/icon.png'))

        # Tabs and dialogs
        self.vd_panel = VesselDetectorPanel(self)
        self.cd_panel = ChangeDetectorPanel(self)
        self.dl_panel = DownloaderTab(self)
        self.login_dialog = None

        # Attributes
        self.username = None

        # Flags
        self.logged_in = False

        # Binding buttons, elements actions with their respective functions
        self.bind_login_actions()  # Log in and log out
        #self.bind_vessel_detection_actions()  # Manual vessel detection tab

        self.modes_tabs.setCurrentIndex(0)  # Make sure first tab is always the selected one


    def bind_login_actions(self):
        """
        Binds the login button to its function.
        :return: None.
        """
        # Login and logout
        self.loginout_bttn.clicked.connect(self.loginout)

    def bind_vessel_detection_actions(self):
        """
        Binds the vessel detector buttons to their respective methods.
        :return: None.
        """
        self.vsel_opn_btn.clicked.connect(view_controller.utils.load_products)
        self.sbst_type_cbox.currentTextChanged.connect(self.vessel_detector.subset_option_enabler)
        self.aoi_type_2.currentTextChanged.connect(self.vessel_detector.subset_type_enabler)
        self.detect_btn.clicked.connect(self.vessel_detector.detect_vessels)
        self.output_path_sel.clicked.connect(self.vessel_detector.out_path_button)

    def loginout(self):
        """
        Executed when either user logs in or out. Changes display messages and button placeholders.
        :return: None.
        """
        if not self.logged_in:
            self.login_dialog = LoginDialog(self)

            self.logged_in = True
            self.setEnabled(False)
            self.login_dialog.show()

        else:  # If logout
            # Close/remove api and username
            self.downloader.downloader = None
            self.username = None

            # Change displayed text back to log in
            self.loginout_bttn.setText("Log in")

            # Change welcome message back to please log in.
            self.welcome.setText("Please, log in first.")

            # Set log_in flag as false
            self.logged_in = False

            # Disable all 3 tabs
            self.set_enabled_tabs(False)

    def login_success(self, api, username):
        """
        Called upon successfull login.
        :param api: Downloader. Instance of the Downloader class.
        :param username: str. Username to display on the greeting label in the main window.
        :return: None.
        """
        self.setEnabled(True)

        # Close login dialog
        self.login_dialog.close()
        self.login_dialog = None

        # Store api and user name
        self.dl_panel.downloader = api
        self.username = username

        # Change welcome message
        self.welcome.setText(f"Hello, {username}!")

        # Change login button placeholder to logout
        self.loginout_bttn.setText("Log out")
        self.logged_in = True

        # Enable all 3 tabs
        self.set_enabled_tabs()

    def set_enabled_tabs(self, value: bool = True) -> None:
        """
        Enables or disables the tabs when session changes.
        :param value: bool, optional. Defaults to True. If True, tabs will be enabled. If False, tabs will be disabled.
        :return: None.
        """
        self.downloader.setEnabled(value)
        self.rslts_tbl.setEnabled(value)
        # self.scheduled.setEnabled(value)  # Not implemented

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        """
        Method called upon window closing.
        :param a0: Action. Ignored.
        :return: None.
        """
        if os.path.isdir(self.dl_panel.tmp_dir):
            shutil.rmtree(self.dl_panel.tmp_dir)
