import jsonpickle
import sqlalchemy

from hovor.session.in_memory_session import InMemorySession
from hovor.runtime.outcome_determination_progress import OutcomeDeterminationProgress


class DatabaseSession(InMemorySession):
    def __init__(self, db, conversation_id, configuration_provider, loading_from: bool = False):
        from app import ConversationDatabase
        # Prepopulate the superclass
        super(DatabaseSession, self).__init__(configuration_provider)
        try:
            conversation = db.session.execute(db.select(ConversationDatabase).filter_by(user_id=conversation_id)).scalar_one()
            # initially created database will have user_id and nothing else,
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
            if loading_from:
                raise ValueError("Invalid user ID provided.")


    def save(self, db, conversation_id):
        from app import ConversationDatabase
        try:
            conversation = db.session.execute(db.select(ConversationDatabase).filter_by(user_id=conversation_id)).scalar_one()
        except sqlalchemy.exc.NoResultFound:
            db.session.add(ConversationDatabase(user_id=conversation_id))

        conversation = db.session.execute(db.select(ConversationDatabase).filter_by(user_id=conversation_id)).scalar_one()
        conversation.state = jsonpickle.encode(self._current_state)
        conversation.action = jsonpickle.encode(self._current_action)
        conversation.action_result = jsonpickle.encode(self._current_action_result)
        conversation.context = jsonpickle.encode(self._current_context)
        conversation.node_id = self._current_node.node_id
        # All but the last element will be json, and the last element is the full
        #  object so that the progress can be reported in the in_memory_session
        conversation.history = [prog.json if isinstance(prog, OutcomeDeterminationProgress)
                                    else prog for prog in self.delta_history]

        db.session.commit()
