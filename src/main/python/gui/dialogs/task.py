from abc import ABC, abstractmethod

from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QLabel, QLineEdit, QPushButton, QSpinBox, \
    QVBoxLayout, QWidget

from application.models import Task


class CreateEditTaskModel(QObject):
    """
        Model of the edit or create task dialog
    """
    name_changed = pyqtSignal(str)
    priority_changed = pyqtSignal(int)
    total_workload_changed = pyqtSignal(int)

    def __init__(self, task: Task):
        super().__init__()
        self._task = task

    @property
    def task(self) -> Task:
        return self._task

    @property
    def name_label(self) -> str:
        return "Name"

    @property
    def priority_label(self) -> str:
        return "Priority"

    @property
    def completed_workload_label(self) -> str:
        return "Completed Workload"

    @property
    def total_workload_label(self) -> str:
        return "Total Workload"

    @property
    def name(self) -> str:
        return self._task.name

    @name.setter
    def name(self, name: str):
        self._task.name = name
        self.name_changed.emit(name)

    @property
    def priority(self) -> int:
        return self._task.priority

    @priority.setter
    def priority(self, priority: int):
        self._task.priority = priority
        self.priority_changed.emit(priority)

    @property
    def completed_workload(self) -> int:
        return self._task.completed_workload

    @property
    def total_workload(self) -> int:
        return self._task.total_workload

    @total_workload.setter
    def total_workload(self, total_workload: int):
        self._task.total_workload = total_workload
        self.total_workload_changed.emit(total_workload)

    @property
    def completed_workload_enabled(self):
        return False


class CreateEditTaskController(QObject):
    """
       Controller of the edit or create task dialog
    """
    def __init__(self, model: CreateEditTaskModel):
        super(CreateEditTaskController, self).__init__()
        self._model = model

    @pyqtSlot(str)
    def on_name_change(self, name: str):
        self._model.name = name

    @pyqtSlot(int)
    def on_priority_change(self, priority: int):
        self._model.priority = priority

    @pyqtSlot(int)
    def on_total_workload_change(self, total_workload: int):
        self._model.total_workload = total_workload


class CreateEditTaskView(QWidget):
    """
       View of the edit or create task dialog
    """
    def __init__(self, controller: CreateEditTaskController, model: CreateEditTaskModel):
        super(CreateEditTaskView, self).__init__()

        self._controller = controller
        self._model = model

        self._name_label = QLabel(text=self._model.name_label, parent=self)
        self._name_field = QLineEdit(self._model.name, parent=self)

        self._priority_label = QLabel(text=self._model.priority_label, parent=self)
        self._priority_field = QSpinBox(self)

        self._completed_workload_label = QLabel(text=self._model.completed_workload_label, parent=self)
        self._completed_workload_field = QSpinBox(self)

        self._total_workload_label = QLabel(text=self._model.total_workload_label, parent=self)
        self._total_workload_field = QSpinBox(self)

        self._init_state()
        self._init_bindings()
        self._init_layout()

    def _init_state(self):
        self._priority_field.setRange(1, 5)
        self._priority_field.setValue(self._model.priority)

        self._completed_workload_field.setEnabled(self._model.completed_workload_enabled)
        self._completed_workload_field.setValue(self._model.completed_workload)

        self._total_workload_field.setMinimum(1)
        self._total_workload_field.setValue(self._model.total_workload)

    def _init_bindings(self):
        self._name_field.textChanged.connect(self._controller.on_name_change)
        self._priority_field.valueChanged.connect(self._controller.on_priority_change)
        self._total_workload_field.valueChanged.connect(self._controller.on_total_workload_change)

        self._model.name_changed.connect(self._on_name_changed)
        self._model.priority_changed.connect(self._on_priority_changed)
        self._model.total_workload_changed.connect(self._on_total_workload_changed)

    def _init_layout(self):
        layout = QFormLayout(self)

        layout.addRow(self._name_label, self._name_field)
        layout.addRow(self._priority_label, self._priority_field)
        layout.addRow(self._completed_workload_label, self._completed_workload_field)
        layout.addRow(self._total_workload_label, self._total_workload_field)

    @pyqtSlot(str)
    def _on_name_changed(self, name: str):
        self._name_field.setText(name)

    @pyqtSlot(int)
    def _on_priority_changed(self, priority: int):
        self._priority_field.setValue(priority)

    @pyqtSlot(int)
    def _on_completed_workload_changed(self, completed_workload: int):
        self._completed_workload_field.setValue(completed_workload)

    @pyqtSlot(int)
    def _on_total_workload_changed(self, total_workload: int):
        self._total_workload_field.setValue(total_workload)


class CreateEditTaskDialog(QDialog):
    """
        Dialog used to create or edit tasks.
    """
    def __init__(self, title: str, confirm_label: str, task: Task):
        super(CreateEditTaskDialog, self).__init__()

        self.setWindowTitle(title)

        self._model = CreateEditTaskModel(task)
        self._controller = CreateEditTaskController(self._model)
        self._view = CreateEditTaskView(self._controller, self._model)

        self._reject_button = QPushButton(text="Cancel", parent=self)
        self._confirm_button = QPushButton(text=confirm_label, parent=self)

        self._button_box = QDialogButtonBox()
        self._button_box.addButton(self._reject_button, QDialogButtonBox.ButtonRole.RejectRole)
        self._button_box.addButton(self._confirm_button, QDialogButtonBox.ButtonRole.AcceptRole)
        self._button_box.accepted.connect(self.accept)
        self._button_box.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self._view)
        layout.addWidget(self._button_box)

    @property
    def task(self):
        return self._model.task


class TaskCompletedDialog(QDialog):
    """
        Simple dialog used to ask the user if a task is completed.
    """
    def __init__(self, name: str):
        super(TaskCompletedDialog, self).__init__()

        self.setWindowTitle("Task Completed")

        self._reject_button = QPushButton(text="No", parent=self)
        self._confirm_button = QPushButton(text="Yes", parent=self)

        self._button_box = QDialogButtonBox()
        self._button_box.setCenterButtons(True)
        self._button_box.addButton(self._reject_button, QDialogButtonBox.ButtonRole.RejectRole)
        self._button_box.addButton(self._confirm_button, QDialogButtonBox.ButtonRole.AcceptRole)
        self._button_box.accepted.connect(self.accept)
        self._button_box.rejected.connect(self.reject)

        layout = QVBoxLayout(self)

        self._message_box = QLabel(f"Did you complete the task {name}?")

        layout.addWidget(self._message_box)
        layout.addWidget(self._button_box)


class CreateEditTaskDialogFactory(ABC):
    @abstractmethod
    def create_dialog(self) -> CreateEditTaskDialog:
        raise NotImplementedError

    @abstractmethod
    def edit_dialog(self, task: Task) -> CreateEditTaskDialog:
        raise NotImplementedError


class CreateEditTaskDialogFactoryImpl(CreateEditTaskDialogFactory):
    def create_dialog(self) -> CreateEditTaskDialog:
        return CreateEditTaskDialog(
            title="Create Task",
            confirm_label="Create",
            task=Task(name="", priority=1, completed_workload=0, total_workload=1)
        )

    def edit_dialog(self, task: Task) -> CreateEditTaskDialog:
        return CreateEditTaskDialog(
            title="Edit Task",
            confirm_label="Save",
            task=task
        )


class TaskCompletedDialogFactory(ABC):
    @abstractmethod
    def create(self, name: str):
        raise NotImplementedError


class TaskCompletedDialogFactoryImpl(TaskCompletedDialogFactory):
    def create(self, name: str):
        return TaskCompletedDialog(name)
