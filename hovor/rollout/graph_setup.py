from typing import Iterable
from graphviz import Digraph


class GraphGenerator:
    def __init__(self):
        self._label_map = {}
        self._idx = "0"
        self._parent = "0"
        self.graph = Digraph()
        self.graph.node(self._idx, "START", fillcolor="darkolivegreen3", style="filled")

    def _inc_idx(self):
        self._idx = str(int(self._idx) + 1)

    def _set_last_chosen(self, new_id):
        self._parent = str(new_id)

    def create_from_parent(self, nodes: Iterable[str], fillcolor: str, new_parent: str):
        for node in nodes:
            edge_color = "black"
            self._inc_idx()
            self.graph.node(self._idx, node, fillcolor=fillcolor, style="filled")
            if new_parent:
                if node == new_parent:
                    new_parent_id = self._idx
                    edge_color = "red"
            self.graph.edge(self._parent, self._idx, color=edge_color)
        if new_parent:
            self._set_last_chosen(new_parent_id)

    def complete_conversation(self):
        self.create_from_parent(["GOAL REACHED"], "darkolivegreen3", "GOAL REACHED")
            