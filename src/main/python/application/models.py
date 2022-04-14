from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Task(Base):
    __tablename__ = "task"
    id = Column(Integer, primary_key=True)
    name = Column(String(length=50))
    priority = Column(Integer)
    completed_workload = Column(Integer)
    total_workload = Column(Integer)
    completed = Column(Boolean)
    activities = relationship("WorkActivity", back_populates="task_reference")

    def __init__(self, name: str, priority: int, completed_workload: int, total_workload: int):
        self.name = name
        self.priority = priority
        self.completed_workload = completed_workload
        self.total_workload = total_workload
        self.completed = False
        self.activities = []


class Activity(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True)
    date = Column(DateTime)
    duration = Column(Integer)
    expected_duration = Column(Integer)

    def __init__(self, date: datetime, expected_duration: int):
        self.date = date
        self.expected_duration = expected_duration


class WorkActivity(Activity):
    __tablename__ = "work-activity"
    task_id = Column(Integer, ForeignKey(Task.id))
    task_reference = relationship("Task", back_populates="activities")

    def __init__(self, date: datetime, expected_duration: int, work_item: Task):
        super(WorkActivity, self).__init__(date, expected_duration)

        if work_item:
            self.task_id = work_item.id
            self.task_reference = work_item


class BreakActivity(Activity):
    __tablename__ = "break-activity"


class Settings(Base):
    __tablename__ = "settings"
    id = Column(Integer, primary_key=True)
    work_time = Column(Integer, default=20)
    break_time = Column(Integer, default=5)
    play_sound = Column(Boolean, default=False)
    show_notification = Column(Boolean, default=True)
