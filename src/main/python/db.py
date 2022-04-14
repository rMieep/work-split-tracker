import os.path
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

from appdirs import user_data_dir
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from application.models import Activity, Base, BreakActivity, Settings, Task, WorkActivity


class DBSessionManager(ABC):
    @property
    @abstractmethod
    def session(self) -> sessionmaker:
        raise NotImplementedError


class SQLiteSessionManager(DBSessionManager):
    def __init__(self, path_to_db: str = 'work-split-tracker.db'):
        if getattr(sys, 'frozen', False):
            app_dir = user_data_dir("work-split-tracker", "rMieep")
            Path(app_dir).mkdir(parents=True, exist_ok=True)
        else:
            app_dir = os.path.dirname(os.path.abspath(__file__))
        engine = create_engine('sqlite:///' + app_dir + '/' + path_to_db)
        Base.metadata.create_all(engine)
        self._sqlite_session = sessionmaker(bind=engine, expire_on_commit=False)

    @property
    def session(self):
        return self._sqlite_session


class WorkActivityRepository(ABC):
    @property
    @abstractmethod
    def work_activities(self) -> List[WorkActivity]:
        raise NotImplementedError

    @abstractmethod
    def add_work_activity(self, activity: WorkActivity):
        raise NotImplementedError

    @abstractmethod
    def update_work_activity(self, activity: WorkActivity):
        raise NotImplementedError


class BreakActivityRepository(ABC):
    @property
    @abstractmethod
    def break_activities(self) -> List[BreakActivity]:
        raise NotImplementedError

    @abstractmethod
    def add_break_activity(self, activity: BreakActivity):
        raise NotImplementedError

    @abstractmethod
    def update_break_activity(self, activity: BreakActivity):
        raise NotImplementedError


class TaskRepository(ABC):
    @property
    @abstractmethod
    def tasks(self) -> List[Task]:
        raise NotImplementedError

    @abstractmethod
    def add(self, task: Task):
        raise NotImplementedError

    @abstractmethod
    def remove(self, task: Task):
        raise NotImplementedError

    @abstractmethod
    def update(self, task: Task):
        raise NotImplementedError


class SettingsRepository(ABC):
    @abstractmethod
    def get(self) -> Settings:
        raise NotImplementedError

    @abstractmethod
    def update(self, settings: Settings):
        raise NotImplementedError


class WorkBreakActivityRepository(WorkActivityRepository, BreakActivityRepository):
    def __init__(self, session_manager: DBSessionManager):
        self.__session_manager = session_manager

    @property
    def work_activities(self) -> List[WorkActivity]:
        with self.__session_manager.session() as session:
            return session.query(WorkActivity).all()

    @property
    def break_activities(self) -> List[BreakActivity]:
        with self.__session_manager.session() as session:
            return session.query(BreakActivity).all()

    @property
    def activities(self) -> List[Activity]:
        with self.__session_manager.session() as session:
            return session.query(WorkActivity).all() + session.query(BreakActivity).all()

    def add_work_activity(self, activity: WorkActivity):
        with self.__session_manager.session.begin() as session:
            session.add(activity)

    def add_break_activity(self, activity: BreakActivity):
        with self.__session_manager.session.begin() as session:
            session.add(activity)

    def update_work_activity(self, activity: WorkActivity):
        with self.__session_manager.session.begin() as session:
            session.merge(activity)

    def update_break_activity(self, activity: BreakActivity):
        with self.__session_manager.session.begin() as session:
            session.merge(activity)


class TaskRepositoryImpl(TaskRepository):
    def __init__(self, session_manager: DBSessionManager):
        self.__session_manager = session_manager

    @property
    def tasks(self) -> List[Task]:
        with self.__session_manager.session() as session:
            return session.query(Task).all()

    def add(self, task: Task):
        with self.__session_manager.session.begin() as session:
            session.add(task)

    def remove(self, task: Task):
        with self.__session_manager.session.begin() as session:
            session.delete(task)

    def update(self, task: Task):
        with self.__session_manager.session.begin() as session:
            session.merge(task)


class SettingsRepositoryImpl(SettingsRepository):
    def __init__(self, session_manager: DBSessionManager):
        self.__session_manager = session_manager

    def get(self) -> Settings:
        with self.__session_manager.session.begin() as session:
            settings = session.query(Settings).first()

            if not settings:
                settings = Settings()
                session.add(settings)

        return settings

    def update(self, settings: Settings):
        with self.__session_manager.session.begin() as session:
            session.merge(settings)
