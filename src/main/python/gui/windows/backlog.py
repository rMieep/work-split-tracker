from abc import ABC, abstractmethod

from PyQt5.QtCore import pyqtSlot, pyqtSignal, QItemSelection, QItemSelectionModel, QModelIndex, QObject, \
    QSortFilterProxyModel, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QHBoxLayout, QListView, QPushButton, QVBoxLayout, QWidget

import utils
from application.models import Task
from gui.dialogs.confirm import ConfirmDialogFactory
from gui.dialogs.task import CreateEditTaskDialogFactory
from gui.task import TaskListModel
from gui.windows.mainwindow import AbstractWindow


class BacklogProxyModel(QSortFilterProxyModel):
    """
        Proxy Model used to display, sort and select the tasks provided by the TaskListModel
    """
    def __init__(self, default_task: Task):
        super().__init__()
        self._default = default_task
        self.setFilterRole(Qt.ItemDataRole.UserRole)

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        data = self.sourceModel().index(source_row, 0, source_parent).data(Qt.ItemDataRole.UserRole)
        return data != self._default and not data.completed


class BacklogModel(QObject):
    """
        Model of the backlog window
    """
    remove_enabled_changed = pyqtSignal(bool)
    mark_enabled_changed = pyqtSignal(bool)

    def __init__(self, create_edit_task_dialog_factory: CreateEditTaskDialogFactory,
                 confirm_dialog_factory: ConfirmDialogFactory, task_model: TaskListModel):

        super(BacklogModel, self).__init__()

        self._create_edit_dialog_factory = create_edit_task_dialog_factory
        self._confirm_dialog_factory = confirm_dialog_factory
        self._task_model = task_model

        self._add_icon = QIcon(utils.resource_provider.image("211878_plus_icon.png"))
        self._remove_icon = QIcon(utils.resource_provider.image("211864_minus_icon.png"))
        self._mark_icon = QIcon(utils.resource_provider.image("211643_checkmark_round_icon.png"))

        self._proxy_task_model = BacklogProxyModel(task_model.DEFAULT)
        self._proxy_task_model.setSortRole(self._task_model.SORT_NAME_ROLE)
        self._proxy_task_model.setSourceModel(self._task_model)
        self._proxy_task_model.setDynamicSortFilter(True)
        self._proxy_task_model.setSortCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._proxy_task_model.sort(0, Qt.SortOrder.AscendingOrder)

        self._selection_model = None

        self._remove_enabled = False
        self._mark_enabled = False

    @property
    def add_icon(self) -> QIcon:
        return self._add_icon

    @property
    def remove_icon(self) -> QIcon:
        return self._remove_icon

    @property
    def mark_icon(self) -> QIcon:
        return self._mark_icon

    @property
    def proxy_task_model(self):
        return self._proxy_task_model

    @property
    def selection_model(self):
        return self._selection_model

    @selection_model.setter
    def selection_model(self, model: QItemSelectionModel):
        self._selection_model = model

    @property
    def remove_enabled(self) -> bool:
        return self._remove_enabled

    @remove_enabled.setter
    def remove_enabled(self, enabled: bool):
        self._remove_enabled = enabled
        self.remove_enabled_changed.emit(enabled)

    @property
    def mark_enabled(self) -> bool:
        return self._mark_enabled

    @mark_enabled.setter
    def mark_enabled(self, enabled: bool):
        self._mark_enabled = enabled
        self.mark_enabled_changed.emit(enabled)

    def open_create_dialog(self):
        dialog = self._create_edit_dialog_factory.create_dialog()
        if dialog.exec():
            self._task_model.insert_task(self._task_model.rowCount(), dialog.task)

        self.selection_model.clear()

    def open_edit_dialog(self, index: QModelIndex):
        index = self._proxy_task_model.mapToSource(index)
        dialog = self._create_edit_dialog_factory.edit_dialog(index.data(Qt.ItemDataRole.UserRole))
        if dialog.exec():
            self._task_model.setData(index, dialog.task)

    def open_remove_confirm_dialog(self):
        index = self._get_current_selection_source()
        task = index.data(Qt.ItemDataRole.UserRole)
        self._selection_model.clear()
        dialog = self._confirm_dialog_factory.create(
            title="Remove task",
            message=f"Are you sure you want to remove {task.name}?"
        )

        if dialog.exec():
            self._task_model.remove_task(index)

    def open_mark_confirm_dialog(self):
        index = self._get_current_selection_source()
        task = index.data(Qt.ItemDataRole.UserRole)
        self._selection_model.clear()
        dialog = self._confirm_dialog_factory.create(
            title="Mark task as completed",
            message=f"Are you sure you want to mark {task.name} as completed?"
        )

        if dialog.exec():
            task.completed = True
            self._task_model.setData(index=index, value=task)

    def _get_current_selection_source(self) -> QModelIndex:
        return self._proxy_task_model.mapToSource(self._selection_model.currentIndex())


