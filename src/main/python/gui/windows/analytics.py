from abc import abstractmethod, ABC

from PyQt5.QtCore import pyqtSignal, pyqtSlot, QModelIndex, QObject, Qt
from PyQt5.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QSpinBox, QVBoxLayout, QWidget

from application.models import BreakActivity, WorkActivity
from gui.activity import ActivityTableModel
from gui.task import TaskListModel
from gui.windows.mainwindow import AbstractWindow


class AnalyticsModel(QObject):
    """
        Model of the Analytics Window
    """
    work_time_diff_changed = pyqtSignal(int)
    break_time_diff_changed = pyqtSignal(int)
    work_activity_count_changed = pyqtSignal(int)
    break_activity_count_changed = pyqtSignal(int)
    completed_tasks_count_changed = pyqtSignal(int)
    left_tasks_count_changed = pyqtSignal(int)

    def __init__(self):
        super().__init__()

        self._work_time_diff = None
        self._break_time_diff = None
        self._work_activity_count = None
        self._break_activity_count = None
        self._completed_tasks_count = None
        self._left_tasks_count = None

    @property
    def work_time_diff_label(self) -> str:
        return "Work Time Diff"

    @property
    def break_time_diff_label(self) -> str:
        return "Break Time Diff"

    @property
    def work_activity_count_label(self) -> str:
        return "Work Activity Count"

    @property
    def break_activity_count_label(self) -> str:
        return "Break Activity Count"

    @property
    def completed_task_count_label(self) -> str:
        return "Total Tasks completed"

    @property
    def left_task_count_label(self) -> str:
        return "Total Tasks left"

    @property
    def work_time_diff(self) -> int:
        return self._work_time_diff

    @work_time_diff.setter
    def work_time_diff(self, diff: int):
        self._work_time_diff = diff
        self.work_time_diff_changed.emit(diff)

    @property
    def break_time_diff(self) -> int:
        return self._break_time_diff

    @break_time_diff.setter
    def break_time_diff(self, diff: int):
        self._break_time_diff = diff
        self.break_time_diff_changed.emit(diff)

    @property
    def work_activity_count(self) -> int:
        return self._work_activity_count

    @work_activity_count.setter
    def work_activity_count(self, count: int):
        self._work_activity_count = count
        self.work_activity_count_changed.emit(count)

    @property
    def break_activity_count(self) -> int:
        return self._break_activity_count

    @break_activity_count.setter
    def break_activity_count(self, count: int):
        self._break_activity_count = count
        self.break_activity_count_changed.emit(count)

    @property
    def completed_tasks_count(self) -> int:
        return self._completed_tasks_count

    @completed_tasks_count.setter
    def completed_tasks_count(self, count: int):
        self._completed_tasks_count = count
        self.completed_tasks_count_changed.emit(count)

    @property
    def left_tasks_count(self) -> int:
        return self._left_tasks_count

    @left_tasks_count.setter
    def left_tasks_count(self, count: int):
        self._left_tasks_count = count
        self.left_tasks_count_changed.emit(count)


