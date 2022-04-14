from enum import auto, Enum
from typing import Callable, Dict, Optional

from sortedcontainers import SortedList

from application.models import Task


class PriorityCallback:
    """
        A callback with a priority
    """
    def __init__(self, callback: Callable, priority: int):
        self._callback = callback
        self._priority = priority

    @property
    def priority(self) -> int:
        return self._priority

    @property
    def callback(self) -> Callable:
        return self._callback

    def __lt__(self, other):
        if self.priority == other.priority:
            return hash(self._callback) < hash(other.callback)
        return self.priority < other.priority

    def __call__(self, context):
        self.callback(context)

    def __eq__(self, other):
        if not isinstance(other, PriorityCallback):
            return NotImplemented

        return self.callback == other.callback

    def __hash__(self):
        return hash(self.callback)


def execute_priority_callbacks(priority_callbacks: SortedList, context):
    for priority_callback in reversed(priority_callbacks):
        priority_callback(context)


class IllegalWorkSplitTrackerStateException(Exception):
    pass


class WSTState(Enum):
    WORK = auto()
    BREAK = auto()
    IDLE = auto()


class WSTContext:
    """
        Context of the work-split-tracker
    """
    def __init__(self):
        self.state = WSTState.IDLE
        self.activity = None
        self.task = None
        self.stop_time = None
        self.work_time = None
        self.break_time = None
        self._before_state_change_callbacks = {}
        self._after_state_change_callbacks = {}

    @staticmethod
    def _push_state_change_callback(state_callback_dict: Dict[WSTState, SortedList],
                                    state: WSTState, callback: PriorityCallback):
        if state not in state_callback_dict:
            state_callback_dict[state] = SortedList()

        state_callback_dict[state].add(callback)

    def change_state(self, new_state: WSTState):
        if self.state == new_state:
            raise IllegalWorkSplitTrackerStateException(f"previousState: {self.state}, newState: {new_state}")

        self._before_state_change()
        self.state = new_state
        self._after_state_change()

    def _before_state_change(self):
        priority_callback_list = self._before_state_change_callbacks.get(self.state)

        if priority_callback_list:
            execute_priority_callbacks(priority_callback_list, self)

    def _after_state_change(self):
        priority_callback_list = self._after_state_change_callbacks.get(self.state)

        if priority_callback_list:
            execute_priority_callbacks(priority_callback_list, self)

    def push_before_state_change_callback(self, state: WSTState, callback: PriorityCallback):
        self._push_state_change_callback(self._before_state_change_callbacks, state, callback)

    def remove_before_state_change_callback(self, state: WSTState, callback: PriorityCallback):
        self._before_state_change_callbacks[state].remove(callback)

    def push_after_state_change_callback(self, state: WSTState, callback: PriorityCallback):
        self._push_state_change_callback(self._after_state_change_callbacks, state, callback)

    def remove_after_state_change_callback(self, state: WSTState, callback: PriorityCallback):
        self._after_state_change_callbacks[state].remove(callback)


class WorkSplitTracker:
    """
        Work Split Tracker app that can be used to work, break or idle
    """
    def __init__(self, context: WSTContext):
        self._context = context

    @property
    def context(self) -> WSTContext:
        return self._context

    def do_work(self, task: Optional[Task]):
        self._context.task = task
        self._context.change_state(WSTState.WORK)

    def do_break(self):
        self._context.change_state(WSTState.BREAK)

    def do_idle(self):
        self._context.change_state(WSTState.IDLE)
