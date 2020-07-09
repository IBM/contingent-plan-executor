class ConfigurationProviderBase(object):
    def __init__(self, id, plan):
        self._id = id
        self._plan = plan

    @property
    def plan(self):
        """
        The plan which configuration is represented.
        """
        return self._plan

    @property
    def id(self):
        """
        Id of the configuration provider.
        """
        return self._id

    def get_outcome_determination_info(self, outcome_group_name):
        """
        Gets the actual OutcomeDeterminationInfo (can change throughout the time - but the changes should not been
        dependent on current node in the graph)

        The configuration changing can be used e.g. for live changes during debugging or for learning purposes
        (changing OD priors etc)


        :param outcome_group_name: The name of outcome group which info is retrieved.
        :return: OutcomeDeterminationInfo
        """
        raise NotImplementedError("has to be overriden")

    def get_node_info(self, node):
        """
        Gets the node info, which is in turn just information about the action.

        :param node: The plan node.
        :return: String of info.
        """
        raise NotImplementedError("has to be overriden")

    def get_node_type(self, node):
        """
        Gets the node type, which is in turn just type of the action.

        :param node: The plan node.
        :return: String of node (/action) type.
        """
        raise NotImplementedError("has to be overriden")

    def create_action(self, node, state, context):
        """
        Creates an action that can be run at given node in the given state and context.

        The action can be called once at maximum.
        """

        raise NotImplementedError("has to be overriden")

    def create_initial_effects(self):
        """
        Creates effects that should be used for context initialization
        """
        raise NotImplementedError("has to be overriden")
