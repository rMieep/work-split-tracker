from abc import ABC, abstractmethod
from enum import auto, Enum
from typing import Callable, Dict

from PyQt5.QtCore import QTimer
from playsound import playsound
from plyer import notification
from plyer.utils import platform
from sortedcontainers import SortedList

import utils
from application.app import execute_priority_callbacks, WSTContext, WSTState, PriorityCallback
from application.models import Settings
from application.settings import SettingsNotifier


class Timer(ABC):
    """Provides an interface for a timer that repeatedly executes a task for a defined interval."""

    def __init__(self, task: Callable[[], None] = lambda: None, interval: int = 1000):
        """
        Args:
            task: callable
                a callback function that should be executed every interval.
            interval: int
                Time in milliseconds after which the task should be repeatedly executed.

        """
        self._task = task
        self._interval = interval

    @property
    def task(self):
        return self._task

    @task.setter
    def task(self, task: Callable):
        self._task = task

    @abstractmethod
    def start(self):
        raise NotImplementedError

    @abstractmethod
    def stop(self):
        raise NotImplementedError

    def is_active(self) -> bool:
        raise NotImplementedError


class QTimerAdapter(Timer):
    """
        Timer implementation using the QTimer class provided by the PyQt framework
    """
    def __init__(self, task: Callable[[], None] = lambda: None, interval: int = 1000):
        super(QTimerAdapter, self).__init__(task, interval)
        self._timer = QTimer()
        self._timer.interval = self._interval

    @Timer.task.setter
    def task(self, task: Callable):
        self._task = task
        if not self._task:
            self._timer.timeout.disconnect()
        self._timer.timeout.connect(self.task)

    def start(self):
        self._timer.start(self._interval)

    def stop(self):
        self._timer.stop()

    def is_active(self) -> bool:
        return self._timer.isActive()


class IllegalCountdownTimerStateException(Exception):
    pass


class WSTCountdownTimerIdentifier(Enum):
    WORK = auto()
    BREAK = auto()


class CountdownTimerContext:
    """
        Context of the CountdownTimer
    """
    def __init__(self):
        self.seconds_left = 0
        self._alarm_callbacks = {}
        self._tick_callbacks = {}

    @staticmethod
    def _push_identifier_callback(state_callback_dict: Dict[WSTCountdownTimerIdentifier, SortedList],
                                  identifier: WSTCountdownTimerIdentifier, callback: PriorityCallback):
        if identifier not in state_callback_dict:
            state_callback_dict[identifier] = SortedList()

        state_callback_dict[identifier].add(callback)

    def execute_alarm_callbacks(self, identifier: WSTCountdownTimerIdentifier):
        priority_callback_list = self._alarm_callbacks.get(identifier)

        if priority_callback_list:
            execute_priority_callbacks(priority_callback_list, self)

    def execute_tick_callbacks(self, identifier: WSTCountdownTimerIdentifier):
        priority_callback_list = self._tick_callbacks.get(identifier)

        if priority_callback_list:
            execute_priority_callbacks(priority_callback_list, self)

    def push_alarm_identifier_callback(self, identifier: WSTCountdownTimerIdentifier, callback: PriorityCallback):
        self._push_identifier_callback(self._alarm_callbacks, identifier, callback)

    def remove_alarm_identifier_callback(self, identifier: WSTCountdownTimerIdentifier, callback: PriorityCallback):
        self._alarm_callbacks[identifier].remove(callback)

    def push_tick_identifier_callback(self, identifier: WSTCountdownTimerIdentifier, callback: PriorityCallback):
        self._push_identifier_callback(self._tick_callbacks, identifier, callback)

    def remove_tick_identifier_callback(self, identifier: WSTCountdownTimerIdentifier, callback: PriorityCallback):
        self._tick_callbacks[identifier].remove(callback)


class CountdownTimer:
    """
        A timer that countdown from a predefined number of seconds and triggers an alarm if it hits zero
        Once the timer hits zero it continues to count negative
    """
    def __init__(self, identifier: WSTCountdownTimerIdentifier, timer: Timer, context: CountdownTimerContext,
                 seconds: int):
        self._identifier = identifier
        self._timer = timer
        self._context = context
        self._context.push_tick_identifier_callback(self._identifier, PriorityCallback(self._update_seconds_left, 5))
        self._context.push_tick_identifier_callback(self._identifier, PriorityCallback(self._trigger_alarm, 4))
        self._timer.task = self._tick_callback
        self._seconds = seconds

    @property
    def seconds(self):
        return self._seconds

    @seconds.setter
    def seconds(self, seconds: int):
        if self._timer.is_active():
            raise IllegalCountdownTimerStateException

        self._seconds = seconds

    @staticmethod
    def _update_seconds_left(context: CountdownTimerContext):
        context.seconds_left = context.seconds_left - 1

    def _is_alarm(self) -> bool:
        return self._context.seconds_left == 0

    def _trigger_alarm(self, context: CountdownTimerContext):
        if self._is_alarm():
            context.execute_alarm_callbacks(self._identifier)

    def _tick_callback(self):
        self._context.execute_tick_callbacks(self._identifier)

    def start(self):
        if self._timer.is_active():
            raise IllegalCountdownTimerStateException()

        self._timer.start()

    def stop(self) -> int:
        if not self._timer.is_active():
            raise IllegalCountdownTimerStateException()

        self._timer.stop()
        seconds_left = self._context.seconds_left
        self._reset()

        return seconds_left

    def _reset(self):
        self._seconds_left = self._seconds


