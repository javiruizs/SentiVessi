"""Module dedicated to the download tab."""
import io
import json
import os.path
import shutil
from itertools import compress

import folium
import pandas as pd
from PyQt5 import QtWidgets, Qt
from PyQt5.QtCore import QDate
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QSizePolicy, QTableView
from folium import Map, GeoJson, LayerControl

import utils
from model import Downloader
from .results_table import ResultsModel
from ..utils import warning_dialog, information_dialog, save_json_path, open_json_path, yes_no_dialog, save_csv_path, \
    set_dir


class DownloaderTab:
    """Class that manages the download UI and model."""

    def __init__(self, main_window):
        self.main_window = main_window
        self.downloader: Downloader = None
        self.results = None
        self.model: ResultsModel = None
        self.tmp_dir = ".tmp"

        # Initialize the map
        self.map = None
        self.clear_map()
        self.map_view = QWebEngineView()
        main_window.map_gb.layout().addWidget(self.map_view)
        self.map_view.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.update_map()

        # Buttons
        main_window.dlr_aoi_load_btn.clicked.connect(self.load_aoi)
        main_window.srch_btn.clicked.connect(self.search)
        main_window.save_results_btn.clicked.connect(self.save_results)
        main_window.dlr_start_btn.clicked.connect(self.download)
        main_window.clear_results_btn.clicked.connect(self.clear_table)
        main_window.load_q_btn.clicked.connect(self.load_query)
        main_window.save_q_btn.clicked.connect(self.save_query)

    def load_query(self):
        """Loads query to the GUI.

        :return: None.
        """
        path = open_json_path(self.main_window)[0]
        if not path:
            return

        try:
            with open(path) as f:
                vals = json.load(f)
        except OSError:
            warning_dialog(f"Query couldn't be loaded from {path}. File might be in use by another program.")

        # Parameters extraction
        try:
            self.set_start_date(vals["start"])
            self.set_end_date(vals["end"])
            self.set_platformname(vals["platform"])
            self.set_prodtype(vals["prod_type"])
            self.set_orbit_dir(vals["orb_dir"])
            self.set_relative_orbit(vals["rel_orbit"])
            self.set_aoi(vals["aoi"])
            self.set_aoi_pct(vals["aoi_pct"])
            self.set_same_datatake(vals["same_datatake"])

            self.load_aoi()
        except KeyError:
            warning_dialog("Invalid JSON format.")
            return

    def save_query(self):
        """Saves the inputs in the query fields to a JSON file.

        :return: None.
        """
        # Parameters extraction
        start = self.get_start_date()
        end = self.get_end_date()
        platform = self.get_platformname()
        prod_type = self.get_prodtype()
        orb_dir = self.get_orbit_dir()
        rel_orbit = self.get_relative_orbit()
        aoi = self.get_aoi()
        aoi_pct = self.get_aoi_pct()
        same_datatake = self.get_same_datatake()

        js = {
            "start": start,
            "end": end,
            "platform": platform,
            "prod_type": prod_type,
            "orb_dir": orb_dir,
            "rel_orbit": rel_orbit,
            "aoi": aoi,
            "aoi_pct": aoi_pct,
            "same_datatake": same_datatake
        }

        path = save_json_path(self.main_window)[0]
        if not path:
            return

        try:
            with open(path, 'w') as f:
                json.dump(js, f, indent=2)
        except OSError:
            warning_dialog(f"Query couldn't be saved to {path}. File might be use by another program.")

    def load_aoi(self):
        """Loads AoI WKT to the map

        :return: WKT object or none.
        """

        # AoI drawing style
        aoi_style = lambda feature: {
            'fillOpacity': 0.3,
            'weight': 2,
            'fillColor': '#00FF00'
        }

        aoi = self.get_aoi()
        if not aoi:  # If aoi == "", then return.
            return

        aoi = utils.test_wkt(aoi)  # Test WKT format
        if not aoi:
            warning_dialog("The Given AoI has an iinvalid format.")
            return

        self.clear_map()  # Clears map

        gjson = folium.GeoJson(aoi, style_function=aoi_style, name="AOI")  # Creates AoI layer with the given style
        gjson.add_to(self.map)  # Adds it to the map

        self.map.location = list(aoi.centroid.coords)[0][::-1]  # Centers the map with the AoI centroid
        self.map.fit_bounds(gjson.get_bounds())  # Sets the bounds so it's zoomed out and the whole figure appears.
        self.update_map()  # Updates map

        return aoi

    def search(self):
        """Launches the search with the given parameters

        :return: None.
        """

        if not self.downloader:  # Checks whether the user is already logged in.
            warning_dialog("Please, login first.")
            return

        # Parameters extraction
        start = self.get_start_date()
        end = self.get_end_date()
        platform = self.get_platformname()
        prod_type = self.get_prodtype()
        orb_dir = self.get_orbit_dir()
        rel_orbit = self.get_relative_orbit()
        aoi = self.get_aoi()
        aoi_pct = self.get_aoi_pct()
        same_datatake = self.get_same_datatake()

        # Parameters conversion
        if not self.load_aoi():
            return

        if rel_orbit:  # If there was an input
            rel_orbit = int(rel_orbit)
        else:
            rel_orbit = None

        if orb_dir == "Both":
            orb_dir = None

        if aoi_pct == 100:
            area_relation = "Contains"
        else:
            area_relation = "Intersects"

        results = self.downloader.query(aoi, start, end, relative_orbit=rel_orbit, platformname=platform,
                                        area_relation=area_relation, producttype=prod_type, orbitdirection=orb_dir)

        results = self.downloader.filter_by_aoi_pct(results, aoi, aoi_pct, same_datatake=same_datatake)

        self.results = results

        if results.empty:
            information_dialog("No results matched your query.")
            return

        """
        Download quicklook temporarily
        """
        if not os.path.isdir(self.tmp_dir):
            os.mkdir(self.tmp_dir)

        quicklooks = [os.path.join(self.tmp_dir, x + '.jpeg') for x in results["identifier"]]
        results["quicklooks"] = quicklooks

        exist = [not os.path.isfile(f) for f in quicklooks]

        to_download = list(compress(quicklooks, exist))

        if to_download:
            prod_dict = Downloader.to_dict(results[results["quicklooks"].isin(to_download)], True)
            self.downloader.download_all_quicklooks(prod_dict, self.tmp_dir)

        self.add_prods_to_map(results)

        self.add_prods_to_table(results)

    def add_prods_to_table(self, results):
        """
        Adds the products obtained after a query to the result table.
        :param results: Result dataframe.
        """
        results = results[["beginposition", "satellite", "orbitdirection", "missiondatatakeid", "relativeorbitnumber",
                           "aoicoverage", "access", "quicklooks"]]

        results.rename(columns={
            "beginposition": "Date",
            "satellite": "Satellite",
            "orbitdirection": "Orb. Dir.",
            "missiondatatakeid": "Datatake",
            "relativeorbitnumber": "Rel. orbit",
            "aoicoverage": "AoI coverage (%)",
            "quicklooks": "Preview"
        }, inplace=True)

        self.model = ResultsModel(results)
        self.main_window.rslts_tbl.setModel(self.model)
        self.main_window.rslts_tbl.setSelectionBehavior(QtWidgets.QTableView.SelectRows)

        # Hide columns
        # for i, col in enumerate(results.columns):
        #     if col not in display_cols:
        #         self.main_window.rslts_tbl.setColumnHidden(i, True)

        self.main_window.rslts_tbl.resizeRowsToContents()
        self.main_window.rslts_tbl.resizeColumnsToContents()

        self.main_window.rslts_tbl.show()

    def add_prods_to_map(self, results):
        """
        Adds the given results to the map.
        :param results: Result dataframe.
        """
        style_me = lambda feature: {
            'fillOpacity': 0.1,
            'weight': 1,
            'fillColor': '#ff0000'
        }

        layer = GeoJson(
            data=results[['geometry', 'title', 'link_icon']],
            style_function=style_me,
            name='Products',
        ).add_to(self.map)

        LayerControl().add_to(self.map)

        self.map.fit_bounds(layer.get_bounds())

        self.update_map()

    def save_results(self):
        """
        Saves the results to a CSV file.
        :return: Results to save.
        """
        if self.results is not None:
            path = save_csv_path(self.main_window)[0]
            if not path:
                return
            self.results.to_csv(path, sep=";", decimal=",")

    def clear_table(self):
        """
        Clears/empties the result table.
        """

        if self.model is not None:
            self.model.beginResetModel()
            self.model._data = pd.DataFrame()
            self.model.endResetModel()
            self.results = None

    def download(self):
        """
        Downloads the selected products.
        :return: None.
        """
        table_view: QTableView = self.main_window.rslts_tbl
        selmodel = table_view.selectionModel()
        if selmodel.hasSelection():
            selection = [i.row() for i in selmodel.selectedRows()]
        elif yes_no_dialog("No rows where selected. Would you like to download all products?"):
            selection = list(range(self.model.rowCount()))
        else:
            return

        sel_df = self.get_selected_rows(selection)

        if "offline" in sel_df["access"].unique():
            file = f"offline_{utils.formatted_ts()}.csv"
            information_dialog("Only online products can be downloaded with this program. To download offline products,"
                               f" please use OAHretriever.py with the generated file {os.path.join(os.getcwd(), file)}.")

            sel_df[sel_df.access == "offline"].to_csv(file, sep=";", decimal=",")

        if "online" not in sel_df["access"].unique():
            warning_dialog("No online products where selected.")
            return

        path = set_dir(self.main_window)
        if not path:
            return

        for f in sel_df[sel_df.access == "online"]["quicklooks"]:
            basename = os.path.split(f)[1]
            new_path = os.path.join(path, basename)
            shutil.copy2(f, new_path)

        self.downloader.download_all(Downloader.to_dict(sel_df[sel_df.access == "online"], True), directory_path=path)

        information_dialog("Download complete.")

    def clear_map(self):
        """
        Clears the map.
        """

        self.map = Map(tiles="Stamen Terrain")

    def update_map(self):
        """
        Updates the map.
        """

        data = io.BytesIO()
        self.map.save(data, close_file=False)
        self.map_view.setHtml(data.getvalue().decode())
        data.close()

    def get_selected_rows(self, indices):
        """
        Extracts the uuids from the selected rows on the result table.
        :param indices: Indices of the selected rows.
        :return: DataFrame.
        """
        return self.results.iloc[indices]

    def get_start_date(self):
        """
        Extracts the starting date from the input field.
        :return: str. Date in the format yyyyMMdd.
        """
        return self.main_window.start_date_2.date().toString("yyyyMMdd")

    def get_end_date(self):
        """
        Extracts the ending date from the input field.
        :return: str. Date in the format yyyyMMdd.
        """
        return self.main_window.end_date_2.date().toString("yyyyMMdd")

    def get_platformname(self):
        """
        Extracts the platformname end from the input field.
        :return: str.
        """
        return self.main_window.pltfrm_cbox_2.currentText()

    def get_prodtype(self):
        """
        Extracts the product type end from the input field.
        :return: str.
        """
        return self.main_window.prod_type_cbox_2.currentText()

    def get_orbit_dir(self):
        """
        Extracts the orbit direction end from the input field.
        :return: str.
        """
        return self.main_window.orb_dir_cbox.currentText()

    def get_relative_orbit(self):
        """
        Extracts the relative orbit end from the input field.
        :return: str.
        """
        return self.main_window.dlr_rel_orb.text()

    def get_aoi(self) -> str:
        """
        Gets the input text from the text field.
        :return: String.
        """
        return self.main_window.aoi_plg_in.text()

    def get_aoi_pct(self):
        """
        Extracts the AoI coverage percent from the input field.
        :return: int.
        """
        return self.main_window.aoi_percent_2.value()

    def set_start_date(self, value):
        """
        Sets the start date in the input field.
        :param value: str. Date in the format of yyyyMMdd.
        :return: None.
        """
        date = QDate.fromString(value, "yyyyMMdd")
        self.main_window.start_date_2.setDate(date)

    def set_end_date(self, value):
        """
        Sets the end date in the input field.
        :param value: str. Date in the format of yyyyMMdd.
        :return: None.
        """
        date = QDate.fromString(value, "yyyyMMdd")
        self.main_window.end_date_2.setDate(date)

    def set_platformname(self, value):
        """
        Sets the platform name in the input field.
        :param value: str. Value to display.
        :return: None.
        """
        i = self.main_window.pltfrm_cbox_2.findText(value)
        self.main_window.pltfrm_cbox_2.setCurrentIndex(i)

    def set_prodtype(self, value):
        """
        Sets the product type in the input field.
        :param value: str. Value to display.
        :return: None.
        """
        i = self.main_window.prod_type_cbox_2.findText(value)
        self.main_window.prod_type_cbox_2.setCurrentIndex(i)

    def set_orbit_dir(self, value):
        """"
        Sets the orbit direction in the input field.
        :param value: str. Value to display.
        :return: None.
        """
        i = self.main_window.orb_dir_cbox.findText(value)
        self.main_window.orb_dir_cbox.setCurrentIndex(i)

    def set_relative_orbit(self, value):
        """
        Sets the relative orbit number in the input field.
        :param value: str. Value to display.
        :return: None.
        """
        self.main_window.dlr_rel_orb.setText(value)

    def set_aoi(self, value):
        """
        Sets the AoI wkt string in the input field.
        :param value: str. Value to display.
        :return: None.
        """
        self.main_window.aoi_plg_in.setText(value)

    def set_aoi_pct(self, value):
        """
        Sets the coverage percent the input field.
        :param value: int. Value to display.
        :return: None.
        """
        self.main_window.aoi_percent_2.setValue(value)

    def get_same_datatake(self):
        """
        Gets the value for the checkbox button on same datatake id filtering.
        :return: Bool.
        """
        return self.main_window.dlr_same_datatake_chk.isChecked()

    def set_same_datatake(self, value: bool):
        """
        Sets the checkbox button on same datatake id filtering.
        :param value: bool. True or False.
        :return: None.
        """
        self.main_window.dlr_same_datatake_chk.setCheckState(Qt.Qt.Checked if value else Qt.Qt.Unchecked)
