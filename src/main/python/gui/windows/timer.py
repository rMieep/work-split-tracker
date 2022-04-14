from abc import ABC, abstractmethod

from PyQt5.QtCore import pyqtSignal, pyqtSlot, QModelIndex, QObject, QSortFilterProxyModel, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QComboBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

import utils
from application.app import WorkSplitTracker, WSTContext, WSTState
from application.models import Task
from application.timer import CountdownTimerContext, PriorityCallback, WSTCountdownTimerIdentifier
from application.timer import CountdownTimerController as WSTCountdownTimerController
from gui.dialogs.task import TaskCompletedDialogFactory
from gui.task import TaskListModel
from gui.windows.mainwindow import AbstractWindow


class CountdownTimerTaskProxyModel(QSortFilterProxyModel):
    """
       Proxy Model used to display, sort and select the tasks provided by the TaskListModel
   """
    def __init__(self):
        super().__init__()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        data = self.sourceModel().index(source_row, 0, source_parent).data(Qt.ItemDataRole.UserRole)
        return not data.completed


class CountdownTimerModel(QObject):
    """
        Model of the timer window
    """
    work_button_hidden_changed = pyqtSignal(bool)
    break_button_hidden_changed = pyqtSignal(bool)
    idle_button_enabled_changed = pyqtSignal(bool)
    label_changed = pyqtSignal(str)
    time_changed = pyqtSignal(str)
    time_color_changed = pyqtSignal(str)
    selected_index_changed = pyqtSignal(int)
    task_select_enabled_changed = pyqtSignal(bool)

    def __init__(self, task_model: TaskListModel, task_completed_dialog_factory: TaskCompletedDialogFactory):
        super().__init__()

        self._task_model = task_model
        self._task_completed_dialog_factory = task_completed_dialog_factory

        self._work_icon = QIcon(utils.resource_provider.image("211876_play_icon.png"))
        self._break_icon = QIcon(utils.resource_provider.image("211871_pause_icon.png"))
        self._idle_icon = QIcon(utils.resource_provider.image("211931_stop_icon.png"))

        self._work_button_hidden = False
        self._break_button_hidden = True
        self._idle_button_enabled = False
        self._label = "Timer"
        self._time = "-"
        self._time_color = "black"
        self._selected_index = 0
        self._task_select_enabled = True

        self._proxy_task_model = CountdownTimerTaskProxyModel()
        self._proxy_task_model.setSourceModel(self._task_model)
        self._proxy_task_model.setSortRole(self._task_model.SORT_PRIORITY_ROLE)
        self._proxy_task_model.setDynamicSortFilter(True)
        self._proxy_task_model.sort(0, Qt.SortOrder.DescendingOrder)

    @property
    def work_icon(self) -> QIcon:
        return self._work_icon

    @property
    def work_button_hidden(self) -> bool:
        return self._work_button_hidden

    @work_button_hidden.setter
    def work_button_hidden(self, hidden: bool):
        self._work_button_hidden = hidden
        self.work_button_hidden_changed.emit(hidden)

    @property
    def break_icon(self) -> QIcon:
        return self._break_icon

    @property
    def break_button_hidden(self) -> bool:
        return self._break_button_hidden

    @break_button_hidden.setter
    def break_button_hidden(self, hidden: bool):
        self._break_button_hidden = hidden
        self.break_button_hidden_changed.emit(hidden)

    @property
    def idle_icon(self) -> QIcon:
        return self._idle_icon

    @property
    def idle_button_enabled(self) -> bool:
        return self._idle_button_enabled

    @idle_button_enabled.setter
    def idle_button_enabled(self, enabled: bool):
        self._idle_button_enabled = enabled
        self.idle_button_enabled_changed.emit(enabled)

    @property
    def label(self) -> str:
        return self._label

    @label.setter
    def label(self, label):
        self._label = label
        self.label_changed.emit(label)

    @property
    def time(self) -> str:
        return self._time

    @time.setter
    def time(self, time: str):
        self._time = time
        self.time_changed.emit(time)

    @property
    def time_color(self) -> str:
        return self._time_color

    @time_color.setter
    def time_color(self, color: str):
        self._time_color = color
        self.time_color_changed.emit(color)

    @property
    def selected_index(self) -> int:
        return self._selected_index

    @selected_index.setter
    def selected_index(self, index: int):
        self._selected_index = index
        self.selected_index_changed.emit(index)

    @property
    def task_select_enabled(self) -> bool:
        return self._task_select_enabled

    @task_select_enabled.setter
    def task_select_enabled(self, enabled: bool):
        self._task_select_enabled = enabled
        self.task_select_enabled_changed.emit(enabled)

    @property
    def proxy_model(self) -> QSortFilterProxyModel:
        return self._proxy_task_model

    @property
    def task_model(self) -> TaskListModel:
        return self._task_model

    def open_task_completed_dialog(self, index: QModelIndex, task: Task):
        dialog = self._task_completed_dialog_factory.create(task.name)
        if dialog.exec():
            task.completed = True
            self._task_model.setData(index, task)


