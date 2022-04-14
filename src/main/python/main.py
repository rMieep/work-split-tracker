import sys

from fbs_runtime.application_context.PyQt5 import ApplicationContext
from PyQt5.QtWidgets import QMessageBox

import utils
from application.app import WorkSplitTracker, WSTContext
from application.settings import SettingsNotifier
from application.timer import CountdownTimerContext, CountdownTimerController
from db import SettingsRepositoryImpl, SQLiteSessionManager, TaskRepositoryImpl, WorkBreakActivityRepository
from gui.activity import ActivityTableModel
from gui.dialogs.confirm import ConfirmDialogFactoryImpl
from gui.dialogs.task import CreateEditTaskDialogFactoryImpl, TaskCompletedDialogFactoryImpl
from gui.task import TaskListModel
from gui.tray import Tray
from gui.windows.analytics import AnalyticsFactoryImpl
from gui.windows.backlog import BacklogFactoryImpl
from gui.windows.log import LogFactoryImpl
from gui.windows.settings import SettingsFactoryImpl
from gui.windows.timer import CountdownTimerFactoryImpl


def main():
    app_context = ApplicationContext()
    app = app_context.app
    app.setQuitOnLastWindowClosed(False)
    utils.resource_provider = utils.ResourceProvider(app_context)

    if not Tray.isSystemTrayAvailable():
        QMessageBox.critical(None, "System Tray", "System tray was not detected!")
        sys.exit(1)

    # DB Access
    session_manager = SQLiteSessionManager()
    settings_repository = SettingsRepositoryImpl(session_manager)
    task_repository = TaskRepositoryImpl(session_manager)
    activity_repository = WorkBreakActivityRepository(session_manager)

    # Application
    settings_notifier = SettingsNotifier(settings_repository)
    wst_context = WSTContext()
    timer_context = CountdownTimerContext()
    wst_timer_controller = CountdownTimerController(wst_context=wst_context, timer_context=timer_context,
                                                    settings_notifier=settings_notifier)
    wst = WorkSplitTracker(wst_context)

    # GUI
    task_model = TaskListModel(task_repository)
    activity_model = ActivityTableModel(activity_repository)
    create_edit_task_dialog_factory = CreateEditTaskDialogFactoryImpl()
    confirm_dialog_factory = ConfirmDialogFactoryImpl()
    task_completed_dialog_factory = TaskCompletedDialogFactoryImpl()
    timer_factory = CountdownTimerFactoryImpl(wst=wst, wst_timer_controller=wst_timer_controller,
                                              task_model=task_model,
                                              task_completed_dialog_factory=task_completed_dialog_factory)
    backlog_factory = BacklogFactoryImpl(create_edit_task_dialog_factory, confirm_dialog_factory, task_model)
    analytics_factory = AnalyticsFactoryImpl(task_model, activity_model)
    log_factory = LogFactoryImpl(activity_model)
    settings_factory = SettingsFactoryImpl(settings_notifier)
    tray = Tray(
        app=app,
        wst=wst,
        wst_timer_controller=wst_timer_controller,
        activity_model=activity_model,
        settings_notifier=settings_notifier,
        timer_factory=timer_factory,
        backlog_factory=backlog_factory,
        analytics_factory=analytics_factory,
        log_factory=log_factory,
        settings_factory=settings_factory
    )

    tray.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
