"""
View-controller module for the Vessel Detection panel/tab.
"""
import os.path
from datetime import datetime

import shapely.errors
import shapely.wkt
from PyQt5.QtWidgets import QLineEdit, QComboBox, QLabel, QMainWindow

from model import VesselDetector
from view_controller.utils import load_products, set_dir, warning_dialog


class VesselDetectorPanel:
    """
    View and controller for the vessel detector panel.
    """

    def __init__(self, main_window: QMainWindow):
        self.main_window = main_window
        self.detector: VesselDetector = None

        # Paths
        self.prod_paths = []
        self.out_dir = ""
        self.subset = ""
        self.tmp_files = False

        # Params
        self.tgt_window = 0
        self.guard_wd_size = 0.0
        self.bg_wd_size = 0.0
        self.pfa = 0.0
        self.min_tgt = 0.0
        self.max_tgt = 0.0

        # Bind buttons
        self.main_window.vd_prods_btn.clicked.connect(self.open_prods)
        self.main_window.vd_output_btn.clicked.connect(self.sel_output_dir)
        self.main_window.vd_process_btn.clicked.connect(self.launch_detector)

        # Bind comboboxes
        cd_subset_type: QComboBox = self.main_window.vd_subset_type
        cd_subset_type.currentTextChanged.connect(self.enable_subset_input)

    def enable_subset_input(self, value):
        """
        Method called when subset type is changed. Enables WKT input field or disables it.
        :param value: str. Selected text value from the combo box.
        :return: None.
        """
        vd_subset_str: QLineEdit = self.main_window.vd_subset_str
        if value == "Yes":
            vd_subset_str.setEnabled(True)
        else:
            vd_subset_str.setEnabled(False)

    def launch_detector(self):
        """
        Launches the detector.
        :return: None.
        """
        self.get_subset_input()
        self.get_tmp_files_input()
        self.read_parameters()

        self.detector = VesselDetector(subset=self.subset, out_dir=self.out_dir, steps=self.tmp_files, verbose=False,
                                       tgt_window=self.tgt_window, guard_wd_size=self.guard_wd_size,
                                       bg_wd_size=self.bg_wd_size, pfa=self.pfa, min_tgt=self.min_tgt,
                                       max_tgt=self.max_tgt)


        self.display_status("Processing...")
        start = datetime.now()
        self.detector.detect(*self.prod_paths)
        end = datetime.now()
        self.display_status(f"Complete. {end - start}")

    def sel_output_dir(self):
        """
        Selects the output dir path for the vessel detection results.
        :return:
        """
        path = set_dir(self.main_window)
        if not path:
            return
        else:
            self.out_dir = path
            self.display_outputdir_path()

    def open_prods(self):
        """
        Selects the source product paths.
        :return: None.
        """
        paths = load_products(self.main_window)[0]
        if not paths:
            return
        else:
            self.prod_paths = paths
            self.display_prod_count()

    def display_prod_count(self):
        """
        Method called to update the selected product count.
        :return: None.
        """
        vd_prod_count: QLabel = self.main_window.vd_prod_count

        if self.prod_paths:
            vd_prod_count.setText(f"{len(self.prod_paths)}")

        else:
            vd_prod_count.setText("No products selected.")

    def display_outputdir_path(self):
        """
        Method called to display the selected output dir path.
        :return: None.
        """
        vd_output_path: QLabel = self.main_window.vd_output_path

        if self.out_dir:
            basename = os.path.basename(self.out_dir)
            vd_output_path.setText(basename)

        else:
            vd_output_path.setText("No output directory selected.")

    def display_status(self, message):
        """
        Displays the current execution status.
        :param message: Message to display.
        :return: None.
        """
        vd_status_lbl: QLabel = self.main_window.vd_status_lbl
        vd_status_lbl.setText(message)

    def get_subset_input(self):
        """
        Gets the subset input.
        :return: None.
        """
        vd_subset_str: QLineEdit = self.main_window.vd_subset_str.text()

        if vd_subset_str:
            try:
                shapely.wkt.loads(vd_subset_str)
            except shapely.errors.WKTReadingError as e:
                warning_dialog(e.message)
                return

        self.subset = vd_subset_str

    def get_tmp_files_input(self):
        """
        Gets the input regarding the temporary files.
        :return: None.
        """
        vd_tmp_files_cbox: QComboBox = self.main_window.vd_tmp_files_cbox
        self.tmp_files = True if vd_tmp_files_cbox.currentText() == "Yes" else False

    def read_parameters(self) -> None:
        """
        Reads the input parameters for the vessel detection algorithm.
        :return: None.
        """
        self.tgt_window = self.main_window.vd_tgt_wdw_in.value()
        self.guard_wd_size = self.main_window.vd_guard_ws_in.value()
        self.bg_wd_size = self.main_window.vd_bg_ws_in.value()
        self.pfa = self.main_window.vd_pfa_in.value()

        self.min_tgt = self.main_window.vd_min_tgt_size_in.value()
        self.max_tgt = self.main_window.vd_max_tgt_size_in.value()