class CountdownTimerController(QObject):
    """
        Controller of the timer window
    """
    def __init__(self, wst: WorkSplitTracker, wst_timer_controller: WSTCountdownTimerController,
                 model: CountdownTimerModel):
        super(CountdownTimerController, self).__init__()
        self._wst = wst
        self._wst_timer_controller = wst_timer_controller
        self._model = model

        # before state change callbacks
        self._wst.context.push_before_state_change_callback(WSTState.WORK, PriorityCallback(self._after_work, 3))

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

        # timer alarm callbacks
        self._wst_timer_controller.timer_context.push_alarm_identifier_callback(
            WSTCountdownTimerIdentifier.WORK,
            PriorityCallback(self._on_timer_alarm, 3)
        )
        self._wst_timer_controller.timer_context.push_alarm_identifier_callback(
            WSTCountdownTimerIdentifier.BREAK,
            PriorityCallback(self._on_timer_alarm, 3)
        )

        self._init_model(self._wst.context)

    def remove_callbacks(self):
        self._wst.context.remove_before_state_change_callback(WSTState.WORK, PriorityCallback(self._after_work, 3))
        self._wst.context.remove_after_state_change_callback(WSTState.WORK, PriorityCallback(self._before_work, 3))
        self._wst.context.remove_after_state_change_callback(WSTState.BREAK, PriorityCallback(self._before_break, 3))
        self._wst.context.remove_after_state_change_callback(WSTState.IDLE, PriorityCallback(self._before_idle, 3))
        self._wst_timer_controller.timer_context.remove_tick_identifier_callback(
            WSTCountdownTimerIdentifier.WORK,
            PriorityCallback(self._on_timer_tick, 3)
        )
        self._wst_timer_controller.timer_context.remove_tick_identifier_callback(
            WSTCountdownTimerIdentifier.BREAK,
            PriorityCallback(self._on_timer_tick, 3)
        )
        self._wst_timer_controller.timer_context.remove_alarm_identifier_callback(
            WSTCountdownTimerIdentifier.WORK,
            PriorityCallback(self._on_timer_alarm, 3)
        )
        self._wst_timer_controller.timer_context.remove_alarm_identifier_callback(
            WSTCountdownTimerIdentifier.BREAK,
            PriorityCallback(self._on_timer_alarm, 3)
        )

    @pyqtSlot()
    def on_work_button_pressed(self):
        if self._model.selected_index == 0:
            self._wst.do_work(None)
        else:
            self._wst.do_work(self._model.proxy_model.index(
                self._model.selected_index, 0).data(Qt.ItemDataRole.UserRole))

    @pyqtSlot()
    def on_break_button_pressed(self):
        self._wst.do_break()

    @pyqtSlot()
    def on_idle_button_pressed(self):
        self._wst.do_idle()

    @pyqtSlot(int)
    def on_selection_changed(self, index: int):
        self._model.selected_index = index

    def _before_work(self, context: WSTContext):
        self._model.work_button_hidden = True
        self._model.break_button_hidden = False
        self._model.idle_button_enabled = True
        self._model.label = "Work"
        self._model.time = utils.convert_seconds_to_time_string(context.work_time * 60)
        self._model.time_color = "green"
        self._model.task_select_enabled = False

    def _after_work(self, context: WSTContext):
        index = self._model.proxy_model.mapToSource(self._model.proxy_model.index(self._model.selected_index, 0))
        task = context.task
        if task:
            self._increment_task_workload(index=index, task=task)
            self._model.open_task_completed_dialog(index=index, task=task)
        self._model.selected_index = 0
        self._model.task_select_enabled = True

    def _before_break(self, context: WSTContext):
        self._model.work_button_hidden = False
        self._model.break_button_hidden = True
        self._model.idle_button_enabled = True
        self._model.label = "Break"
        self._model.time = utils.convert_seconds_to_time_string(context.break_time * 60)
        self._model.time_color = "green"

    def _before_idle(self, context: WSTContext):
        self._model.idle_button_enabled = False
        self._model.work_button_hidden = False
        self._model.break_button_hidden = True
        self._model.label = "Timer"
        self._model.time = "-"
        self._model.time_color = "black"

    def _on_timer_tick(self, context: CountdownTimerContext):
        self._model.time = utils.convert_seconds_to_time_string(context.seconds_left)

    def _on_timer_alarm(self, context: CountdownTimerContext):
        self._model.time_color = "red"

    def _init_model(self, context: WSTContext):
        if context.state == WSTState.WORK:
            self._before_work(context)
        elif context.state == WSTState.BREAK:
            self._before_break(context)
        elif context.state == WSTState.IDLE:
            self._before_idle(context)

    def _increment_task_workload(self, index: QModelIndex, task: Task):
        task.completed_workload = task.completed_workload + 1
        self._model.task_model.setData(index, task)