class CountdownTimerController:
    """
        Controller of the Break- and WorkCountdownTimer that starts and stops the corresponding timers.
        Handles settings changes and configures the timer accordingly.
    """
    def __init__(self, wst_context: WSTContext, timer_context: CountdownTimerContext,
                 settings_notifier: SettingsNotifier):
        self._app_context = wst_context
        self._countdown_timer_context = timer_context
        self._show_notification = settings_notifier.show_notification
        self._play_sound = settings_notifier.play_sound
        self._timer = {
            WSTCountdownTimerIdentifier.WORK: CountdownTimer(
                identifier=WSTCountdownTimerIdentifier.WORK,
                timer=QTimerAdapter(),
                context=self._countdown_timer_context,
                seconds=settings_notifier.work_time * 60
            ),
            WSTCountdownTimerIdentifier.BREAK: CountdownTimer(
                identifier=WSTCountdownTimerIdentifier.BREAK,
                timer=QTimerAdapter(),
                context=self._countdown_timer_context,
                seconds=settings_notifier.break_time * 60
            )
        }

        self._app_context.work_time = settings_notifier.work_time
        self._app_context.break_time = settings_notifier.break_time

        settings_notifier.add_change_listener(self._handle_work_time_change)
        settings_notifier.add_change_listener(self._handle_break_time_change)
        settings_notifier.add_change_listener(self._handle_show_notification_change)
        settings_notifier.add_change_listener(self._handle_play_sound_change)

        self._app_context.push_after_state_change_callback(WSTState.WORK, PriorityCallback(self._start_work_timer, 1))
        self._app_context.push_after_state_change_callback(WSTState.BREAK, PriorityCallback(self._start_break_timer, 1))
        self._app_context.push_after_state_change_callback(
            WSTState.WORK, PriorityCallback(self._set_work_timer_seconds_left, 4))
        self._app_context.push_after_state_change_callback(
            WSTState.BREAK, PriorityCallback(self._set_break_timer_seconds_left, 4))
        self._app_context.push_before_state_change_callback(WSTState.WORK, PriorityCallback(self._stop_work_timer, 5))
        self._app_context.push_before_state_change_callback(WSTState.BREAK, PriorityCallback(self._stop_break_timer, 5))

        self._countdown_timer_context.push_alarm_identifier_callback(
            WSTCountdownTimerIdentifier.WORK,
            PriorityCallback(self._show_work_timer_notification_callback, 1)
        )
        self._countdown_timer_context.push_alarm_identifier_callback(
            WSTCountdownTimerIdentifier.WORK,
            PriorityCallback(self._play_sound_callback, 1)
        )
        self._countdown_timer_context.push_alarm_identifier_callback(
            WSTCountdownTimerIdentifier.BREAK,
            PriorityCallback(self._show_break_timer_notification_callback, 1)
        )
        self._countdown_timer_context.push_alarm_identifier_callback(
            WSTCountdownTimerIdentifier.BREAK,
            PriorityCallback(self._play_sound_callback, 1)
        )

    @property
    def timer_context(self) -> CountdownTimerContext:
        return self._countdown_timer_context

    def _set_work_timer_seconds_left(self, context: WSTContext):
        self._countdown_timer_context.seconds_left = self._timer[WSTCountdownTimerIdentifier.WORK].seconds

    def _set_break_timer_seconds_left(self, context: WSTContext):
        self._countdown_timer_context.seconds_left = self._timer[WSTCountdownTimerIdentifier.BREAK].seconds

    def _stop_work_timer(self, context: WSTContext):
        context.stop_time = self._timer[WSTCountdownTimerIdentifier.WORK].stop()

    def _stop_break_timer(self, context: WSTContext):
        context.stop_time = self._timer[WSTCountdownTimerIdentifier.BREAK].stop()

    def _start_work_timer(self, context: WSTContext):
        self._timer[WSTCountdownTimerIdentifier.WORK].start()

    def _start_break_timer(self, context: WSTContext):
        self._timer[WSTCountdownTimerIdentifier.BREAK].start()

    def _handle_work_time_change(self, settings: Settings):
        self._timer[WSTCountdownTimerIdentifier.WORK].seconds = settings.work_time * 60
        self._app_context.work_time = settings.work_time

    def _handle_break_time_change(self, settings: Settings):
        self._timer[WSTCountdownTimerIdentifier.BREAK].seconds = settings.break_time * 60
        self._app_context.break_time = settings.break_time

    def _handle_show_notification_change(self, settings: Settings):
        if settings.show_notification != self._show_notification:
            self._show_notification = settings.show_notification

    def _handle_play_sound_change(self, settings: Settings):
        if settings.play_sound != self._play_sound:
            self._play_sound = settings.play_sound

    def _show_notification_callback(self, timer_type: str):
        if self._show_notification:
            notification.notify(
                title="Alarm",
                message=f"Your {timer_type} time is over!",
                app_name="Work Split Tracker",
                app_icon=utils.resource_provider.image("211694_bell_icon" + (".ico" if platform == "win" else ".png"))
            )

    def _show_work_timer_notification_callback(self, context: CountdownTimerContext):
        self._show_notification_callback("work")

    def _show_break_timer_notification_callback(self, context: CountdownTimerContext):
        self._show_notification_callback("break")

    def _play_sound_callback(self, context: CountdownTimerContext):
        if self._play_sound:
            playsound(utils.resource_provider.sound("notification.wav"))
