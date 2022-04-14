from datetime import datetime

from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMenu, QSystemTrayIcon

import utils
from application.app import WorkSplitTracker, WSTContext, WSTState
from application.models import BreakActivity, WorkActivity
from application.settings import SettingsNotifier
from application.timer import CountdownTimerContext, CountdownTimerController, PriorityCallback, \
    WSTCountdownTimerIdentifier
from gui.activity import ActivityTableModel
from gui.windows.analytics import AnalyticsFactory, AnalyticsWindow
from gui.windows.backlog import BacklogFactory, BacklogWindow
from gui.windows.log import LogFactory, LogWindow
from gui.windows.settings import SettingsFactory, SettingsWindow
from gui.windows.timer import CountdownTimerFactory, CountdownTimerWindow


class TrayModel(QObject):
    """
        Model of the tray
    """
    timer_label_changed = pyqtSignal(str)
    work_action_hidden_changed = pyqtSignal(bool)
    break_action_hidden_changed = pyqtSignal(bool)
    idle_action_enabled_changed = pyqtSignal(bool)

    def __init__(
            self,
            app: QApplication,
            timer_factory: CountdownTimerFactory,
            backlog_factory: BacklogFactory,
            analytics_factory: AnalyticsFactory,
            log_factory: LogFactory,
            settings_factory: SettingsFactory
    ):
        super(TrayModel, self).__init__()

        self._app = app
        self._timer_factory = timer_factory
        self._backlog_factory = backlog_factory
        self._analytics_factory = analytics_factory
        self._log_factory = log_factory
        self._settings_factory = settings_factory

        # window reference needed while window open as otherwise it is going to be garbage collected
        self._timer_window = None
        self._backlog_window = None
        self._analytics_window = None
        self._log_window = None
        self._settings_window = None

        self._timer_label = "Timer: -"
        
        self._work_action_hidden = False
        self._break_action_hidden = True
        self._idle_action_enabled = False

    @property
    def app(self) -> QApplication:
        return self._app

    @property
    def timer_label(self) -> str:
        return self._timer_label

    @timer_label.setter
    def timer_label(self, label: str):
        self._timer_label = label
        self.timer_label_changed.emit(label)

    @property
    def work_label(self) -> str:
        return "Work"

    @property
    def break_label(self) -> str:
        return "Break"

    @property
    def idle_label(self) -> str:
        return "Idle"

    @property
    def backlog_label(self) -> str:
        return "Backlog"

    @property
    def analytics_label(self) -> str:
        return "Analytics"

    @property
    def log_label(self) -> str:
        return "Log"

    @property
    def settings_label(self) -> str:
        return "Settings"

    @property
    def exit_label(self) -> str:
        return "Exit"

    @property
    def timer_factory(self) -> CountdownTimerFactory:
        return self._timer_factory

    @property
    def backlog_factory(self) -> BacklogFactory:
        return self._backlog_factory

    @property
    def analytics_factory(self) -> AnalyticsFactory:
        return self._analytics_factory

    @property
    def log_factory(self) -> LogFactory:
        return self._log_factory

    @property
    def settings_factory(self) -> SettingsFactory:
        return self._settings_factory

    @property
    def timer_window(self) -> CountdownTimerWindow:
        return self._timer_window

    @timer_window.setter
    def timer_window(self, window: CountdownTimerWindow):
        self._timer_window = window

    @property
    def backlog_window(self) -> BacklogWindow:
        return self._backlog_window

    @backlog_window.setter
    def backlog_window(self, window: BacklogWindow):
        self._backlog_window = window

    @property
    def analytics_window(self) -> AnalyticsWindow:
        return self._analytics_window

    @analytics_window.setter
    def analytics_window(self, window: AnalyticsWindow):
        self._analytics_window = window

    @property
    def log_window(self) -> LogWindow:
        return self._log_window

    @log_window.setter
    def log_window(self, window: LogWindow):
        self._log_window = window

    @property
    def settings_window(self) -> SettingsWindow:
        return self._settings_window

    @settings_window.setter
    def settings_window(self, window: SettingsWindow):
        self._settings_window = window
    
    @property
    def work_action_hidden(self) -> bool:
        return self._work_action_hidden
    
    @work_action_hidden.setter
    def work_action_hidden(self, hidden: bool):
        self._work_action_hidden = hidden
        self.work_action_hidden_changed.emit(hidden)

    @property
    def break_action_hidden(self) -> bool:
        return self._break_action_hidden

    @break_action_hidden.setter
    def break_action_hidden(self, hidden: bool):
        self._break_action_hidden = hidden
        self.break_action_hidden_changed.emit(hidden)

    @property
    def idle_action_enabled(self) -> bool:
        return self._idle_action_enabled

    @idle_action_enabled.setter
    def idle_action_enabled(self, enabled: bool):
        self._idle_action_enabled = enabled
        self.idle_action_enabled_changed.emit(enabled)


