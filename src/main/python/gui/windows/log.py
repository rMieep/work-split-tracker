from abc import abstractmethod, ABC

from PyQt5.QtWidgets import QAbstractItemView, QHBoxLayout, QTableView

from gui.activity import ActivityTableModel
from gui.windows.mainwindow import AbstractWindow


class LogWindow(AbstractWindow):
    """
        Window displaying the latest activities
    """
    def __init__(self, activity_model: ActivityTableModel):
        super(LogWindow, self).__init__()

        layout = QHBoxLayout(self)

        self.log_view = QTableView()
        self.log_view.verticalHeader().hide()
        self.log_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.log_view.setModel(activity_model)

        layout.addWidget(self.log_view)

        self._center()


class LogFactory(ABC):
    @abstractmethod
    def create(self) -> LogWindow:
        raise NotImplementedError


class LogFactoryImpl(LogFactory):
    def __init__(self, activity_model: ActivityTableModel):
        self._activity_model = activity_model

    def create(self) -> LogWindow:
        return LogWindow(self._activity_model)
