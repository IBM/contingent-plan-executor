from hovor.runtime.action_result import ActionResult


class ActionBase(object):
    """Object that represents a fully defined action - ready to be executed.
    Everything required for the call has to be passed through via config, state and context.

    It can be called inside the execution monitor, or passed through some RPC call to other services (when external==True).

    Outcome group is a part of the action - it allows action -> outcome group communication
    e.g. credentials acquired by the action needs to be passed to OD etc.

    Outcome group will be visible after execution is called.
    """

    _registered_actions = {}

    def __init__(self, config, state, context, outcome_group):
        if outcome_group is None:
            raise ValueError("outcome group cannot be null")

        self._hidden_outcome_group = outcome_group
        self._outcome_group = None
        self.config = config
        self.name = config["name"]
        self.action_type = config["type"]
        self.state = state
        self.context = context

        # True if the execution of this action corresponds to an external call
        self.is_external = False

    @property
    def outcome_group(self):
        return self._outcome_group

    def is_deterministic(self):
        class_name = None
        if self._hidden_outcome_group is not None:
            class_name =  self._hidden_outcome_group.__class__.__name__
        return class_name is None or class_name == 'DeterministicOutcomeGroup'

    def _start_execution_callback(self, action_result):
        raise NotImplementedError("has to be overriden")

    def _end_execution_callback(self, action_result, info):
        raise NotImplementedError("has to be overriden")

    def start_execution(self):

        if not self._outcome_group:
            # make outcome group visible for the execution callback and the outside world
            self._outcome_group = self._hidden_outcome_group
            self._hidden_outcome_group = None

        result = ActionResult()
        result.start_action()
        self._start_execution_callback(result)
        return result

    def end_execution(self, result, info=None):
        self._end_execution_callback(result, info)
        result.end_action()

    def execute(self):
        # Can only monolithicly execute this if it is not external
        if self.is_external and not self.is_deterministic():
            raise ValueError("Cannot perform a complete execution for monolithic action of type %s" % self.action_type)

        result = self.start_execution()
        self.end_execution(result)

        return result


    @classmethod
    def register_action(cls, prefix, action_factory):
        """
        Registers an action factory for the given prefix. Is used for action name resolving.
        """

        ActionBase._registered_actions[prefix] = action_factory

    @classmethod
    def create_action(cls, config, state, context, outcome_group):
        """Create the appropriate action type given the action name."""

        action_type = config["type"]

        if action_type in ActionBase._registered_actions:
            return ActionBase._registered_actions[action_type](config, state, context, outcome_group)

        raise ValueError("Action type unrecognized: %s for %s" % (action_type, config))

    @classmethod
    def create_builder(cls, config, outcome_group):
        action_type = config["type"]

        if action_type not in ActionBase._registered_actions:
            raise ValueError("Action type %s not known for %s." % (action_type, config))

        builder = ActionBase._registered_actions[action_type]

        def builder_wrapper(state, context):
            action = builder(config, state, context, outcome_group)
            return action

        return builder_wrapper
