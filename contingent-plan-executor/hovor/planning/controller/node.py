
from hovor.planning.node import Node

class ControllerNode(Node):
    """
    Node API specific to a plan represented as a controller.
    """

    def __init__(self, id, partial_state, is_initial, is_goal):
        super(ControllerNode, self).__init__(id, partial_state, is_initial, is_goal)