class TrayController(QObject):
    """
        Controller of the tray
    """
    def __init__(self, wst: WorkSplitTracker, wst_timer_controller: CountdownTimerController,
                 activity_model: ActivityTableModel, settings_notifier: SettingsNotifier, model: TrayModel):
        super(TrayController, self).__init__()

        self._wst = wst
        self._wst_timer_controller = wst_timer_controller
        self._activity_model = activity_model
        self._settings_notifier = settings_notifier
        self._model = model

        # before state change callbacks
        self._wst.context.push_before_state_change_callback(WSTState.WORK, PriorityCallback(self._after_work, 1))
        self._wst.context.push_before_state_change_callback(WSTState.BREAK, PriorityCallback(self._after_break, 1))

        # after state change callbacks
        self._wst.context.push_after_state_change_callback(WSTState.WORK, PriorityCallback(self._before_work, 3))
        self._wst.context.push_after_state_change_callback(WSTState.BREAK, PriorityCallback(self._before_break, 3))
        self._wst.context.push_after_state_change_callback(WSTState.IDLE, PriorityCallback(self._before_idle, 3))

        # timer tick callbacks
        self._wst_timer_controller.timer_context.push_tick_identifier_callback(
            WSTCountdownTimerIdentifier.WORK,
            PriorityCallback(self._on_timer_tick, 3)
        )
        self._wst_timer_controller.timer_context.push_tick_identifier_callback(
            WSTCountdownTimerIdentifier.BREAK,
            PriorityCallback(self._on_timer_tick, 3)
        )

        self._init_model(self._wst.context)

    @pyqtSlot()
    def on_timer_action_pressed(self):
        self._model.timer_window = self._model.timer_factory.create()
        self._model.timer_window.about_to_close.connect(self._cleanup_closed_timer_window)
        self._model.timer_window.show()

    @pyqtSlot()
    def _cleanup_closed_timer_window(self):
        self._model.timer_window.clean_up()
        self._model.timer_window = None

    @pyqtSlot()
    def on_work_action_pressed(self):
        self._wst.do_work(None)

    @pyqtSlot()
    def on_break_action_pressed(self):
        self._wst.do_break()

    @pyqtSlot()
    def on_idle_action_pressed(self):
        self._wst.do_idle()

    @pyqtSlot()
    def on_backlog_action_pressed(self):
        self._model.backlog_window = self._model.backlog_factory.create()
        self._model.backlog_window.about_to_close.connect(self._cleanup_closed_backlog_window)
        self._model.backlog_window.show()

    @pyqtSlot()
    def _cleanup_closed_backlog_window(self):
        self._model.backlog_window = None

    @pyqtSlot()
    def on_analytics_action_pressed(self):
        self._model.analytics_window = self._model.analytics_factory.create()
        self._model.analytics_window.about_to_close.connect(self._cleanup_closed_analytics_window)
        self._model.analytics_window.show()

    @pyqtSlot()
    def _cleanup_closed_analytics_window(self):
        self._model.analytics_window = None

    @pyqtSlot()
    def on_log_action_pressed(self):
        self._model.log_window = self._model.log_factory.create()
        self._model.log_window.about_to_close.connect(self._cleanup_closed_log_window)
        self._model.log_window.show()

    @pyqtSlot()
    def _cleanup_closed_log_window(self):
        self._model.log_window = None

    @pyqtSlot()
    def on_settings_action_pressed(self):
        self._model.settings_window = self._model.settings_factory.create()
        self._model.settings_window.about_to_close.connect(self._cleanup_closed_settings_window)
        self._model.settings_window.show()

    @pyqtSlot()
    def _cleanup_closed_settings_window(self):
        self._model.settings_window = None

    @pyqtSlot()
    def on_exit_action_pressed(self):
        if self._wst.context.state != WSTState.IDLE:
            self._wst.do_idle()
        self._model.app.exit()

    def _before_work(self, context: WSTContext):
        self._model.work_action_hidden = True
        self._model.break_action_hidden = False
        self._model.idle_action_enabled = True
        self._model.timer_label = f"Work: {utils.convert_seconds_to_time_string(context.work_time * 60)}"
        self._create_work_activity(context)

    def _before_break(self, context: WSTContext):
        self._model.work_action_hidden = False
        self._model.break_action_hidden = True
        self._model.idle_action_enabled = True
        self._model.timer_label = f"Break: {utils.convert_seconds_to_time_string(context.break_time * 60)}"
        self._create_break_activity(context)

    def _before_idle(self, context: WSTContext):
        self._model.work_action_hidden = False
        self._model.break_action_hidden = True
        self._model.idle_action_enabled = False
        self._model.timer_label = "Timer: -"

    def _after_work(self, context: WSTContext):
        self._stop_work_activity(context)

    def _after_break(self, context: WSTContext):
        self._stop_break_activity(context)

    def _on_timer_tick(self, context: CountdownTimerContext):
        prefix_index = self._model.timer_label.find(':')
        self._model.timer_label = \
            self._model.timer_label[:prefix_index + 2] + \
            utils.convert_seconds_to_time_string(context.seconds_left)

    def _create_work_activity(self, context: WSTContext):
        work_activity = WorkActivity(
            date=datetime.now(),
            expected_duration=self._settings_notifier.work_time * 60,
            work_item=context.task
        )
        context.activity = work_activity
        self._activity_model.add_work_activity(work_activity)

    def _stop_work_activity(self, context: WSTContext):
        context.activity.duration = (context.work_time * 60) - context.stop_time
        self._activity_model.update_work_activity(context.activity)
        context.activity = None

    def _create_break_activity(self, context: WSTContext):
        break_activity = BreakActivity(
            date=datetime.now(),
            expected_duration=self._settings_notifier.break_time * 60
        )
        context.activity = break_activity
        self._activity_model.add_break_activity(break_activity)

    def _stop_break_activity(self, context: WSTContext):
        context.activity.duration = (context.break_time * 60) - context.stop_time
        self._activity_model.update_break_activity(context.activity)
        context.activity = None

    def _init_model(self, context: WSTContext):
        if context.state == WSTState.WORK:
            self._before_work(context)
        elif context.state == WSTState.BREAK:
            self._before_break(context)
        elif context.state == WSTState.IDLE:
            self._before_idle(context)


