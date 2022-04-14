from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt, QVariant

from application.models import Activity, BreakActivity, WorkActivity
from db import WorkBreakActivityRepository


def _is_work_activity(activity: Activity) -> bool:
    return isinstance(activity, WorkActivity)


class ActivityTableModel(QAbstractTableModel):
    """
        Model that handles the insertion, deletion and manipulation of activities
    """
    def __init__(self, activity_repository: WorkBreakActivityRepository, parent=None):
        super().__init__(parent)
        self._repository = activity_repository
        self._data = self._repository.activities
        self._horizontal_header = ['Name', 'Date', 'Duration', 'Expected Duration']

    def rowCount(self, parent: QModelIndex = None) -> int:
        return len(self._data)

    def columnCount(self, parent: QModelIndex = None) -> int:
        return 4

    def add_work_activity(self, item: WorkActivity, parent: QModelIndex = QModelIndex()) -> bool:
        try:
            self._repository.add_work_activity(item)
        except:
            return False

        self.beginInsertRows(parent, self.rowCount(), self.rowCount())
        self._data.insert(self.rowCount(), item)
        self.endInsertRows()

        return True

    def add_break_activity(self, item: BreakActivity, parent: QModelIndex = QModelIndex()) -> bool:
        try:
            self._repository.add_break_activity(item)
        except:
            return False

        self.beginInsertRows(parent, self.rowCount(), self.rowCount())
        self._data.insert(self.rowCount(), item)
        self.endInsertRows()

        return True

    def update_work_activity(self, activity: WorkActivity):
        try:
            self._repository.update_work_activity(activity)
        except:
            return False

        index = self._find_index_with_id(activity.id)
        self.dataChanged.emit(index, index, {})

    def update_break_activity(self, activity: BreakActivity):
        try:
            self._repository.update_break_activity(activity)
        except:
            return False

        index = self._find_index_with_id(activity.id)
        self.dataChanged.emit(index, index, {})

    def _find_index_with_id(self, activity_id: int):
        for index, activity in enumerate(self._data):
            if activity.id == activity_id:
                return self.index(index, 0)

        return None

    def data(self, index: QModelIndex, role: int = 0):
        row = index.row()
        column = index.column()
        data = self._data[row]

        if role == Qt.ItemDataRole.DisplayRole:
            if column == 0:
                if _is_work_activity(data):
                    return QVariant("Work")
                else:
                    return QVariant("Break")
            elif column == 1:
                return QVariant(data.date.strftime("%d.%m.%y %H:%M:%S"))
            elif column == 2:
                return QVariant(data.duration)
            elif column == 3:
                return QVariant(data.expected_duration)
        elif role == Qt.ItemDataRole.UserRole:
            return QVariant(data)

    def headerData(self, col: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self._horizontal_header[col]
        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled

