from typing import Iterable, Dict
from graphviz import Digraph


class GraphGenerator:
    def __init__(self):
        self._idx = "0"
        self._parent = "0"
        self.graph = Digraph()
        self.graph.node(self._idx, "START", fillcolor="darkolivegreen3", style="filled")

    def _inc_idx(self, inc: int = 1):
        self._idx = str(int(self._idx) + inc)

    def _set_last_chosen(self, new_id):
        self._parent = str(new_id)

    def complete_conversation(self):
        self.create_from_parent(["GOAL REACHED"], "darkolivegreen3", "GOAL REACHED")

    def create_from_parent(self, nodes: Iterable[str], fillcolor: str, new_parent: str = None):
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


class BeamSearchGraphGenerator(GraphGenerator):
    class Beam:
        def __init__(self, parent_nodes_id_map: Dict = None):
            if not parent_nodes_id_map:
                parent_nodes_id_map = {}
            parent_nodes_id_map["START"] = "0"
            self.parent_nodes_id_map = parent_nodes_id_map

        
    def __init__(self, k: int): 
        super().__init__()
        self.beams = [self.Beam() for _ in range(k)]

    def set_last_chosen(self, node: str, beam: int):
        self._set_last_chosen(self.beams[beam].parent_nodes_id_map[node])

    def create_nodes_highlight_k(self, nodes: Iterable[str], fillcolor: str, parent: str, beam: int, k_chosen: Iterable[str]):
        for node in nodes:
            edge_color = "black"
            self._inc_idx()
            self.graph.node(self._idx, node, fillcolor=fillcolor, style="filled")

            if node in k_chosen:
                edge_color = "red"
                self.beams[beam].parent_nodes_id_map[node] = self._idx
            self.graph.edge(self.beams[beam].parent_nodes_id_map[parent], self._idx, color=edge_color)
            