from copy import deepcopy
from hovor.runtime.context import Context
from hovor.session.session_base import SessionBase
from hovor import DEBUG


class InMemorySession(SessionBase):
    def __init__(self, configuration_provider):
        super(InMemorySession, self).__init__()

        self._configuration_provider = configuration_provider
        self._current_node = None
        self._current_state = None
        self._current_action = None
        self._current_context = None
        self._delta_history = []
        self._action_names = {node.action_name for node in self.plan.nodes}

    @property
    def plan(self):
        return self._configuration_provider.plan

    @property
    def configuration(self):
        return self._configuration_provider

    @property
    def current_action(self):
        """Action currently processed"""
        return self._current_action

    @property
    def current_action_result(self):
        return self._current_action_result

    @property
    def current_state(self):
        return self._current_state

    @property
    def delta_history(self):
        return self._delta_history

    def load_initial_plan_data(self):
        if self._current_node is not None:
            raise ValueError("It is too late for initial data loading.")

        self._current_node = self.plan.get_initial_node()
        self._current_state = self._current_node.partial_state
        self._current_context = Context()

    def create_initial_action(self):
        if self._current_action is not None:
            raise AssertionError("It is too late for initial action creation.")

        self._update_action()

    def update_context_by(self, progress):
        if self != progress._session:
            raise ValueError("Inconsistent session access detected.")

        next_context = progress.actual_context
        self._current_context = deepcopy(next_context)
        self._delta_history.append(progress)
        # self._print_update_report()

    def update_by(self, progress):
        if self != progress._session:
            raise ValueError("Inconsistent session access detected.")

        next_state = progress.actual_state
        next_context = progress.actual_context

        n1 = self._current_node

        # update the current state, context, and node
        self._current_state = next_state
        self._current_context = deepcopy(next_context)
        self._current_node = self.plan.get_next_node(self._current_node, self._current_state,
                                                     progress.final_outcome_name)

        n2 = self._current_node

        progress.apply_state_update(n2.partial_state)
        progress.associate_edge(n1)

        if self._current_action:
            if self._current_node.action_name == "dialogue_statement":
                # currently, we will only get a dialogue statement through a fallback or a response
                if progress._edge.info["intent"] == "fallback":
                    if "fallback_message_variants" in self._current_action.config:
                        self.configuration._configuration_data["actions"]["dialogue_statement"]["message_variants"] = self.configuration._configuration_data["actions"][self.current_action.name]["fallback_message_variants"]
                else:
                    for outcfg in self.configuration._configuration_data["actions"][self.current_action.name]["effect"]["outcomes"]:
                        if outcfg["name"] == progress.final_outcome_name:
                            self.configuration._configuration_data["actions"]["dialogue_statement"]["message_variants"] = outcfg["response_variants"]
                            break
        self._update_action()
        self._delta_history.append(progress)
        # self._print_update_report()

    def update_action_result(self, result):
        self._current_action_result = result

    def get_context_copy(self):
        return deepcopy(self._current_context)

    def _update_action(self):
        self._current_action = self._configuration_provider.create_action(self._current_node, self._current_state,
                                                                          self.get_context_copy())

    def _print_update_report(self):
        current_progress = self._delta_history[-1]

        values = current_progress.collect_monitored_values()
        DEBUG("\t outcome determination monitor: " + str(values))

        context_delta_removed, context_delta_added = current_progress.collect_context_delta()
        DEBUG("\t context removed: " + str(context_delta_removed))
        DEBUG("\t context added: " + str(context_delta_added))

        removed_fluents, added_fluents = current_progress.collect_state_delta()
        DEBUG("\t fluents removed: " + str(removed_fluents))
        DEBUG("\t fluents added: " + str(added_fluents))
