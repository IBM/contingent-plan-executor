import time

from hovor.runtime.fields_container import FieldsContainer


class ActionResult(FieldsContainer):
    def __init__(self):
        super().__init__()

        self._is_action_started = False
        self._is_action_complete = False

        self._action_start_time = None
        self._action_end_time = None

    @property
    def json(self):
        return {
            'fields': self._fields,
            'status': 'completed' if self._is_action_complete else 'started' if self._is_action_started else 'not-started',
            'start-time': self._action_start_time,
            'end-time': self._action_end_time
        }

    def start_action(self):
        if self._is_action_started:
            raise ValueError("Cannot start action twice.")

        self._is_action_started = True
        self._action_start_time = time.time()

    def end_action(self):
        if self._is_action_complete:
            raise ValueError("Cannot complete action twice.")

        if not self._is_action_started:
            raise ValueError("Cannot finish action before start.")

        self._action_end_time = time.time()
        self._is_action_started = False
        self._is_action_complete = True

    def set_field(self, field, value):
        self._require_modification_rights()

        super().set_field(field, value)

    def _can_be_modified(self):
        return self._is_action_started and not self._is_action_complete

    def _require_modification_rights(self):
        if not self._can_be_modified():
            raise ValueError("Action result cannot be modified in this state.")