class BacklogController(QObject):
    """
        Controller of the backlog window
    """
    def __init__(self, model: BacklogModel):
        super(BacklogController, self).__init__()
        self._model = model

    @pyqtSlot()
    def on_add_clicked(self):
        self._model.open_create_dialog()

    @pyqtSlot(QModelIndex)
    def on_edit_clicked(self, index: QModelIndex):
        self._model.open_edit_dialog(index)

    @pyqtSlot()
    def on_remove_clicked(self):
        self._model.open_remove_confirm_dialog()

    @pyqtSlot()
    def on_mark_clicked(self):
        self._model.open_mark_confirm_dialog()

    @pyqtSlot(QItemSelection, QItemSelection)
    def on_select_changed(self, current_selection, previous_selection):
        if len(current_selection) == 1 and len(previous_selection) == 0:
            self._model.mark_enabled = True
            self._model.remove_enabled = True

        if len(current_selection) == 0 and len(previous_selection) == 1:
            self._model.mark_enabled = False
            self._model.remove_enabled = False


class BacklogView(QWidget):
    """
        View of the backlog window
    """
    def __init__(self, controller: BacklogController, model: BacklogModel):
        super(BacklogView, self).__init__()

        self._controller = controller
        self._model = model

        self._add_button = QPushButton(icon=self._model.add_icon, parent=self)
        self._remove_button = QPushButton(icon=self._model.remove_icon, parent=self)
        self._mark_button = QPushButton(icon=self._model.mark_icon, parent=self)

        self._task_view = QListView(self)

        self._init_state()
        self._init_bindings()
        self._init_layout()

    def _init_state(self):
        self._remove_button.setEnabled(self._model.remove_enabled)
        self._mark_button.setEnabled(self._model.mark_enabled)

        self._task_view.setModel(self._model.proxy_task_model)
        self._model.selection_model = self._task_view.selectionModel()

    def _init_layout(self):
        layout = QHBoxLayout(self)
        list_button_layout = QVBoxLayout()

        list_button_layout.addWidget(self._add_button)
        list_button_layout.addWidget(self._remove_button)
        list_button_layout.addWidget(self._mark_button)
        list_button_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        layout.addWidget(self._task_view)
        layout.addLayout(list_button_layout)

    def _init_bindings(self):
        self._add_button.pressed.connect(self._controller.on_add_clicked)
        self._remove_button.pressed.connect(self._controller.on_remove_clicked)
        self._mark_button.pressed.connect(self._controller.on_mark_clicked)
        self._task_view.doubleClicked.connect(self._controller.on_edit_clicked)
        self._task_view.selectionModel().selectionChanged.connect(self._controller.on_select_changed)

        self._model.remove_enabled_changed.connect(self._on_remove_enabled_changed)
        self._model.mark_enabled_changed.connect(self._on_mark_enabled_changed)

    @pyqtSlot(bool)
    def _on_remove_enabled_changed(self, enabled: bool):
        self._remove_button.setEnabled(enabled)

    @pyqtSlot(bool)
    def _on_mark_enabled_changed(self, enabled: bool):
        self._mark_button.setEnabled(enabled)


class BacklogWindow(AbstractWindow):
    """
        Window allowing the user to view, edit, create and remove tasks
        The window implements the MVC pattern.
    """
    def __init__(self, create_edit_task_dialog_factory: CreateEditTaskDialogFactory,
                 confirm_dialog_factory: ConfirmDialogFactory, task_model: TaskListModel):
        super(BacklogWindow, self).__init__()

        self._model = BacklogModel(create_edit_task_dialog_factory, confirm_dialog_factory, task_model)
        self._controller = BacklogController(self._model)
        self._view = BacklogView(self._controller, self._model)

        layout = QVBoxLayout(self)
        layout.addWidget(self._view)
        self.setLayout(layout)

        self._center()


class BacklogFactory(ABC):
    @abstractmethod
    def create(self) -> BacklogWindow:
        raise NotImplementedError


class BacklogFactoryImpl(BacklogFactory):
    def __init__(self, create_edit_task_dialog_factory: CreateEditTaskDialogFactory,
                 confirm_dialog_factory: ConfirmDialogFactory, task_model: TaskListModel):
        self._task_model = task_model
        self._create_edit_task_dialog_factory = create_edit_task_dialog_factory
        self._confirm_dialog_factory = confirm_dialog_factory

    def create(self) -> BacklogWindow:
        return BacklogWindow(self._create_edit_task_dialog_factory, self._confirm_dialog_factory, self._task_model)