class AnalyticsController(QObject):
    """
        Controller of the Analytics Window
    """
    def __init__(self, task_model: TaskListModel, activity_model: ActivityTableModel, model: AnalyticsModel):
        super().__init__()

        self._model = model
        self._task_model = task_model
        self._activity_model = activity_model

        self._task_model.dataChanged.connect(self._on_task_data_changed)
        self._task_model.rowsInserted.connect(self._on_task_data_inserted)
        self._task_model.rowsRemoved.connect(self._on_task_data_removed)
        self._activity_model.dataChanged.connect(self._on_activity_data_changed)
        self._activity_model.rowsInserted.connect(self._on_activity_data_inserted)

        self._init_model()

    def _on_activity_model_change(self):
        work_activity_count = self._calc_work_activity_count()
        break_activity_count = self._activity_model.rowCount() - work_activity_count

        self._model.work_activity_count = work_activity_count
        self._model.break_activity_count = break_activity_count
        self._model.work_time_diff = self._calc_time_diff(WorkActivity)
        self._model.break_time_diff = self._calc_time_diff(BreakActivity)

    def _on_task_model_change(self):
        completed_tasks_count = self._calc_task_completed_count()
        left_tasks_count = self._task_model.rowCount() - 1 - completed_tasks_count
        self._model.completed_tasks_count = completed_tasks_count
        self._model.left_tasks_count = left_tasks_count

    def _calc_time_diff(self, activity_type) -> int:
        diff = 0

        for index in range(self._activity_model.rowCount()):
            activity = self._activity_model.index(index, 0).data(Qt.ItemDataRole.UserRole)
            if isinstance(activity, activity_type) and activity.duration:
                diff = diff + activity.duration - activity.expected_duration

        return diff

    def _calc_work_activity_count(self) -> int:
        count = 0

        for index in range(self._activity_model.rowCount()):
            activity = self._activity_model.index(index, 0).data(Qt.ItemDataRole.UserRole)
            if isinstance(activity, WorkActivity):
                count = count + 1

        return count

    def _calc_task_completed_count(self) -> int:
        completed_sum = 0

        for index in range(self._task_model.rowCount()):
            task = self._task_model.index(index, 0).data(Qt.ItemDataRole.UserRole)
            if task.completed:
                completed_sum = completed_sum + 1

        return completed_sum

    @pyqtSlot(QModelIndex, QModelIndex)
    def _on_activity_data_changed(self, left: QModelIndex, right: QModelIndex):
        self._on_activity_model_change()

    @pyqtSlot(QModelIndex, int, int)
    def _on_activity_data_inserted(self, parent: QModelIndex, first: int, last: int):
        self._on_activity_model_change()

    @pyqtSlot(QModelIndex, QModelIndex)
    def _on_task_data_changed(self, left: QModelIndex, right: QModelIndex):
        self._on_task_model_change()

    @pyqtSlot(QModelIndex, int, int)
    def _on_task_data_inserted(self, parent: QModelIndex, first: int, last: int):
        self._on_task_model_change()

    @pyqtSlot(QModelIndex, int, int)
    def _on_task_data_removed(self, parent: QModelIndex, first: int, last: int):
        self._on_task_model_change()

    def _init_model(self):
        self._on_activity_model_change()
        self._on_task_model_change()


