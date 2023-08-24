from graphviz import Digraph
from typing import Iterable, Dict
from enum import Enum


class NodeType(Enum):
    DEFAULT_ACTION = 1
    MESSAGE_ACTION = 2
    SYSTEM_API = 3
    INTENT = 4
    GOAL = 5
    DROP_OFF = 6


class BeamSearchGraph:
    def __init__(self, k: int):
        self.graph = Digraph(strict=True)
        self.graph.node(
            "0",
            "START",
            fillcolor="darkolivegreen3",
            style="filled",
            fontsize="50",
        )
        self._idx = "0"
        self.beams = [BeamSearchGraph.SingleBeam() for _ in range(k)]

    @staticmethod
    def _set_color(type: NodeType):
        return {
            NodeType.DEFAULT_ACTION: "steelblue1",
            NodeType.MESSAGE_ACTION: "powderblue",
            NodeType.SYSTEM_API: "plum2",
            NodeType.INTENT: "lightgoldenrod1",
            NodeType.GOAL: "darkolivegreen3",
            NodeType.DROP_OFF: "indianred2",
        }[type]

    def _inc_idx(self, inc: int = 1):
        self._idx = str(int(self._idx) + inc)

    def create_nodes_outside_beams(self, nodes: Dict, parent: str):
        """
        nodes should be in the form:
        {
            [node name]: (score, NodeType)
        }
        """
        for node, cfg in nodes.items():
            edge_color, penwidth = "grey45", "5.0"
            self._inc_idx()
            self.graph.node(
                self._idx,
                f"{node}\n{cfg[0]}",
                fillcolor=BeamSearchGraph._set_color(cfg[1]),
                style="filled",
                fontsize="50",
            )

            self.graph.edge(parent, self._idx, color=edge_color, penwidth=penwidth)

    def create_nodes_from_beams(
        self,
        nodes: Dict,
        beam: int,
        parent: str,
        k_highlighted: Iterable[str] = None,
    ):
        """
        nodes should be in the form:
        {
            [node name]: (score, NodeType)
        }
        """
        # have to access the parent ID before potentially making changes to the map to prevent
        # overwriting in the case where you have a node "A" connected to a parent "A"
        # (otherwise you would attach the node to itself)
        parent = self.beams[beam].get_parent_node(parent)
        for node, cfg in nodes.items():
            edge_color, arrowhead, penwidth = "grey45", "none", "5.0"
            self._inc_idx()
            self.graph.node(
                self._idx,
                f"{node}\n{cfg[0]}",
                fillcolor=BeamSearchGraph._set_color(cfg[1]),
                style="filled",
                fontsize="50",
            )
            if k_highlighted:
                if node in k_highlighted:
                    edge_color, arrowhead, penwidth = "purple", "normal", "10.0"
                    # create the list if it doesn't exist yet, otherwise add to it
                    if node not in self.beams[beam].parent_nodes_id_map:
                        self.beams[beam].parent_nodes_id_map[node] = []
                    self.beams[beam].parent_nodes_id_map[node].append(self._idx)

            self.graph.edge(
                parent,
                self._idx,
                color=edge_color,
                penwidth=penwidth,
                arrowhead=arrowhead,
            )

    class SingleBeam:
        def __init__(
            self,
        ):
            self.parent_nodes_id_map = {"START": ["0"]}

        def get_parent_node(self, node: str):
            return str(self.parent_nodes_id_map[node][-1])

        def copy(self):
            beam = BeamSearchGraph.SingleBeam()
            beam.parent_nodes_id_map = {
                node_name: [node for node in self.parent_nodes_id_map[node_name]]
                for node_name in self.parent_nodes_id_map
            }
            return beam
