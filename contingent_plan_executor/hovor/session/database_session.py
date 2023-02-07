from copy import deepcopy

import jsonpickle, json

from hovor.session.in_memory_session import InMemorySession
from hovor.runtime.outcome_determination_progress import OutcomeDeterminationProgress


class DatabaseSession(InMemorySession):
    def __init__(self, db, conversation_id, configuration_provider):
        # Fetch the conversation first
        conversation = db[conversation_id]

        # Prepopulate the superclass
        super(DatabaseSession, self).__init__(configuration_provider)
        self._current_state = jsonpickle.decode(conversation['state'])
        self._current_action = jsonpickle.decode(conversation['action'])
        self._current_action_result = jsonpickle.decode(conversation['action_result'])
        self._current_context = jsonpickle.decode(conversation['context'])
        self._current_node = configuration_provider.plan.get_node_from_id(conversation['node_id'])
        self._delta_history = conversation['history']

    def save(self, db, conversation_id):
        conversation = db[conversation_id]
        conversation['state'] = jsonpickle.encode(self._current_state)
        conversation['action'] = jsonpickle.encode(self._current_action)
        conversation['action_result'] = jsonpickle.encode(self._current_action_result)
        conversation['context'] = jsonpickle.encode(self._current_context)
        conversation['node_id'] = self._current_node.node_id
        # All but the last element will be json, and the last element is the full
        #  object so that the progress can be reported in the in_memory_session
        conversation['history'] = [prog.json if isinstance(prog, OutcomeDeterminationProgress)
                                    else prog for prog in self.delta_history]
        conversation.save()
