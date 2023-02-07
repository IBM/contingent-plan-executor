from copy import deepcopy

from hovor.runtime.action_result import ActionResult
from hovor.runtime.outcome_determination_result import OutcomeDeterminationResult
from hovor.session.session_base import SessionBase


class OutcomeDeterminationProgress(object):
    """
    Keeps track on determination progress (a couple of determination reports for each evaluated outcome group can be created).

    Can be used as a detailed information source for execution monitoring analysis.
    """

    def __init__(self, session: SessionBase, action_result: ActionResult, parent=None):
        self._parent = parent
        self._session = session
        self._action_result = action_result
        self._final_outcome_name = None
        self._edge = None

        self._actual_state = session.current_state
        self._actual_context = session.get_context_copy()
        self._actual_determination_result = OutcomeDeterminationResult()
        self._force_invalidation = False

        # stores monitoring information for this particular instance of progress (it is not propagated through)
        # author names are used for indexing the information
        self._monitoring_info = {}

        if parent:
            self._force_invalidation = parent._force_invalidation
            self._actual_state = parent._actual_state  # state is immutable - no copies are required
            self._actual_context = deepcopy(parent._actual_context)
            self._actual_determination_result = deepcopy(parent._actual_determination_result)

        # keep initial execution info, so deltas can be computed
        self._initial_state = self._actual_state  # state is immutable - no copies are required
        self._initial_context = deepcopy(self._actual_context)

    def create_child(self):
        return OutcomeDeterminationProgress(self._session, self._action_result, self)

    @property
    def final_outcome_name(self):
        return self._final_outcome_name

    @property
    def actual_state(self):
        return self._actual_state

    @property
    def actual_context(self):
        return self._actual_context

    @property
    def action_result(self):
        return self._action_result

    @property
    def json(self):
        if self._edge:
            id = self._edge.edge_id
        else:
            id = None
        return {
            'action_result': self.action_result.json,
            'id': id
        }

    def associate_edge(self, source_node):
        for edge in self._session.plan.edges:
            if edge.src == source_node and edge.outcome_id == self._final_outcome_name:
                self._edge = edge
                return

        raise AssertionError(f"Edge was not found for node: '{source_node}'.")

    def add_monitor_field(self, author_name, field_name, monitored_value):
        if not author_name in self._monitoring_info:
            self._monitoring_info[author_name] = {}

        monitor = self._monitoring_info[author_name]
        monitor[field_name] = monitored_value

    def add_monitor_fields(self, author_name, fields: dict):
        for field, value in fields.items():
            self.add_monitor_field(author_name, field, value)

    def get_monitored_values(self):
        return deepcopy(self._monitoring_info)

    def invalidate(self):
        self._force_invalidation = True

    def collect_monitored_values(self):
        """
        Collects all monitored values registered from the progress root.
        """
        result = []

        current_progress = self
        while current_progress is not None:
            result.extend(current_progress._monitoring_info.items())

            current_progress = current_progress._parent

        return result

    def collect_state_delta(self):
        """
        Collects changes in state during the progress chain.
        """

        # states are complete, therefore, only positive fluents needs to be checked
        chain_start = self._get_progress_chain_start()
        initial_state = chain_start._initial_state

        removed_fluents = []
        for fluent in initial_state.get_positive_fluents():
            if not self._actual_state.contains(fluent):
                # fluent positive at the beginning, negative now ==> fluent removed
                removed_fluents.append(fluent)

        added_fluents = []
        for fluent in self._actual_state.get_positive_fluents():
            if not initial_state.contains(fluent):
                # fluent positive at the end, negative at the begining ==> fluent added
                added_fluents.append(fluent)

        return removed_fluents, added_fluents

    def collect_context_delta(self):
        """
        Collects changes in context during the progress chain.
        """

        chain_start = self._get_progress_chain_start()
        initial_context = chain_start._initial_context

        removed_entities = []
        for entity in initial_context.field_names:
            entity_value = initial_context.get_field(entity)
            new_entity_value = self._actual_context.get_field(entity)
            if entity_value != new_entity_value:
                # new entity value is different from old one (it can be either due to removal, or override - which is treated as remove-add sequence)
                removed_entities.append((entity, entity_value))

        added_entities = []
        for entity in self._actual_context.field_names:
            entity_value = initial_context.get_field(entity)
            new_entity_value = self._actual_context.get_field(entity)

            if entity_value != new_entity_value:
                # new entity was added, or some entity was overridden
                added_entities.append((entity, new_entity_value))

        return removed_entities, added_entities

    def get_determiner(self, outcome_group_name):
        info = self.get_outcome_determination_info(outcome_group_name)
        return info.outcome_determiner

    def apply_effect(self, outcome_group_name):
        info = self.get_outcome_determination_info(outcome_group_name)

        for context_effect in info.context_effects:
            self.run_effect(context_effect)

    def run_effect(self, context_effect):
        if not self.is_valid():
            return

        effect_success = context_effect(self._actual_context, self._actual_determination_result)
        if not effect_success:
            self._force_invalidation = True

    def apply_state_update(self, state_update):
        self._actual_state = self._actual_state.update_by(state_update)

    def remove_entities(self, required_missing_entities):
        for entity in required_missing_entities:
            self._actual_context.remove_field(entity)

    def get_description(self, outcome_group_name):
        return self.get_outcome_determination_info(outcome_group_name).description

    def get_outcome_determination_info(self, outcome_group_name):
        return self._session.configuration.get_outcome_determination_info(outcome_group_name)

    def get_entity_type(self, entity):
        return self._session.plan.domain["entities"][entity]

    def get_entity_config(self, entity):
        return self._session.plan.domain["entity_configs"][entity]

    def add_detected_entity(self, entity, value):
        self._actual_determination_result.set_field(entity, value)

    def finalize(self, outcome_name):
        self._final_outcome_name = outcome_name

    def is_valid(self):
        if self._force_invalidation:
            return False

        return True

    def _get_progress_chain_start(self):
        chain_start = self
        while chain_start._parent is not None:
            chain_start = chain_start._parent
        return chain_start
