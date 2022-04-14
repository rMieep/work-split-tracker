from abc import ABC, abstractmethod

from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject
from PyQt5.QtWidgets import QCheckBox, QFormLayout, QLabel, QPushButton, QSpinBox, QVBoxLayout, QWidget

from application.settings import SettingsNotifier
from gui.windows.mainwindow import AbstractWindow


class SettingsModel(QObject):
    """
        Model of the settings window
    """
    work_time_changed = pyqtSignal(int)
    break_time_changed = pyqtSignal(int)
    show_notification_changed = pyqtSignal(bool)
    play_sound_changed = pyqtSignal(bool)

    def __init__(self):
        super(SettingsModel, self).__init__()

        self._work_time_value = 20
        self._break_time_value = 5
        self._show_notification_value = True
        self._play_sound_value = False

    @property
    def work_time_label(self) -> str:
        return "Work minutes"

    @property
    def break_time_label(self) -> str:
        return "Break minutes"

    @property
    def show_notification_label(self) -> str:
        return "Show notification"

    @property
    def play_sound_label(self) -> str:
        return "Play sound"

    @property
    def save_label(self) -> str:
        return "Save"

    @property
    def work_time(self) -> int:
        return self._work_time_value

    @work_time.setter
    def work_time(self, work_time: int):
        self._work_time_value = work_time
        self.work_time_changed.emit(work_time)

    @property
    def break_time(self) -> int:
        return self._break_time_value

    @break_time.setter
    def break_time(self, break_time: int):
        self._break_time_value = break_time
        self.break_time_changed.emit(break_time)

    @property
    def show_notification(self) -> bool:
        return self._show_notification_value

    @show_notification.setter
    def show_notification(self, show: bool):
        self._show_notification_value = show
        self.show_notification_changed.emit(show)

    @property
    def play_sound(self) -> bool:
        return self._play_sound_value

    @play_sound.setter
    def play_sound(self, play: bool):
        self._play_sound_value = play
        self.play_sound_changed.emit(play)


class SettingsController(QObject):
    """
        Controller of the settings window
    """
    def __init__(self, notifier: SettingsNotifier, model: SettingsModel):
        super(SettingsController, self).__init__()

        self._model = model
        self._notifier = notifier
        self._init_settings()
        
    def _init_settings(self):
        self._model.work_time = self._notifier.work_time
        self._model.break_time = self._notifier.break_time
        self._model.show_notification = self._notifier.show_notification
        self._model.play_sound = self._notifier.play_sound

    @pyqtSlot(int)
    def on_work_time_change(self, minutes: int):
        self._model.work_time = minutes

    @pyqtSlot(int)
    def on_break_time_change(self, minutes: int):
        self._model.break_time = minutes

    @pyqtSlot(int)
    def on_show_notification_change(self, show: int):
        self._model.show_notification = show != 0

    @pyqtSlot(int)
    def on_play_sound_change(self, play: int):
        self._model.play_sound = play != 0
    
    @pyqtSlot()
    def on_save_clicked(self):
        if self._model.work_time != self._notifier.work_time:
            self._notifier.work_time = self._model.work_time
            
        if self._model.break_time != self._notifier.break_time:
            self._notifier.break_time = self._model.break_time
            
        if self._model.show_notification != self._notifier.show_notification:
            self._notifier.show_notification = self._model.show_notification
            
        if self._model.play_sound != self._notifier.play_sound:
            self._notifier.play_sound = self._model.play_sound


class SettingsView(QWidget):
    """
        View of the settings window
    """
    def __init__(self, controller: SettingsController, model: SettingsModel):
        super(SettingsView, self).__init__()

        self._controller = controller
        self._model = model

        self._work_time_label = QLabel(text=self._model.work_time_label, parent=self)
        self._work_time_field = QSpinBox(parent=self)

        self._break_time_label = QLabel(text=self._model.break_time_label, parent=self)
        self._break_time_field = QSpinBox(parent=self)

        self._show_notification_label = QLabel(text=self._model.show_notification_label, parent=self)
        self._show_notification_field = QCheckBox(parent=self)

        self._play_sound_label = QLabel(text=self._model.play_sound_label, parent=self)
        self._play_sound_field = QCheckBox(parent=self)

        self._save_button = QPushButton(text=self._model.save_label, parent=self)

        self._init_state()
        self._init_bindings()
        self._init_layout()

    def _init_state(self):
        self._work_time_field.setRange(1, 59)
        self._work_time_field.setValue(self._model.work_time)

        self._break_time_field.setRange(1, 59)
        self._break_time_field.setValue(self._model.break_time)

        self._show_notification_field.setChecked(self._model.show_notification)

        self._play_sound_field.setChecked(self._model.play_sound)

    def _init_bindings(self):
        self._work_time_field.valueChanged.connect(self._controller.on_work_time_change)
        self._break_time_field.valueChanged.connect(self._controller.on_break_time_change)
        self._show_notification_field.stateChanged.connect(self._controller.on_show_notification_change)
        self._play_sound_field.stateChanged.connect(self._controller.on_play_sound_change)
        self._save_button.pressed.connect(self._controller.on_save_clicked)

        self._model.work_time_changed.connect(self._on_work_time_changed)
        self._model.break_time_changed.connect(self._on_break_time_changed)
        self._model.show_notification_changed.connect(self._on_show_notification_changed)
        self._model.play_sound_changed.connect(self._on_play_sound_changed)

    def _init_layout(self):
        layout = QFormLayout(self)

        layout.addRow(self._work_time_label, self._work_time_field)
        layout.addRow(self._break_time_label, self._break_time_field)
        layout.addRow(self._show_notification_label, self._show_notification_field)
        layout.addRow(self._play_sound_label, self._play_sound_field)
        layout.addRow(None, self._save_button)

    @pyqtSlot(int)
    def _on_work_time_changed(self, minutes: int):
        self._work_time_field.setValue(minutes)

    @pyqtSlot(int)
    def _on_break_time_changed(self, minutes: int):
        self._break_time_field.setValue(minutes)

    @pyqtSlot(bool)
    def _on_show_notification_changed(self, show: bool):
        self._show_notification_field.setChecked(show)

    @pyqtSlot(bool)
    def _on_play_sound_changed(self, play: bool):
        self._play_sound_field.setChecked(play)


class SettingsWindow(AbstractWindow):
    """
        Window allowing the user to edit the app settings
        The window implements the MVC pattern.
    """
    def __init__(self, notifier: SettingsNotifier):
        super(SettingsWindow, self).__init__()

        self._model = SettingsModel()
        self._controller = SettingsController(notifier, self._model)
        self._view = SettingsView(self._controller, self._model)

        layout = QVBoxLayout(self)
        layout.addWidget(self._view)
        self.setLayout(layout)

        self._center()


class SettingsFactory(ABC):
    @abstractmethod
    def create(self) -> SettingsWindow:
        raise NotImplementedError


class SettingsFactoryImpl(SettingsFactory):
    def __init__(self, notifier: SettingsNotifier):
        self._notifier = notifier

    def create(self) -> SettingsWindow:
        return SettingsWindow(self._notifier)
