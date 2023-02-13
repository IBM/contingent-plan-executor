from copy import deepcopy

import jsonpickle, json 
import sqlalchemy

from hovor.session.in_memory_session import InMemorySession
from hovor.runtime.outcome_determination_progress import OutcomeDeterminationProgress
from hovor import db

class ConversationDatabase(db.Model):
    convo_id = db.Column(db.String, unique=True, nullable=False, primary_key=True)
    state = db.Column(db.PickleType, nullable=True)
    action = db.Column(db.PickleType, nullable=True)
    action_result = db.Column(db.PickleType, nullable=True)
    context = db.Column(db.PickleType, nullable=True)
    node_id = db.Column(db.PickleType, nullable=True)
    history = db.Column(db.PickleType, nullable=True)

class DatabaseSession(InMemorySession):
    def __init__(self, db, conversation_id, configuration_provider):
        # Prepopulate the superclass
        super(DatabaseSession, self).__init__(configuration_provider)
        try:
            conversation = db.session.execute(db.select(ConversationDatabase).filter_by(convo_id=conversation_id)).scalar_one()
            # initially created database will have convo_id and nothing else,
            # so only load the rest if it exists.
            # we assume if the state is null we're dealing with a fresh conversation.
            if conversation.state:
                self._current_state = jsonpickle.decode(conversation.state)
                self._current_action = jsonpickle.decode(conversation.action)
                self._current_action_result = jsonpickle.decode(conversation.action_result)
                self._current_context = jsonpickle.decode(conversation.context)
                self._current_node = configuration_provider.plan.get_node_from_id(conversation.node_id)
                self._delta_history = conversation.history
        except sqlalchemy.exc.NoResultFound:
            pass


    def save(self, db, conversation_id):
        conversation = db.query.filter_by(convo_id=conversation_id).first()
        conversation.state = jsonpickle.encode(self._current_state)
        conversation.action = jsonpickle.encode(self._current_action)
        if hasattr(self._current_action, "_utterance"):
            conversation.action_result = jsonpickle.encode(self._current_action._utterance)
        conversation.context = jsonpickle.encode(self._current_context)
        conversation.node_id = self._current_node.node_id
        # All but the last element will be json, and the last element is the full
        #  object so that the progress can be reported in the in_memory_session
        conversation.history = [prog.json if isinstance(prog, OutcomeDeterminationProgress)
                                    else prog for prog in self.delta_history]
        db.session.commit()
