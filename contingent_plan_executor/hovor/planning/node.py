class Node(object):
    """
    Represents a node in a contingent plan.

    Only the stated fields are mandatory.
    Other optional info can be added by ConfigurationProvider implementations
    """

    def __init__(self, id, partial_state, is_initial, is_goal):
        self._is_initial = is_initial
        self._is_goal = is_goal
        self._id = id
        self._partial_state = partial_state

    @property
    def node_id(self):
        return self._id

    @property
    def is_initial(self):
        return self._is_initial

    @property
    def is_goal(self):
        return self._is_goal

    @property
    def partial_state(self):
        # partial state defined for the node
        return self._partial_state

    def __hash__(self):
        return hash(self._id)

    def __eq__(self, other):
        return self.node_id == other.node_id
