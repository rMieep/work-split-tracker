from typing import Callable

from application.models import Settings
from db import SettingsRepository


class SettingsNotifier:
    """
        Class that provides the current settings as well as notifies subscribes when settings change
    """
    def __init__(self, settings_repository: SettingsRepository):
        self._settings_repository = settings_repository
        self._settings = settings_repository.get()
        self._change_listener = []

    @property
    def work_time(self) -> int:
        return self._settings.work_time

    @work_time.setter
    def work_time(self, work_time: int):
        self._settings.work_time = work_time
        self._settings_repository.update(self._settings)
        self._notify()

    @property
    def break_time(self) -> int:
        return self._settings.break_time

    @break_time.setter
    def break_time(self, break_time: int):
        self._settings.break_time = break_time
        self._settings_repository.update(self._settings)
        self._notify()

    @property
    def play_sound(self) -> bool:
        return self._settings.play_sound

    @play_sound.setter
    def play_sound(self, play_sound: bool):
        self._settings.play_sound = play_sound
        self._settings_repository.update(self._settings)
        self._notify()

    @property
    def show_notification(self) -> bool:
        return self._settings.show_notification

    @show_notification.setter
    def show_notification(self, show_notification: bool):
        self._settings.show_notification = show_notification
        self._settings_repository.update(self._settings)
        self._notify()

    def _notify(self):
        for listener in self._change_listener:
            listener(self._settings)

    def add_change_listener(self, listener: Callable[[Settings], None]):
        self._change_listener.append(listener)
