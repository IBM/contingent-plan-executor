from hovor.planning.node import Node


class PlanBase(object):
    """
    Encapsulates state structure and traversing logic of the contingent plan.
    """

    def __init__(self, domain):
        self._domain = domain

    @property
    def domain(self):
        """
        The planning domain description.
        """
        return self._domain

    def get_next_node(self, current_node, next_state, outcome_name):
        """
        Implements plan traversal logic.
        Given the current_node in plan and the next_state, next_node needs to be find.

        Different traversing strategies can be implemented in different plans.
        :return: the Node
        """
        raise NotImplementedError("has to be overriden")

    def get_initial_node(self) -> Node:
        """
        Finds an initial node of the plan.
        """
        raise NotImplementedError
