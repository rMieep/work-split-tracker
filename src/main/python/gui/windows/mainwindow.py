from PyQt5 import QtGui
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget

import utils


class AbstractWindow(QWidget):
    """
        Abstract window that sets the title, icon, provides a close signal and an utility method to center the window
    """
    about_to_close = pyqtSignal()

    def __init__(self):
        super(AbstractWindow, self).__init__()
        self.setWindowTitle("Work Split Tracker")
        self.setWindowIcon(QIcon(utils.resource_provider.image("tray_icon.png")))

    def _center(self):
        frameGm = self.frameGeometry()
        centerPoint = QtGui.QGuiApplication.primaryScreen().availableGeometry().center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.about_to_close.emit()
        super().closeEvent(event)
