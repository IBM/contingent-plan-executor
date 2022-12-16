import json
import os
import sys

# configs will be stored in those globals
HOVOR_CONFIG = None
PRP_OUTPUT = None


def validate():
    global HOVOR_CONFIG, PRP_OUTPUT
    # =======================VALIDATION STARTS HERE==================

    if len(sys.argv) != 3:
        raise ValueError(f"Expected 2 arguments [hovor_config_path] [prp_output_path] but {len(sys.argv)} were given.")

    hovor_config_path = sys.argv[1]
    prp_output_path = sys.argv[2]

    HOVOR_CONFIG = load_json(hovor_config_path)
    PRP_OUTPUT = load_json(prp_output_path)["plan"]

    nodes = _get_all_nodes()
    validate_nodes(nodes)
    validate_outcomes(nodes)

    print("VALIDATION COMPLETED\n\t no errors found")


def validate_nodes(nodes):
    if nodes:
        # todo do we have some validation here?
        print("NODES VALIDATED")
    else:
        raise ValueError("Nodes are not available")


def validate_outcomes(nodes):
    for node in nodes:
        for child in node.children:

            outcome_name = _get_outcome_name(node, child)
            outcome_config = _get_outcome_config(node, outcome_name)
            if outcome_config is None:
                raise ValueError(f"Outcome configuration for outcome '{outcome_name}' was not found.")


def load_json(path):
    abs_path = os.path.abspath(path)
    if not os.path.exists(abs_path):
        raise ValueError(f"Path {abs_path} does not exist")

    if not os.path.isfile(abs_path):
        raise ValueError(f"Path {abs_path} was not recognized as a file")

    # json validation is done inside the loader
    with open(path) as f:
        return json.load(f)


def _get_outcome_config(node, outcome_name):
    action_config = _get_action_config(node)
    action_outcomes = action_config["effect"].get("outcomes", [])
    for action_outcome in action_outcomes:
        if action_outcome["name"] == outcome_name:
            return action_outcome

    return None


def _get_outcome_name(src_node, dst_node):
    for successor in PRP_OUTPUT["nodes"][src_node.node_id]["successors"]:
        successor_id = successor["successor_id"]

        if not isinstance(successor_id, str):
            raise ValueError("Successor ID has to be string.")

        if successor_id == dst_node.node_id:
            return successor["outcome_label"]

    raise ValueError(f"Successor {dst_node.node_id} was not found for node {src_node.node_id}")


def _get_action_config(node):
    return HOVOR_CONFIG["actions"][node.action_name]


def _get_all_nodes():
    """Loads nodes from the generated plan"""
    plan_data = PRP_OUTPUT
    node_id_to_node = {}
    for node_id, node_definition in plan_data["nodes"].items():
        # read definition
        state_id = node_definition["state"]
        state_fluents = plan_data["states"][state_id]

        node = Node(node_id)

        # set action name performed at the node
        node.action_name = plan_data["nodes"][node.node_id]["action"]

        node_id_to_node[node_id] = node

    # after all nodes are load we can define parentship between them
    for node in node_id_to_node.values():
        node.children = _get_children(node, node_id_to_node)
        for child in node.children:
            child.parent = node

    return node_id_to_node.values()


def _get_children(node, node_id_to_node):
    children = []
    outcome_node_ids = PRP_OUTPUT["nodes"][node.node_id]["successors"]
    for outcome_node_id in outcome_node_ids:
        successor_id = outcome_node_id["successor_id"]
        outcome_node = node_id_to_node[successor_id]
        children.append(outcome_node)

    return children


class Node(object):
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.children = []


validate()