class TrayView(QMenu):
    """
        View of the tray
    """
    def __init__(self, controller: TrayController, model: TrayModel):
        super(TrayView, self).__init__()
        self._controller = controller
        self._model = model

        self._timer_action = self.addAction(self._model.timer_label)
        self.addSeparator()
        self._work_action = self.addAction(self._model.work_label)
        self._break_action = self.addAction(self._model.break_label)
        self._idle_action = self.addAction(self._model.idle_label)
        self.addSeparator()
        self._backlog_action = self.addAction(self._model.backlog_label)
        self._analytics_action = self.addAction(self._model.analytics_label)
        self._log_action = self.addAction(self._model.log_label)
        self._settings_action = self.addAction(self._model.settings_label)
        self.addSeparator()
        self._exit_action = self.addAction(self._model.exit_label)

        self._init_state()
        self._init_bindings()

    def _init_state(self):
        self._work_action.setVisible(not self._model.work_action_hidden)
        self._break_action.setVisible(not self._model.break_action_hidden)
        self._idle_action.setEnabled(self._model.idle_action_enabled)

    def _init_bindings(self):
        self._timer_action.triggered.connect(self._controller.on_timer_action_pressed)
        self._work_action.triggered.connect(self._controller.on_work_action_pressed)
        self._break_action.triggered.connect(self._controller.on_break_action_pressed)
        self._idle_action.triggered.connect(self._controller.on_idle_action_pressed)
        self._backlog_action.triggered.connect(self._controller.on_backlog_action_pressed)
        self._analytics_action.triggered.connect(self._controller.on_analytics_action_pressed)
        self._log_action.triggered.connect(self._controller.on_log_action_pressed)
        self._settings_action.triggered.connect(self._controller.on_settings_action_pressed)
        self._exit_action.triggered.connect(self._controller.on_exit_action_pressed)

        self._model.timer_label_changed.connect(self._on_timer_label_changed)
        self._model.work_action_hidden_changed.connect(self._on_work_action_hidden_changed)
        self._model.break_action_hidden_changed.connect(self._on_break_action_hidden_changed)
        self._model.idle_action_enabled_changed.connect(self._on_idle_action_enabled_changed)

    @pyqtSlot(str)
    def _on_timer_label_changed(self, label: str):
        self._timer_action.setText(label)

    @pyqtSlot(bool)
    def _on_work_action_hidden_changed(self, hidden: bool):
        self._work_action.setVisible(not hidden)

    @pyqtSlot(bool)
    def _on_break_action_hidden_changed(self, hidden: bool):
        self._break_action.setVisible(not hidden)

    @pyqtSlot(bool)
    def _on_idle_action_enabled_changed(self, enabled: bool):
        self._idle_action.setEnabled(enabled)


class Tray(QSystemTrayIcon):
    """
        Tray used to interact with application and open other windows
    """
    def __init__(
            self,
            app: QApplication,
            wst: WorkSplitTracker,
            wst_timer_controller: CountdownTimerController,
            activity_model: ActivityTableModel,
            settings_notifier: SettingsNotifier,
            timer_factory: CountdownTimerFactory,
            backlog_factory: BacklogFactory,
            analytics_factory: AnalyticsFactory,
            log_factory: LogFactory,
            settings_factory: SettingsFactory
    ):
        super(Tray, self).__init__(QIcon(utils.resource_provider.image("tray_icon.png")), app)

        self._model = TrayModel(
            app=app,
            timer_factory=timer_factory,
            backlog_factory=backlog_factory,
            analytics_factory=analytics_factory,
            log_factory=log_factory,
            settings_factory=settings_factory
        )
        self._controller = TrayController(wst, wst_timer_controller, activity_model, settings_notifier, self._model)
        self._view = TrayView(self._controller, self._model)
        self.setContextMenu(self._view)
