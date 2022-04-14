from PyQt5.QtCore import QAbstractListModel, QModelIndex, Qt, QVariant

from application.models import Task
from db import TaskRepository


class TaskListModel(QAbstractListModel):
    """
        Model that handles the insertion, deletion and manipulation of tasks
    """
    DEFAULT = Task("None", 6, 0, 0)
    SORT_PRIORITY_ROLE = Qt.ItemDataRole.UserRole + 1
    SORT_NAME_ROLE = Qt.ItemDataRole.UserRole + 2

    def __init__(self, task_repository: TaskRepository, parent=None):
        super().__init__(parent)
        self._repository = task_repository
        self._data = [self.DEFAULT] + self._repository.tasks

    def rowCount(self, parent: QModelIndex = None) -> int:
        return len(self._data)

    def insert_task(self, row: int, item: Task, parent: QModelIndex = QModelIndex()) -> bool:
        try:
            self._repository.add(item)
        except:
            return False

        self.beginInsertRows(parent, row, row)
        self._data.insert(row, item)
        self.endInsertRows()

        return True

    def remove_task(self, index: QModelIndex) -> bool:
        task = index.data(Qt.ItemDataRole.UserRole)

        try:
            self._repository.remove(task)
        except:
            return False

        self.beginRemoveRows(index, index.row(), index.row())
        self._data.remove(task)
        self.endRemoveRows()

        return True

    def setData(self, index: QModelIndex, value: Task, role: int = ...) -> bool:
        if index.isValid():
            try:
                self._repository.update(value)
            except:
                return False

            self.dataChanged.emit(index, index, {})
            return True

        return False

    def data(self, index: QModelIndex, role: int = 0):
        row = index.row()
        data = self._data[row]

        if role == Qt.ItemDataRole.DisplayRole:
            return QVariant(f"{data.name} [{data.completed_workload}/{data.total_workload}]")
        elif role == Qt.ItemDataRole.UserRole:
            return QVariant(data)
        elif role == Qt.ItemDataRole.UserRole + 1:
            return QVariant(data.priority)
        elif role == Qt.ItemDataRole.UserRole + 2:
            return QVariant(data.name)