class CountdownTimerView(QWidget):
    """
        View of the timer window
    """
    def __init__(self, controller: CountdownTimerController, model: CountdownTimerModel):
        super(CountdownTimerView, self).__init__()
        self._model = model
        self._controller = controller

        self._label = QLabel(text=self._model.label, parent=self)
        self._time = QLabel(text=self._model.time, parent=self)
        self._work_button = QPushButton(icon=self._model.work_icon, parent=self)
        self._break_button = QPushButton(icon=self._model.break_icon, parent=self)
        self._idle_button = QPushButton(icon=self._model.idle_icon, parent=self)
        self._work_select = QComboBox(parent=self)

        self._init_state()
        self._init_bindings()
        self._init_layout()

    def _init_state(self):
        self._work_button.setHidden(self._model.work_button_hidden)
        self._break_button.setHidden(self._model.break_button_hidden)
        self._idle_button.setEnabled(self._model.idle_button_enabled)
        self._work_select.setModel(self._model.proxy_model)
        self._time.setStyleSheet(f"color: {self._model.time_color}")

        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._time.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def _init_bindings(self):
        self._model.work_button_hidden_changed.connect(self._on_work_button_hidden_changed)
        self._model.break_button_hidden_changed.connect(self._on_break_button_hidden_changed)
        self._model.idle_button_enabled_changed.connect(self._on_idle_button_enabled_changed)
        self._model.label_changed.connect(self._on_label_changed)
        self._model.time_changed.connect(self._on_time_changed)
        self._model.time_color_changed.connect(self._on_time_color_changed)
        self._model.selected_index_changed.connect(self._on_selected_index_changed)

        self._work_button.pressed.connect(self._controller.on_work_button_pressed)
        self._break_button.pressed.connect(self._controller.on_break_button_pressed)
        self._idle_button.pressed.connect(self._controller.on_idle_button_pressed)
        self._work_select.currentIndexChanged.connect(self._controller.on_selection_changed)

    def _init_layout(self):
        main_layout = QVBoxLayout(self)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self._work_button)
        button_layout.addWidget(self._break_button)
        button_layout.addWidget(self._idle_button)

        main_layout.addWidget(self._label)
        main_layout.addWidget(self._time)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self._work_select)

    @pyqtSlot(bool)
    def _on_work_button_hidden_changed(self, hidden: bool):
        self._work_button.setHidden(hidden)

    @pyqtSlot(bool)
    def _on_break_button_hidden_changed(self, hidden: bool):
        self._break_button.setHidden(hidden)

    @pyqtSlot(bool)
    def _on_idle_button_enabled_changed(self, enabled: bool):
        self._idle_button.setEnabled(enabled)

    @pyqtSlot(str)
    def _on_label_changed(self, label: str):
        self._label.setText(label)

    @pyqtSlot(str)
    def _on_time_changed(self, time: str):
        self._time.setText(time)

    @pyqtSlot(str)
    def _on_time_color_changed(self, color: str):
        self._time.setStyleSheet(f"color: {color}")

    @pyqtSlot(int)
    def _on_selected_index_changed(self, index: int):
        self._work_select.setCurrentIndex(index)


class CountdownTimerWindow(AbstractWindow):
    """
        Window allowing the user to start and stop the timer.
        The window implements the MVC pattern.
    """
    def __init__(self, wst: WorkSplitTracker, wst_timer_controller: CountdownTimerController,
                 task_model: TaskListModel, task_completed_dialog_factory: TaskCompletedDialogFactory):
        super(CountdownTimerWindow, self).__init__()

        self._model = CountdownTimerModel(task_model, task_completed_dialog_factory)
        self._controller = CountdownTimerController(wst=wst, wst_timer_controller=wst_timer_controller,
                                                    model=self._model)
        self._view = CountdownTimerView(controller=self._controller, model=self._model)

        layout = QVBoxLayout(self)
        layout.addWidget(self._view)
        self.setLayout(layout)

        self.resize(250, 100)
        self._center()

    def clean_up(self):
        self._controller.remove_callbacks()


class CountdownTimerFactory(ABC):
    @abstractmethod
    def create(self) -> CountdownTimerWindow:
        raise NotImplementedError


class CountdownTimerFactoryImpl(CountdownTimerFactory):
    def __init__(self, wst: WorkSplitTracker, wst_timer_controller: CountdownTimerController,
                 task_model: TaskListModel, task_completed_dialog_factory: TaskCompletedDialogFactory):
        self._wst = wst
        self._wst_timer_controller = wst_timer_controller
        self._task_model = task_model
        self._task_completed_dialog_factory = task_completed_dialog_factory

    def create(self) -> CountdownTimerWindow:
        return CountdownTimerWindow(self._wst, self._wst_timer_controller, self._task_model,
                                    self._task_completed_dialog_factory)
