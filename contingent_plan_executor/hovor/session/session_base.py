class SessionBase(object):
    """
    Base class for accessing plan, state, and context data.
    Is responsible for defining initial state, context, and action in __init__.
    ALL METHODS MUST BE OVERRIDDEN.
    """

    @property
    def plan(self):
        """The active plan for the session"""
        raise NotImplementedError("must be overriden")

    @property
    def configuration(self):
        """The active configuration provider for the session"""
        raise NotImplementedError("must be overriden")

    @property
    def current_node(self):
        """
        Gets the current node in the plan that the agent is at
        :return: The current node in the plan
        """
        raise NotImplementedError("must be overriden")

    @property
    def current_state(self):
        """
        Gets currently processed state
        :return: The processed state
        """
        raise NotImplementedError("must be overriden")

    @property
    def current_action(self):
        """
        Gets next action to be executed
        :return: The action
        """
        raise NotImplementedError("must be overriden")

    def update_by(self, progress):
        """
        Updates session to state and context described by the give progress.
        Action for given state is created. (Available through current_action property)

        :param progress: State to be set
        """
        raise NotImplementedError("must be overriden")

    def get_context_copy(self):
        """
        Gets copy of currently processed context.
        :return: The processed context copy
        """
        raise NotImplementedError("must be overriden")
