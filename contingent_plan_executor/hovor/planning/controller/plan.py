from hovor.actions.action_base import ActionBase
from hovor.planning.plan_base import PlanBase


class Plan(PlanBase):
    """
    Plan that selects next node according to node connections coming from the planner.
    It does not look at partial state matching quality.
    """

    def __init__(self, nodes, edges, domain):
        super(Plan, self).__init__(domain)
        self._nodes = list(nodes)
        self._edges = list(edges)

        # create some indexes for fast node lookups
        self._node_id_to_node = {}
        for node in self._nodes:
            self._node_id_to_node[node.node_id] = node

    @property
    def nodes(self):
        return self._nodes

    @property
    def edges(self):
        return self._edges

    def get_initial_node(self):
        """Finds initial state in the plan"""
        for node in self._nodes:
            if node.is_initial:
                return node

        return None

    def get_node_from_id(self, nid):
        return self._node_id_to_node[nid]

    def get_children(self, node):
        children = []
        for edge in self._edges:
            if edge.src == node:
                children.append(edge.dst)

        return children

    def get_next_node(self, current_node, next_state, outcome_name):
        candidates = []
        for child_name, child in current_node.named_children:
            if outcome_name == child_name:
                candidates.append(child)

        if len(candidates) == 0:
            raise AssertionError("Invalid state transition detected.")

        if len(candidates) > 1:
            raise AssertionError("Partial states are ambiguous.")

        candidate = candidates[0]

        # todo prp output semantic changed probably, entails is not ensured
        # if not next_state.entails(candidate.partial_state):
        #    raise AssertionError("Next state does not entail the candidate")

        return candidate
