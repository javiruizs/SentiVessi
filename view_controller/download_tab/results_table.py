"""Module in charge of the results table of the GUI."""

import pandas
from PyQt5.QtCore import QAbstractTableModel, Qt, QVariant
from PyQt5.QtGui import QPixmap


class ResultsModel(QAbstractTableModel):
    """
    Custom implementation of a PyQt table, so it fulfills with our purpose.
    Encapsulates a dataframe as a data container.
    """

    def __init__(self, data: pandas.DataFrame, parent=None):
        super().__init__(parent)
        self._data = data

    def rowCount(self, parent=None):
        """
        Returns the total row count.
        :param parent: optional. Parent. Defaults to None.
        :return: int. Number of rows.
        """
        return len(self._data.values)

    def columnCount(self, parent=None):
        """
        Returns the total column count.
        :param parent: optional. Parent. Defaults to None.
        :return: int. Number of columns.
        """
        return self._data.columns.size

    def data(self, index, role=Qt.DisplayRole):
        """
        Overridden method used to display data.
        :param index: int. Col index.
        :param role: Display role. Optional.
        :return: The value to display.
        """
        if index.isValid():
            if role == Qt.DisplayRole and self._data.columns[index.column()] != "Preview":
                return QVariant(str(self._data.iloc[index.row()][index.column()]))
            elif role == Qt.DecorationRole and self._data.columns[index.column()] == "Preview":
                # https://stackoverflow.com/questions/24201822/show-image-in-a-column-of-qtableview-from-qsqltablemodel
                image = QPixmap(self._data.iloc[index.row()][index.column()]).scaledToHeight(50)
                return image

        return QVariant()

    def headerData(self, col: int, orientation: Qt.Orientation, role: int):
        """
        Returns the headers.
        :param col: int. Column index.
        :param orientation: Orientation.
        :param role: int. Role.
        :return: str. The column name.
        """
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._data.columns[col]
        return None

    def get_sel_uuids(self, indices):
        """
        Returns the selected row uuids.
        :param indices: Row indices.
        :return: list of UUIDs.
        """
        return self._data.iloc[indices].index