class AnalyticsView(QWidget):
    """
        Controller of the Analytics Window
    """
    def __init__(self, controller: AnalyticsController, model: AnalyticsModel):
        super().__init__()

        self._controller = controller
        self._model = model

        self._work_time_diff_label = QLabel(text=self._model.work_time_diff_label, parent=self)
        self._work_time_diff_field = QSpinBox(self)

        self._break_time_diff_label = QLabel(text=self._model.break_time_diff_label, parent=self)
        self._break_time_diff_field = QSpinBox(self)

        self._work_activity_count_label = QLabel(text=self._model.work_activity_count_label, parent=self)
        self._work_activity_count_field = QSpinBox(self)

        self._break_activity_count_label = QLabel(text=self._model.break_activity_count_label, parent=self)
        self._break_activity_count_field = QSpinBox(self)

        self._tasks_completed_count_label = QLabel(text=self._model.completed_task_count_label, parent=self)
        self._tasks_completed_count_field = QSpinBox(self)

        self._tasks_left_count_label = QLabel(text=self._model.left_task_count_label, parent=self)
        self._tasks_left_count_field = QSpinBox(self)

        self._init_state()
        self._init_bindings()
        self._init_layout()

    def _init_bindings(self):
        self._model.work_time_diff_changed.connect(self._on_work_time_diff_changed)
        self._model.break_time_diff_changed.connect(self._on_break_time_diff_changed)
        self._model.work_activity_count_changed.connect(self._on_work_activity_count_changed)
        self._model.break_activity_count_changed.connect(self._on_break_activity_count_changed)
        self._model.completed_tasks_count_changed.connect(self._on_tasks_completed_count_changed)
        self._model.left_tasks_count_changed.connect(self._on_tasks_left_count_changed)

    def _init_layout(self):
        layout = QGridLayout(self)

        work_time_diff_layout = QHBoxLayout()
        work_time_diff_layout.addWidget(self._work_time_diff_label)
        work_time_diff_layout.addWidget(self._work_time_diff_field)

        break_time_diff_layout = QHBoxLayout()
        break_time_diff_layout.addWidget(self._break_time_diff_label)
        break_time_diff_layout.addWidget(self._break_time_diff_field)

        work_activity_count_layout = QHBoxLayout()
        work_activity_count_layout.addWidget(self._work_activity_count_label)
        work_activity_count_layout.addWidget(self._work_activity_count_field)

        break_activity_count_layout = QHBoxLayout()
        break_activity_count_layout.addWidget(self._break_activity_count_label)
        break_activity_count_layout.addWidget(self._break_activity_count_field)

        tasks_completed_count_layout = QHBoxLayout()
        tasks_completed_count_layout.addWidget(self._tasks_completed_count_label)
        tasks_completed_count_layout.addWidget(self._tasks_completed_count_field)

        tasks_left_count_layout = QHBoxLayout()
        tasks_left_count_layout.addWidget(self._tasks_left_count_label)
        tasks_left_count_layout.addWidget(self._tasks_left_count_field)

        layout.addLayout(work_time_diff_layout, 0, 0)
        layout.addLayout(break_time_diff_layout, 0, 1)
        layout.addLayout(work_activity_count_layout, 1, 0)
        layout.addLayout(break_activity_count_layout, 1, 1)
        layout.addLayout(tasks_completed_count_layout, 2, 0)
        layout.addLayout(tasks_left_count_layout, 2, 1)

    def _init_state(self):
        self._work_time_diff_field.setEnabled(False)
        self._work_time_diff_field.setMinimum(-1000000)
        self._work_time_diff_field.setValue(self._model.work_time_diff)

        self._break_time_diff_field.setEnabled(False)
        self._break_time_diff_field.setMinimum(-1000000)
        self._break_time_diff_field.setValue(self._model.break_time_diff)

        self._work_activity_count_field.setEnabled(False)
        self._work_activity_count_field.setValue(self._model.work_activity_count)

        self._break_activity_count_field.setEnabled(False)
        self._break_activity_count_field.setValue(self._model.break_activity_count)

        self._tasks_completed_count_field.setEnabled(False)
        self._tasks_completed_count_field.setValue(self._model.completed_tasks_count)

        self._tasks_left_count_field.setEnabled(False)
        self._tasks_left_count_field.setValue(self._model.left_tasks_count)

    @pyqtSlot(int)
    def _on_work_time_diff_changed(self, diff: int):
        self._work_time_diff_field.setValue(diff)

    @pyqtSlot(int)
    def _on_break_time_diff_changed(self, diff: int):
        self._break_time_diff_field.setValue(diff)

    @pyqtSlot(int)
    def _on_work_activity_count_changed(self, count: int):
        self._work_activity_count_field.setValue(count)

    @pyqtSlot(int)
    def _on_break_activity_count_changed(self, count: int):
        self._break_activity_count_field.setValue(count)

    @pyqtSlot(int)
    def _on_tasks_completed_count_changed(self, count: int):
        self._tasks_completed_count_field.setValue(count)

    @pyqtSlot(int)
    def _on_tasks_left_count_changed(self, count: int):
        self._tasks_left_count_field.setValue(count)


class AnalyticsWindow(AbstractWindow):
    """
        Window providing analysis information about recent work/break activities and tasks
        The window implements the MVC pattern.
    """
    def __init__(self, task_model: TaskListModel, activity_model: ActivityTableModel):
        super().__init__()

        self._model = AnalyticsModel()
        self._controller = AnalyticsController(task_model, activity_model, self._model)
        self._view = AnalyticsView(controller=self._controller, model=self._model)

        layout = QVBoxLayout(self)
        layout.addWidget(self._view)
        self.setLayout(layout)

        self._center()


class AnalyticsFactory(ABC):
    @abstractmethod
    def create(self) -> AnalyticsWindow:
        raise NotImplementedError


class AnalyticsFactoryImpl(AnalyticsFactory):
    def __init__(self, task_model: TaskListModel, activity_model: ActivityTableModel):
        self._task_model = task_model
        self._activity_model = activity_model

    def create(self) -> AnalyticsWindow:
        return AnalyticsWindow(self._task_model, self._activity_model)
