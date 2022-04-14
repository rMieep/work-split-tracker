from abc import ABC, abstractmethod

from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QLabel, QPushButton, QVBoxLayout


class ConfirmDialog(QDialog):
    """
        Simple dialog used to get confirmation from the user for an action.
    """
    def __init__(self, title: str, message: str):
        super(ConfirmDialog, self).__init__()

        self.setWindowTitle(title)

        self._reject_button = QPushButton(text="Cancel", parent=self)
        self._confirm_button = QPushButton(text="Confirm", parent=self)

        self._button_box = QDialogButtonBox()
        self._button_box.addButton(self._reject_button, QDialogButtonBox.ButtonRole.RejectRole)
        self._button_box.addButton(self._confirm_button, QDialogButtonBox.ButtonRole.AcceptRole)
        self._button_box.accepted.connect(self.accept)
        self._button_box.rejected.connect(self.reject)

        self._layout = QVBoxLayout()

        self._message_box = QLabel(message)

        self._layout.addWidget(self._message_box)
        self._layout.addWidget(self._button_box)

        self.setLayout(self._layout)


class ConfirmDialogFactory(ABC):
    @abstractmethod
    def create(self, title: str, message: str):
        raise NotImplementedError


class ConfirmDialogFactoryImpl(ConfirmDialogFactory):
    def create(self, title: str, message: str):
        return ConfirmDialog(title=title, message=message)
