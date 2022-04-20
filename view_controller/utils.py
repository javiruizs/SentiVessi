"""Module for utility functions when working with PyQt."""
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QFileDialog, QMessageBox


def set_dir(container):
    """
    Opens a directory path selection window.
    :param container: Parent window. Can be None.
    :return: str. The path to the selected dir.
    """
    dir_name = QFileDialog.getExistingDirectory(container, "Select directory")
    return dir_name


def load_products(container):
    """
    Opens a file selection window to select more than one source products.
    :param container: Parent window. Can be None.
    :return: A list of names.
    """
    file_name = QtWidgets.QFileDialog()
    file_name.setFileMode(QFileDialog.ExistingFiles)
    names = file_name.getOpenFileNames(container, caption="Select the desired products", filter="ZIP (*.zip)")
    return names


def load_product(container):
    """
    Opens a file selection dialog to read just one product.
    :param container: Parent. Can be None.
    :return: Path to the selected file.
    """
    file_name = QtWidgets.QFileDialog()
    file_name.setFileMode(QFileDialog.ExistingFiles)
    name = file_name.getOpenFileName(container, caption="Select the desired product", filter="ZIP (*.zip)")
    return name


def open_json_path(container):
    """
    Opens a file selection dialog to read a JSON product.
    :param container: Parent. Can be None.
    :return: Path to the selected file.
    """
    file_name = QtWidgets.QFileDialog()
    file_name.setFileMode(QFileDialog.ExistingFiles)
    names = file_name.getOpenFileName(container, caption="Select the desired products", filter="JSON (*.json)")
    return names


def save_json_path(container):
    """
    Opens a file selection dialog to save a JSON product.
    :param container: Parent. Can be None.
    :return: Path to the selected file.
    """
    file_name = QtWidgets.QFileDialog()
    file_name.setFileMode(QFileDialog.AnyFile)
    names = file_name.getSaveFileName(container, caption="Select the desired path.", filter="JSON (*.json)")
    return names


def save_csv_path(container):
    """
    Opens a file selection dialog to save a CSV product.
    :param container: Parent. Can be None.
    :return: Path to the selected file.
    """
    file_name = QtWidgets.QFileDialog()
    file_name.setFileMode(QFileDialog.AnyFile)
    names = file_name.getSaveFileName(container, caption="Select the desired path.", filter="CSV (*.csv)")
    return names


def open_cfg_path(container):
    """
    Opens a file selection dialog to read a cfg file.
    :param container: Parent. Can be None.
    :return: Path to the selected file.
    """
    file_name = QtWidgets.QFileDialog()
    file_name.setFileMode(QFileDialog.ExistingFiles)

    file_filter = "Configuration file (*.ini; *.cfg)"

    name = file_name.getOpenFileName(container, caption="Select the desired products", filter=file_filter)
    return name


def warning_dialog(message):
    """
    Opens a warning dialog with the given message.
    :param message: str. Message to display.
    :return: None.
    """
    warning = QMessageBox()
    warning.setIcon(QMessageBox.Warning)
    warning.setText(message)
    warning.setStandardButtons(QMessageBox.Ok)
    warning.exec()


def information_dialog(message):
    """
    Opens a information dialog with the given message.
    :param message: str. Message to display.
    :return: None.
    """
    warning = QMessageBox()
    warning.setIcon(QMessageBox.Information)
    warning.setText(message)
    warning.setStandardButtons(QMessageBox.Ok)
    warning.exec()


def critical_dialog(message):
    """
    Opens a cirtical error dialog with the given message.
    :param message: str. Message to display.
    :return: None.
    """
    warning = QMessageBox()
    warning.setIcon(QMessageBox.Critical)
    warning.setText(message)
    warning.setStandardButtons(QMessageBox.Ok)
    warning.exec()


def yes_no_dialog(question):
    """
    Opens a yes or no dialog with the given message.
    :param question: str. Message to display.
    :return: None.
    """
    qm = QMessageBox()
    if qm.question(None, "", question, qm.Yes | qm.No) == qm.Yes:
        return True
    else:
        return False
