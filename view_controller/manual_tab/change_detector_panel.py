"""This module includes everything related to the change detector groupbox."""
import os.path
from datetime import datetime

import shapely.errors
import shapely.wkt
from PyQt5.QtWidgets import QLineEdit, QComboBox, QLabel, QMainWindow

from model import ChangeDetector
from model.detectors import RGBChannel
from view_controller.utils import load_product, load_products, set_dir, warning_dialog


class ChangeDetectorPanel:
    """Class that manages the change detection section in the UI."""

    def __init__(self, main_window: QMainWindow):
        self.main_window = main_window
        self.detector: ChangeDetector = None

        # Paths
        self.ref_prod_path = ""
        self.prod_paths = []
        self.out_dir = ""
        self.subset = ""
        self.ref_color: RGBChannel = RGBChannel.RED
        self.sequential = False
        self.tmp_files = False

        # Bind buttons
        self.main_window.cd_ref_prod_btn.clicked.connect(self.open_ref_prod)
        self.main_window.cd_prod_count.clicked.connect(self.open_cmp_prods)
        self.main_window.cd_outdir_btn.clicked.connect(self.sel_output_dir)
        self.main_window.cd_process_btn.clicked.connect(self.launch_detector)

        # Bind comboboxes
        cd_subset_type: QComboBox = self.main_window.cd_subset_type
        cd_subset_type.currentTextChanged.connect(self.enable_subset_input)

    def enable_subset_input(self, value):
        """
        Enables and disables the subset text box.
        :param value: str. Yes or No.
        :return: None.
        """
        cd_subset_str: QLineEdit = self.main_window.cd_subset_str
        if value == "Yes":
            cd_subset_str.setEnabled(True)
        else:
            cd_subset_str.setEnabled(False)

    def launch_detector(self):
        """
        Launches the change detector.
        :return: None.
        """
        self.get_subset_input()
        self.get_sequential_input()
        self.get_tmp_files_input()

        if not self.ref_prod_path:
            warning_dialog("You must select a reference product first.")
            return

        # Check if output dir is set
        if not self.out_dir:
            warning_dialog("Please select an output directory first.")
            return

        # Check if products have been selected
        if len(self.prod_paths) < 1:
            warning_dialog("Please select at least one product to compare to first.")
            return

        self.detector = ChangeDetector(subset=self.subset, ref_prod=self.ref_prod_path, sequential=self.sequential,
                                       ref_chnl=self.ref_color, out_dir=self.out_dir, steps=self.tmp_files)

        if not self.prod_paths:
            warning_dialog("You must select products to compare first.")
            return

        self.display_status("Processing...")
        start = datetime.now()
        self.detector.detect(*self.prod_paths)
        end = datetime.now()
        self.display_status(f"Complete. {end - start}")

    def sel_output_dir(self):
        """
        Sets the output directory path.
        :return: None.
        """
        path = set_dir(self.main_window)
        if not path:
            return
        else:
            self.out_dir = path
            self.display_outputdir_path()

    def open_cmp_prods(self):
        """
        Sets the products to compare with the reference product. Opens a file selecting dialog.
        :return: None.
        """
        paths = load_products(self.main_window)[0]
        if not paths:
            return
        else:
            df = ChangeDetector.order_by_name(*paths)
            self.prod_paths = df["abspath"].tolist()
            self.display_prod_count()

    def open_ref_prod(self):
        """
        Opens file seleciton window to choose the reference product.
        :return: None.
        """
        path = load_product(self.main_window)[0]
        if not path:
            return
        else:
            self.ref_prod_path = path
            self.display_ref_prod_path()

    def display_ref_prod_path(self):
        """
        Displays the path to the reference product on the GUI.
        :return: None.
        """
        path_lbl: QLabel = self.main_window.cd_ref_prod_path

        if self.ref_prod_path:
            prod_basename = os.path.splitext(os.path.basename(self.ref_prod_path))[0]

            path_lbl.setText(prod_basename)

        else:
            path_lbl.setText("No product selected.")

    def display_prod_count(self):
        """
        Displays the selected product count.
        :return: None.
        """
        cd_prod_sel: QLabel = self.main_window.cd_prod_sel

        if self.prod_paths:
            cd_prod_sel.setText(f"{len(self.prod_paths)}")

        else:
            cd_prod_sel.setText("No products selected.")

    def display_outputdir_path(self):
        """
        Displays the output directory path on the GUI.
        :return: None.
        """
        cd_outdir_path: QLabel = self.main_window.cd_outdir_path

        if self.out_dir:
            basename = os.path.basename(self.out_dir)
            cd_outdir_path.setText(basename)

        else:
            cd_outdir_path.setText("No output directory selected.")

    def display_status(self, message):
        """
        Sets the status message on the GUI.
        :param message: Message to display.
        :return: None.
        """
        cd_status_lbl: QLabel = self.main_window.cd_status_lbl
        cd_status_lbl.setText(message)

    def get_subset_input(self):
        """
        Gets the subset polygon input.
        :return: None.
        """
        cd_subset_str: QLineEdit = self.main_window.cd_subset_str.text()

        if cd_subset_str:
            try:
                shapely.wkt.loads(cd_subset_str)
            except shapely.errors.WKTReadingError as e:
                warning_dialog(e.message)
                return

        self.subset = cd_subset_str

    def get_sequential_input(self):
        """
        Get the input related to the sequential execution.
        :return: None.
        """
        cd_seq_cbox: QComboBox = self.main_window.cd_seq_cbox
        self.sequential = True if cd_seq_cbox.currentText() == "Yes" else False

    def get_tmp_files_input(self):
        """
        Gets the chosen input related to saving temporary/intermediary files.
        :return: None.
        """
        cd_tmp_files_cbox: QComboBox = self.main_window.cd_tmp_files_cbox
        self.tmp_files = True if cd_tmp_files_cbox.currentText() == "Yes" else False
